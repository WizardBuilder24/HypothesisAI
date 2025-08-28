"""HypothesisAI - LangGraph Research Workflow

Multi-agent research system with supervisor orchestration.
"""

import os
from typing import Literal, Dict, Any, List
from datetime import datetime, timezone
from dotenv import load_dotenv

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
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
    SynthesisResult,
    HypothesisList,
    ValidationResult,
    SupervisorDecision,
    SearchStrategies,
)
from agent.utils import (
    format_papers_for_synthesis,
    extract_paper_ids,
    analyze_state,
    format_synthesis_for_prompt,
)
from agent.workflow_utils import (
    WorkflowLogger,
    LLMProvider,
    PaperSearcher,
    PaperProcessor,
    RateLimiter,
    StateValidator,
    MessageBuilder,
)

load_dotenv()

# Supervisor Node

def supervisor(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Analyze current state and route to next agent."""
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Get LLM for decision making
    llm = LLMProvider.create_llm(
        configurable, 
        temperature=configurable.temperature_settings.supervisor
    )
    
    # Analyze current workflow state
    current_status = analyze_state(state)
    
    # Build routing decision prompt
    routing_prompt = _build_supervisor_prompt(state, current_status)
    
    # Get structured decision from LLM
    structured_llm = llm.with_structured_output(SupervisorDecision)
    decision = structured_llm.invoke(routing_prompt)
    
    # Apply rate limiting for API respect
    RateLimiter.apply_rate_limit()

    # Record decision for transparency
    WorkflowLogger.record_stage(
        state=state,
        agent_name="supervisor",
        prompt=routing_prompt,
        response=decision
    )
    
    # Return updated state with supervisor decision
    return _build_supervisor_state_update(state, decision)


def _build_supervisor_prompt(state: ResearchState, current_status: str) -> str:
    """Build the supervisor routing prompt with current state information."""
    return supervisor_routing_prompt.format(
        query=StateValidator.get_query(state),
        papers_count=len(StateValidator.get_papers(state)),
        has_synthesis=StateValidator.get_synthesis(state) is not None,
        has_hypotheses=len(StateValidator.get_hypotheses(state)) > 0,
        has_validation=len(StateValidator.get_validation_results(state)) > 0,
        error_count=len(StateValidator.get_errors(state)),
        iteration=StateValidator.get_iteration(state),
        status_summary=current_status,
        current_data=state,
    )


def _build_supervisor_state_update(
    state: ResearchState, 
    decision: SupervisorDecision
) -> Dict[str, Any]:
    """Build state update dictionary for supervisor decision."""
    return {
        "next_agent": decision.next_agent,
        "should_continue": decision.should_continue,
        "supervisor_reasoning": decision.reasoning,
        "iteration": StateValidator.get_iteration(state) + 1,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "stages": StateValidator.get_stages(state),
    }


def route_supervisor(state: ResearchState) -> Literal["literature_hunter", "synthesizer", "hypothesis_generator", "validator", "end"]:
    """Route supervisor decisions to appropriate workflow nodes."""
    next_agent = state.get("next_agent")
    should_continue = state.get("should_continue", True)
    
    # End workflow if determined by supervisor
    if not should_continue or next_agent == "end":
        return "end"
    
    # Route to valid agents or default to end
    valid_agents = {
        "literature_hunter", "synthesizer", 
        "hypothesis_generator", "validator"
    }
    
    return next_agent if next_agent in valid_agents else "end"

# Literature Hunter Node

def literature_hunter(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Search for relevant papers using multiple strategies."""
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Generate search strategies using LLM
    search_strategies, search_prompt = _generate_search_strategies(state, configurable)
    
    # Execute multiple search strategies
    search_results = _execute_search_strategies(search_strategies, state)
    
    # Process and consolidate results
    final_papers = _consolidate_search_results(search_results, state)
    
    # Record successful search completion with actual prompt
    WorkflowLogger.record_stage(
        state=state,
        agent_name="literature_hunter",
        prompt=search_prompt,
        response=search_strategies,
        additional_data={
            "strategies_used": len(search_strategies.search_strategies),
            "papers_found": len(final_papers)
        }
    )
    
    return _build_literature_search_state_update(state, final_papers, search_results)


def _generate_search_strategies(
    state: ResearchState, 
    configurable: ResearchWorkflowConfiguration
) -> tuple[SearchStrategies, str]:
    """Generate optimized search strategies using LLM and return both result and prompt."""
    llm = LLMProvider.create_llm(
        configurable, 
        temperature=configurable.temperature_settings.literature_search
    )
    
    query = StateValidator.get_query(state)
    max_papers = StateValidator.get_max_papers(state)
    max_papers_per_search = max(5, max_papers // 3)
    
    search_prompt = literature_search_prompt.format(
        query=query,
        max_papers=max_papers_per_search,
        current_data=state,
    )
    
    structured_llm = llm.with_structured_output(SearchStrategies)
    strategies = structured_llm.invoke(search_prompt)
    
    RateLimiter.apply_rate_limit()
    return strategies, search_prompt


def _execute_search_strategies(
    strategies: SearchStrategies, 
    state: ResearchState
) -> Dict[str, Any]:
    """Execute multiple search strategies and collect results."""
    max_papers = StateValidator.get_max_papers(state)
    max_papers_per_search = max(5, max_papers // 3)
    
    all_papers = []
    search_queries_used = []
    papers_per_strategy = {}
    
    # Sort strategies by priority (1 = highest priority first)
    sorted_strategies = sorted(strategies.search_strategies, key=lambda s: s.priority)
    
    for i, strategy in enumerate(sorted_strategies):
        try:
            print(f"Executing search strategy {i+1}/{len(sorted_strategies)}: {strategy.focus}")
            
            # Perform search for this strategy
            strategy_papers = PaperSearcher.search_papers_sync(
                strategy.query, 
                max_papers_per_search
            )
            
            papers_per_strategy[f"strategy_{i+1}"] = len(strategy_papers)
            all_papers.extend(strategy_papers)
            search_queries_used.append(strategy.query)
            
            # Respectful delay between searches
            if i < len(sorted_strategies) - 1:
                RateLimiter.apply_search_delay()
                
        except Exception as e:
            print(f"Error in search strategy {i+1}: {e}")
            papers_per_strategy[f"strategy_{i+1}"] = 0
            continue
    
    return {
        "all_papers": all_papers,
        "search_queries_used": search_queries_used,
        "papers_per_strategy": papers_per_strategy,
        "strategies_used": len(sorted_strategies)
    }


def _consolidate_search_results(
    search_results: Dict[str, Any], 
    state: ResearchState
) -> List[Dict[str, Any]]:
    """Consolidate, deduplicate, and rank search results."""
    all_papers = search_results["all_papers"]
    max_papers = StateValidator.get_max_papers(state)
    
    # Remove duplicates
    unique_papers = PaperProcessor.deduplicate_papers(all_papers)
    
    print(f"Found {len(all_papers)} total papers, {len(unique_papers)} unique papers")
    
    # Convert to dict format and rank
    paper_dicts = PaperProcessor.convert_papers_to_dict(unique_papers)
    ranked_papers = PaperProcessor.rank_papers(paper_dicts)
    
    # Return top papers up to limit
    return ranked_papers[:max_papers]


def _build_literature_search_state_update(
    state: ResearchState,
    final_papers: List[Dict[str, Any]],
    search_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Build state update for completed literature search."""
    strategy_summary = f"{search_results['strategies_used']} complementary search approaches"
    
    message = MessageBuilder.build_search_complete_message(
        paper_count=len(final_papers),
        strategy_count=search_results["strategies_used"],
        strategy_summary=strategy_summary
    )
    
    return {
        "papers": final_papers,
        "papers_found_count": len(final_papers),
        "search_completed": True,
        "search_queries": search_results["search_queries_used"],
        "search_strategies_used": search_results["strategies_used"],
        "papers_per_strategy": search_results["papers_per_strategy"],
        "total_papers_before_dedup": len(search_results["all_papers"]),
        "duplicate_papers_removed": len(search_results["all_papers"]) - len(final_papers),
        "messages": [message],
        "stages": StateValidator.get_stages(state),
    }


# Knowledge Synthesizer Node

def synthesizer(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Analyze papers to identify patterns and research gaps."""
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Validate we have papers to synthesize
    papers = StateValidator.get_papers(state)
    if not papers:
        return _build_synthesis_error_state(state, "No papers available for synthesis")
    
    # Generate synthesis using LLM
    synthesis_result, synthesis_prompt = _generate_synthesis(state, configurable, papers)
    
    # Record synthesis completion with actual prompt
    WorkflowLogger.record_stage(
        state=state,
        agent_name="synthesizer",
        prompt=synthesis_prompt,
        response=synthesis_result,
        additional_data={"papers_analyzed": len(papers)}
    )
    
    return _build_synthesis_state_update(state, synthesis_result)


def _generate_synthesis(
    state: ResearchState,
    configurable: ResearchWorkflowConfiguration,
    papers: List[Dict[str, Any]]
) -> tuple[SynthesisResult, str]:
    """Generate synthesis using LLM analysis of papers and return both result and prompt."""
    llm = LLMProvider.create_llm(
        configurable, 
        temperature=configurable.temperature_settings.synthesis
    )
    
    papers_summary = format_papers_for_synthesis(papers)
    synthesis_prompt_text = synthesis_prompt.format(
        num_papers=len(papers),
        papers_summary=papers_summary,
        current_data=state,
    )
    
    structured_llm = llm.with_structured_output(SynthesisResult)
    synthesis = structured_llm.invoke(synthesis_prompt_text)
    
    RateLimiter.apply_rate_limit()
    return synthesis, synthesis_prompt_text


def _build_synthesis_error_state(state: ResearchState, error_message: str) -> Dict[str, Any]:
    """Build error state for synthesis failures."""
    return {
        "synthesis": None,
        "errors": StateValidator.get_errors(state) + [error_message],
        "stages": StateValidator.get_stages(state),
    }


def _build_synthesis_state_update(
    state: ResearchState, 
    synthesis: SynthesisResult
) -> Dict[str, Any]:
    """Build state update for completed synthesis."""
    synthesis_dict = synthesis.model_dump()
    
    message = MessageBuilder.build_synthesis_complete_message(
        pattern_count=len(synthesis.patterns),
        gap_count=len(synthesis.research_gaps)
    )
    
    return {
        "synthesis": synthesis_dict,
        "synthesis_completed": True,
        "messages": StateValidator.get_messages(state) + [message],
        "stages": StateValidator.get_stages(state),
    }


# Hypothesis Generator Node

def hypothesis_generator(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Generate novel, testable hypotheses based on synthesis."""
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Validate we have synthesis to work with
    synthesis = StateValidator.get_synthesis(state)
    if not synthesis:
        return _build_hypothesis_error_state(state, "No synthesis available for hypothesis generation")
    
    # Generate hypotheses using LLM
    hypotheses_result, hypothesis_prompt = _generate_hypotheses(state, configurable, synthesis)
    
    # Process and rank hypotheses
    processed_hypotheses = _process_hypotheses(hypotheses_result, synthesis)
    
    # Record hypothesis generation completion with actual prompt
    WorkflowLogger.record_stage(
        state=state,
        agent_name="hypothesis_generator",
        prompt=hypothesis_prompt,
        response=hypotheses_result,
        additional_data={"hypotheses_generated": len(processed_hypotheses)}
    )
    
    return _build_hypothesis_state_update(state, processed_hypotheses)


def _generate_hypotheses(
    state: ResearchState,
    configurable: ResearchWorkflowConfiguration,
    synthesis: Dict[str, Any]
) -> tuple[HypothesisList, str]:
    """Generate hypotheses using LLM with higher creativity temperature and return both result and prompt."""
    llm = LLMProvider.create_llm(
        configurable, 
        temperature=configurable.temperature_settings.hypothesis_generation
    )
    
    synthesis_text = format_synthesis_for_prompt(synthesis)
    hypothesis_prompt_text = hypothesis_generation_prompt.format(
        synthesis=synthesis_text,
        num_hypotheses=configurable.num_hypotheses,
        current_data=state,
    )
    
    structured_llm = llm.with_structured_output(HypothesisList)
    hypotheses = structured_llm.invoke(hypothesis_prompt_text)
    
    RateLimiter.apply_rate_limit()
    return hypotheses, hypothesis_prompt_text


def _process_hypotheses(
    hypotheses_result: HypothesisList, 
    synthesis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Process hypotheses by adding supporting paper references and ranking."""
    processed_hypotheses = []
    
    for hypothesis in hypotheses_result.hypotheses:
        # Add paper IDs from synthesis that support this hypothesis
        hypothesis.supporting_papers = extract_paper_ids(synthesis, hypothesis.content)
        processed_hypotheses.append(hypothesis.dict())
    
    # Sort by confidence score (highest first)
    return sorted(
        processed_hypotheses, 
        key=lambda h: h.get("confidence_score", 0), 
        reverse=True
    )


def _build_hypothesis_error_state(state: ResearchState, error_message: str) -> Dict[str, Any]:
    """Build error state for hypothesis generation failures."""
    return {
        "hypotheses": [],
        "errors": StateValidator.get_errors(state) + [error_message],
        "stages": StateValidator.get_stages(state),
    }


def _build_hypothesis_state_update(
    state: ResearchState, 
    hypotheses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build state update for completed hypothesis generation."""
    message = MessageBuilder.build_hypothesis_complete_message(len(hypotheses))
    
    return {
        "hypotheses": hypotheses,
        "hypotheses_generated": len(hypotheses),
        "messages": StateValidator.get_messages(state) + [message],
        "stages": StateValidator.get_stages(state),
    }


# Validation Agent Node

def validator(state: ResearchState, config: RunnableConfig) -> Dict[str, Any]:
    """Validate hypotheses for logical consistency and feasibility."""
    configurable = ResearchWorkflowConfiguration.from_runnable_config(config)
    
    # Validate we have hypotheses to validate
    hypotheses = StateValidator.get_hypotheses(state)
    if not hypotheses:
        return _build_validation_error_state(state, "No hypotheses to validate")
    
    # Validate hypotheses up to configured limit
    validation_results, validation_prompts = _validate_hypotheses(
        state, configurable, hypotheses[:configurable.max_hypotheses_to_validate]
    )
    
    # Record validation completion with actual prompts used
    WorkflowLogger.record_stage(
        state=state,
        agent_name="validator",
        prompt=validation_prompts,  # List of all validation prompts used
        response=f"Validated {len(validation_results)} hypotheses",
        additional_data={
            "hypotheses_validated": len(validation_results),
            "valid_count": sum(1 for v in validation_results if v.get("is_valid"))
        }
    )
    
    return _build_validation_state_update(state, validation_results)


def _validate_hypotheses(
    state: ResearchState,
    configurable: ResearchWorkflowConfiguration,
    hypotheses_to_validate: List[Dict[str, Any]]
) -> tuple[List[Dict[str, Any]], List[str]]:
    """Validate each hypothesis using LLM assessment and return results with prompts."""
    llm = LLMProvider.create_llm(
        configurable, 
        temperature=configurable.temperature_settings.validation
    )
    
    validation_results = []
    validation_prompts = []
    
    for hypothesis in hypotheses_to_validate:
        # Generate validation prompt for this hypothesis
        validation_prompt_text = validation_prompt.format(
            hypothesis=hypothesis.get("content", ""),
            confidence_score=hypothesis.get("confidence_score", 0),
            reasoning=hypothesis.get("reasoning", ""),
            supporting_papers=len(hypothesis.get("supporting_papers", [])),
            current_data=state,
        )
        
        validation_prompts.append(validation_prompt_text)
        
        # Get structured validation assessment
        structured_llm = llm.with_structured_output(ValidationResult)
        validation = structured_llm.invoke(validation_prompt_text)
        
        # Apply rate limiting between validations
        RateLimiter.apply_rate_limit()

        # Build validation result with hypothesis reference
        validation_dict = validation.model_dump()
        validation_dict["hypothesis_id"] = hypothesis.get("id")
        validation_results.append(validation_dict)
    
    return validation_results, validation_prompts


def _build_validation_error_state(state: ResearchState, error_message: str) -> Dict[str, Any]:
    """Build error state for validation failures."""
    return {
        "validation_results": [],
        "errors": StateValidator.get_errors(state) + [error_message],
        "workflow_complete": True,
        "stages": StateValidator.get_stages(state),
    }


def _build_validation_state_update(
    state: ResearchState, 
    validation_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build state update for completed validation."""
    valid_count = sum(1 for v in validation_results if v.get("is_valid"))
    
    message = MessageBuilder.build_validation_complete_message(
        valid_count=valid_count,
        total_count=len(validation_results)
    )
    
    return {
        "validation_results": validation_results,
        "valid_hypotheses_count": valid_count,
        "workflow_complete": True,
        "messages": StateValidator.get_messages(state) + [message],
        "stages": StateValidator.get_stages(state),
    }


# Workflow Graph Construction

# Create the graph with proper configuration
graph_builder = StateGraph(ResearchState, config_schema=ResearchWorkflowConfiguration)

# Add all workflow nodes
graph_builder.add_node("supervisor", supervisor)
graph_builder.add_node("literature_hunter", literature_hunter)
graph_builder.add_node("synthesizer", synthesizer)
graph_builder.add_node("hypothesis_generator", hypothesis_generator)
graph_builder.add_node("validator", validator)

# Set entry point to supervisor
graph_builder.add_edge(START, "supervisor")

# Add conditional routing from supervisor based on decisions
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

# All agents return control to supervisor for next decision
graph_builder.add_edge("literature_hunter", "supervisor")
graph_builder.add_edge("synthesizer", "supervisor")
graph_builder.add_edge("hypothesis_generator", "supervisor")
graph_builder.add_edge("validator", "supervisor")

# Compile the graph for execution
graph = graph_builder.compile(name="hypothesis-ai-research")