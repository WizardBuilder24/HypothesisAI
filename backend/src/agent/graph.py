"""
HypothesisAI - LangGraph Research Workflow
Minimal implementation with 5 essential nodes
"""

import os
from typing import Literal, List, Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
import time
from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain_core.runnables import RunnableConfig

from agent.state import ResearchState
from agent.configuration import ResearchWorkflowConfiguration
from agent.prompts import (
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
    analyze_state,
    format_synthesis_for_prompt,
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
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Get LLM based on configuration
    llm = _get_llm(configurable, temperature=configurable.temperature_settings.supervisor)
    
    # Analyze current state to make routing decision
    current_status = analyze_state(state)
    
    # Format routing prompt
    formatted_prompt = supervisor_routing_prompt.format(
        query=state.get("query", ""),
        papers_count=len(state.get("papers", [])),
        has_synthesis=state.get("synthesis") is not None,
        has_hypotheses=len(state.get("hypotheses", [])) > 0,
        has_validation=state.get("validation_results") is not None,
        error_count=len(state.get("errors", [])),
        iteration=state.get("iteration", 0),
        status_summary=current_status,
        current_data=state,
    )
    
    # Get structured decision from LLM
    structured_llm = llm.with_structured_output(SupervisorDecision)
    decision = structured_llm.invoke(formatted_prompt)
    
    # Rate limiting: small delay to respect Gemini quota (30 req/min = 2 sec between calls)
    time.sleep(2.5)

    # Record stage information for debugging/visibility
    try:
        if "stages" not in state:
            state["stages"] = []
        state["stages"].append({
            "agent": "supervisor",
            "prompt": formatted_prompt,
            "response": decision.model_dump() if hasattr(decision, 'model_dump') else str(decision),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        # Non-critical: don't fail workflow if recording stages fails
        pass
    
    # Update state with supervisor decision
    return {
        "next_agent": decision.next_agent,
        "should_continue": decision.should_continue,
        "supervisor_reasoning": decision.reasoning,
        "iteration": state.get("iteration", 0) + 1,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "stages": state.get("stages", []),
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
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Get LLM
    llm = _get_llm(configurable, temperature=configurable.temperature_settings.literature_search)
    
    # Format search prompt
    query = state.get("query", "")
    max_papers = state.get("max_papers", 20)
    
    formatted_prompt = literature_search_prompt.format(
        query=query,
        max_papers=max_papers,
        current_data=state,
    )
    
    # Get structured paper list from LLM (mock search for now)
    structured_llm = llm.with_structured_output(PaperList)
    paper_results = structured_llm.invoke(formatted_prompt)
    
    # Rate limiting delay
    time.sleep(2.5)

    # Record stage information
    try:
        if "stages" not in state:
            state["stages"] = []
        state["stages"].append({
            "agent": "literature_hunter",
            "prompt": formatted_prompt,
            "response": paper_results.model_dump() if hasattr(paper_results, 'model_dump') else str(paper_results),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass
    
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
        "stages": state.get("stages", []),
    }


# ============================================================================
# KNOWLEDGE SYNTHESIZER NODE
# ============================================================================

def synthesizer(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Knowledge Synthesizer node that analyzes papers to identify patterns and gaps.
    """
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Get LLM
    llm = _get_llm(configurable, temperature=configurable.temperature_settings.synthesis)
    
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
        papers_summary=papers_summary,
        current_data=state,
    )
    
    # Get structured synthesis from LLM
    structured_llm = llm.with_structured_output(SynthesisResult)
    synthesis = structured_llm.invoke(formatted_prompt)
    
    # Rate limiting delay
    time.sleep(2.5)

    # Record stage
    try:
        if "stages" not in state:
            state["stages"] = []
        state["stages"].append({
            "agent": "synthesizer",
            "prompt": formatted_prompt,
            "response": synthesis.model_dump() if hasattr(synthesis, 'model_dump') else str(synthesis),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass
    
    # Store synthesis in state
    return {
        "synthesis": synthesis.model_dump(),
        "synthesis_completed": True,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"Identified {len(synthesis.patterns)} patterns and {len(synthesis.research_gaps)} research gaps")
        ],
        "stages": state.get("stages", []),
    }


# ============================================================================
# HYPOTHESIS GENERATOR NODE
# ============================================================================

def hypothesis_generator(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Hypothesis Generator node that creates novel research hypotheses.
    """
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Get LLM with higher temperature for creativity
    llm = _get_llm(configurable, temperature=configurable.temperature_settings.hypothesis_generation)
    
    # Get synthesis
    synthesis = state.get("synthesis")
    if not synthesis:
        return {
            "hypotheses": [],
            "errors": state.get("errors", []) + ["No synthesis available for hypothesis generation"],
        }
    
    # Format hypothesis generation prompt
    synthesis_text = format_synthesis_for_prompt(synthesis)
    formatted_prompt = hypothesis_generation_prompt.format(
        synthesis=synthesis_text,
        num_hypotheses=configurable.num_hypotheses,
        current_data=state,
    )
    
    # Get structured hypotheses from LLM
    structured_llm = llm.with_structured_output(HypothesisList)
    hypotheses_result = structured_llm.invoke(formatted_prompt)
    
    # Rate limiting delay
    time.sleep(2.5)

    # Record stage
    try:
        if "stages" not in state:
            state["stages"] = []
        state["stages"].append({
            "agent": "hypothesis_generator",
            "prompt": formatted_prompt,
            "response": hypotheses_result.model_dump() if hasattr(hypotheses_result, 'model_dump') else str(hypotheses_result),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass
    
    # Process hypotheses
    hypotheses = []
    for hypothesis in hypotheses_result.hypotheses:
        # Add paper IDs from synthesis that are relevant to this specific hypothesis
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
        "stages": state.get("stages", []),
    }


# ============================================================================
# VALIDATION AGENT NODE
# ============================================================================

def validator(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Validation Agent node that validates hypotheses and completes the workflow.
    """
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Get LLM
    llm = _get_llm(configurable, temperature=configurable.temperature_settings.validation)
    
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
            supporting_papers=len(hypothesis.get("supporting_papers", [])),
            current_data=state,
        )
        
        # Get structured validation
        structured_llm = llm.with_structured_output(ValidationResult)
        validation = structured_llm.invoke(formatted_prompt)
        
        # Rate limiting delay between hypothesis validations
        time.sleep(2.5)

        # Record stage per hypothesis validation
        try:
            if "stages" not in state:
                state["stages"] = []
            state["stages"].append({
                "agent": "validator",
                "prompt": formatted_prompt,
                "response": validation.model_dump() if hasattr(validation, 'model_dump') else str(validation),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hypothesis_id": hypothesis.get("id"),
            })
        except Exception:
            pass
        
        # Add hypothesis ID to validation
        validation_dict = validation.model_dump()
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
        "stages": state.get("stages", []),
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_llm(configurable: ResearchWorkflowConfiguration, temperature: float = 0.7):
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
            model="gemini-2.0-flash-lite",
            temperature=temperature,
            api_key=os.getenv("GEMINI_API_KEY"),
        )


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

# Create the graph
graph_builder = StateGraph(ResearchState, config_schema=ResearchWorkflowConfiguration)

# Add nodes
graph_builder.add_node("supervisor", supervisor)
graph_builder.add_node("literature_hunter", literature_hunter)
graph_builder.add_node("synthesizer", synthesizer)
graph_builder.add_node("hypothesis_generator", hypothesis_generator)
graph_builder.add_node("validator", validator)

# Set entry point
graph_builder.add_edge(START, "supervisor")

# Add conditional routing from supervisor
graph_builder.add_conditional_edges(
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
graph_builder.add_edge("literature_hunter", "supervisor")
graph_builder.add_edge("synthesizer", "supervisor")
graph_builder.add_edge("hypothesis_generator", "supervisor")
graph_builder.add_edge("validator", "supervisor")

# Compile the graph
graph = graph_builder.compile(name="hypothesis-ai-research")