"""
HypothesisAI - LangGraph Research Workflow
Minimal implementation with 5 essential nodes
"""

import os
from typing import Literal, List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain_core.runnables import RunnableConfig

from agent.state import ResearchState
from agent.configuration import Configuration
from agent.prompts import (
    get_system_prompt,
    literature_search_prompt,
    synthesis_prompt,
    hypothesis_generation_prompt,
    validation_prompt,
    supervisor_routing_prompt,
)
from agent.tools_and_schemas import (
    PaperList,
    SynthesisResult,
    HypothesisList,
    ValidationResult,
    SupervisorDecision,
)
from agent.utils import (
    deduplicate_papers,
    score_paper_relevance,
    format_papers_for_synthesis,
    extract_paper_ids,
)

load_dotenv()

# ============================================================================
# SUPERVISOR NODE - The Brain
# ============================================================================

def supervisor(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Supervisor node that makes all routing decisions.
    This is the brain of the system that determines what happens next.
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Get LLM based on configuration
    llm = _get_llm(configurable, temperature=0.3)
    
    # Analyze current state to make routing decision
    current_status = _analyze_state(state)
    
    # Format routing prompt
    formatted_prompt = supervisor_routing_prompt.format(
        query=state.get("query", ""),
        papers_count=len(state.get("papers", [])),
        has_synthesis=state.get("synthesis") is not None,
        has_hypotheses=len(state.get("hypotheses", [])) > 0,
        has_validation=state.get("validation_results") is not None,
        error_count=len(state.get("errors", [])),
        iteration=state.get("iteration", 0),
        status_summary=current_status
    )
    
    # Get structured decision from LLM
    structured_llm = llm.with_structured_output(SupervisorDecision)
    decision = structured_llm.invoke(formatted_prompt)
    
    # Update state with supervisor decision
    return {
        "next_agent": decision.next_agent,
        "should_continue": decision.should_continue,
        "supervisor_reasoning": decision.reasoning,
        "iteration": state.get("iteration", 0) + 1,
        "last_updated": datetime.utcnow().isoformat(),
    }


def route_supervisor(state: ResearchState) -> Literal["literature_hunter", "synthesizer", "hypothesis_generator", "validator", "end"]:
    """
    Routing function for supervisor decisions.
    Returns the next node to execute based on supervisor's decision.
    """
    next_agent = state.get("next_agent")
    should_continue = state.get("should_continue", True)
    
    # Check if we should end
    if not should_continue or next_agent == "end":
        return "end"
    
    # Route to the appropriate agent
    if next_agent == "literature_hunter":
        return "literature_hunter"
    elif next_agent == "synthesizer":
        return "synthesizer"
    elif next_agent == "hypothesis_generator":
        return "hypothesis_generator"
    elif next_agent == "validator":
        return "validator"
    else:
        # Default to end if unknown
        return "end"


# ============================================================================
# LITERATURE HUNTER NODE
# ============================================================================

def literature_hunter(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Literature Hunter node that searches for relevant academic papers.
    Uses LLM to generate search queries and mock search for now.
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Get LLM
    llm = _get_llm(configurable, temperature=0.7)
    
    # Format search prompt
    query = state.get("query", "")
    max_papers = state.get("max_papers", 20)
    
    formatted_prompt = literature_search_prompt.format(
        query=query,
        max_papers=max_papers
    )
    
    # Get structured paper list from LLM (mock search for now)
    structured_llm = llm.with_structured_output(PaperList)
    paper_results = structured_llm.invoke(formatted_prompt)
    
    # Process papers
    papers = []
    for paper in paper_results.papers:
        # Score relevance
        paper.relevance_score = score_paper_relevance(paper.title, paper.abstract, query)
        papers.append(paper.dict())
    
    # Deduplicate and sort by relevance
    unique_papers = deduplicate_papers(papers)
    sorted_papers = sorted(unique_papers, key=lambda p: p.get("relevance_score", 0), reverse=True)
    
    # Take top papers up to max_papers limit
    final_papers = sorted_papers[:max_papers]
    
    return {
        "papers": final_papers,
        "papers_found_count": len(final_papers),
        "search_completed": True,
        "messages": [AIMessage(content=f"Found {len(final_papers)} relevant papers for: {query}")],
    }


# ============================================================================
# KNOWLEDGE SYNTHESIZER NODE
# ============================================================================

def synthesizer(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Knowledge Synthesizer node that analyzes papers to identify patterns and gaps.
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Get LLM
    llm = _get_llm(configurable, temperature=0.5)
    
    # Prepare papers for synthesis
    papers = state.get("papers", [])
    if not papers:
        return {
            "synthesis": None,
            "errors": state.get("errors", []) + ["No papers available for synthesis"],
        }
    
    # Format synthesis prompt
    papers_summary = format_papers_for_synthesis(papers)
    formatted_prompt = synthesis_prompt.format(
        num_papers=len(papers),
        papers_summary=papers_summary
    )
    
    # Get structured synthesis from LLM
    structured_llm = llm.with_structured_output(SynthesisResult)
    synthesis = structured_llm.invoke(formatted_prompt)
    
    # Store synthesis in state
    return {
        "synthesis": synthesis.dict(),
        "synthesis_completed": True,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"Identified {len(synthesis.patterns)} patterns and {len(synthesis.research_gaps)} research gaps")
        ],
    }


# ============================================================================
# HYPOTHESIS GENERATOR NODE
# ============================================================================

def hypothesis_generator(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Hypothesis Generator node that creates novel research hypotheses.
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Get LLM with higher temperature for creativity
    llm = _get_llm(configurable, temperature=0.8)
    
    # Get synthesis
    synthesis = state.get("synthesis")
    if not synthesis:
        return {
            "hypotheses": [],
            "errors": state.get("errors", []) + ["No synthesis available for hypothesis generation"],
        }
    
    # Format hypothesis generation prompt
    synthesis_text = _format_synthesis_for_prompt(synthesis)
    formatted_prompt = hypothesis_generation_prompt.format(
        synthesis=synthesis_text,
        num_hypotheses=configurable.num_hypotheses
    )
    
    # Get structured hypotheses from LLM
    structured_llm = llm.with_structured_output(HypothesisList)
    hypotheses_result = structured_llm.invoke(formatted_prompt)
    
    # Process hypotheses
    hypotheses = []
    for hypothesis in hypotheses_result.hypotheses:
        # Add paper IDs from synthesis
        hypothesis.supporting_papers = extract_paper_ids(synthesis, hypothesis.content)
        hypotheses.append(hypothesis.dict())
    
    # Sort by confidence score
    sorted_hypotheses = sorted(hypotheses, key=lambda h: h.get("confidence_score", 0), reverse=True)
    
    return {
        "hypotheses": sorted_hypotheses,
        "hypotheses_generated": len(sorted_hypotheses),
        "messages": state.get("messages", []) + [
            AIMessage(content=f"Generated {len(sorted_hypotheses)} research hypotheses")
        ],
    }


# ============================================================================
# VALIDATION AGENT NODE
# ============================================================================

def validator(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Validation Agent node that validates hypotheses and completes the workflow.
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Get LLM
    llm = _get_llm(configurable, temperature=0.3)
    
    # Get hypotheses to validate
    hypotheses = state.get("hypotheses", [])
    if not hypotheses:
        return {
            "validation_results": [],
            "errors": state.get("errors", []) + ["No hypotheses to validate"],
            "workflow_complete": True,
        }
    
    validation_results = []
    
    # Validate each hypothesis (in practice, you might batch this)
    for hypothesis in hypotheses[:configurable.max_hypotheses_to_validate]:
        # Format validation prompt
        formatted_prompt = validation_prompt.format(
            hypothesis=hypothesis.get("content", ""),
            confidence_score=hypothesis.get("confidence_score", 0),
            reasoning=hypothesis.get("reasoning", ""),
            supporting_papers=len(hypothesis.get("supporting_papers", []))
        )
        
        # Get structured validation
        structured_llm = llm.with_structured_output(ValidationResult)
        validation = structured_llm.invoke(formatted_prompt)
        
        # Add hypothesis ID to validation
        validation_dict = validation.dict()
        validation_dict["hypothesis_id"] = hypothesis.get("id")
        validation_results.append(validation_dict)
    
    # Count valid hypotheses
    valid_count = sum(1 for v in validation_results if v.get("is_valid"))
    
    return {
        "validation_results": validation_results,
        "valid_hypotheses_count": valid_count,
        "workflow_complete": True,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"Validation complete: {valid_count}/{len(validation_results)} hypotheses validated")
        ],
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_llm(configurable: Configuration, temperature: float = 0.7):
    """
    Get the appropriate LLM based on configuration.
    """
    provider = configurable.llm_provider.lower()
    
    if provider == "openai":
        return ChatOpenAI(
            model=configurable.llm_model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=configurable.llm_model,
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=configurable.llm_model,
            temperature=temperature,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    else:
        # Default to Google
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=temperature,
            api_key=os.getenv("GEMINI_API_KEY"),
        )


def _analyze_state(state: ResearchState) -> str:
    """
    Analyze the current state and return a summary for the supervisor.
    """
    status_parts = []
    
    # Check papers
    papers = state.get("papers", [])
    if papers:
        status_parts.append(f"Papers: {len(papers)} found")
    else:
        status_parts.append("Papers: None")
    
    # Check synthesis
    if state.get("synthesis"):
        synthesis = state["synthesis"]
        status_parts.append(f"Synthesis: Complete ({len(synthesis.get('patterns', []))} patterns)")
    else:
        status_parts.append("Synthesis: Not done")
    
    # Check hypotheses
    hypotheses = state.get("hypotheses", [])
    if hypotheses:
        status_parts.append(f"Hypotheses: {len(hypotheses)} generated")
    else:
        status_parts.append("Hypotheses: None")
    
    # Check validation
    if state.get("validation_results"):
        valid_count = state.get("valid_hypotheses_count", 0)
        status_parts.append(f"Validation: Complete ({valid_count} valid)")
    else:
        status_parts.append("Validation: Not done")
    
    # Check errors
    errors = state.get("errors", [])
    if errors:
        status_parts.append(f"Errors: {len(errors)}")
    
    return " | ".join(status_parts)


def _format_synthesis_for_prompt(synthesis: Dict) -> str:
    """
    Format synthesis dictionary for prompt.
    """
    parts = []
    
    # Add patterns
    patterns = synthesis.get("patterns", [])
    if patterns:
        parts.append("PATTERNS IDENTIFIED:")
        for i, pattern in enumerate(patterns, 1):
            parts.append(f"{i}. {pattern.get('description', '')}")
    
    # Add key findings
    findings = synthesis.get("key_findings", [])
    if findings:
        parts.append("\nKEY FINDINGS:")
        for finding in findings:
            parts.append(f"- {finding}")
    
    # Add research gaps
    gaps = synthesis.get("research_gaps", [])
    if gaps:
        parts.append("\nRESEARCH GAPS:")
        for gap in gaps:
            parts.append(f"- {gap}")
    
    return "\n".join(parts)


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

# Create the StateGraph
builder = StateGraph(ResearchState, config_schema=Configuration)

# Add all nodes
builder.add_node("supervisor", supervisor)
builder.add_node("literature_hunter", literature_hunter)
builder.add_node("synthesizer", synthesizer)
builder.add_node("hypothesis_generator", hypothesis_generator)
builder.add_node("validator", validator)

# Set entry point
builder.add_edge(START, "supervisor")

# Add conditional routing from supervisor
builder.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {
        "literature_hunter": "literature_hunter",
        "synthesizer": "synthesizer",
        "hypothesis_generator": "hypothesis_generator",
        "validator": "validator",
        "end": END,
    }
)

# All agents return to supervisor
builder.add_edge("literature_hunter", "supervisor")
builder.add_edge("synthesizer", "supervisor")
builder.add_edge("hypothesis_generator", "supervisor")
builder.add_edge("validator", "supervisor")

# Compile the graph
graph = builder.compile(name="hypothesis-ai-research")