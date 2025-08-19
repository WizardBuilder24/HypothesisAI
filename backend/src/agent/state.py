"""
State definitions for HypothesisAI research workflow
Adapted from Google's example for hypothesis generation system
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
from langgraph.graph import add_messages
import operator


class ResearchState(TypedDict):
    """Main state for the research workflow - flows through all agents"""
    # Core message tracking
    messages: Annotated[list, add_messages]
    
    # Research query and workflow control
    query: str
    workflow_id: Optional[str]
    iteration: int
    should_continue: bool
    
    # Paper search tracking
    papers: List[Dict[str, Any]]
    search_queries: Annotated[list, operator.add]  # All search queries used
    papers_found_count: int
    
    # Synthesis results
    synthesis: Optional[Dict[str, Any]]
    patterns_found: List[Dict[str, Any]]
    research_gaps: List[str]
    
    # Hypothesis generation
    hypotheses: List[Dict[str, Any]]
    hypotheses_count: int
    
    # Validation results
    validation_results: List[Dict[str, Any]]
    valid_hypotheses_count: int
    
    # Supervisor routing
    next_agent: Optional[str]
    supervisor_reasoning: Optional[str]
    
    # Configuration parameters
    max_papers: int
    max_iterations: int
    min_papers_threshold: int
    num_hypotheses: int
    
    # Error and retry tracking
    errors: Annotated[list, operator.add]
    retry_counts: Dict[str, int]
    
    # Timestamps
    started_at: Optional[str]
    last_updated: Optional[str]
    completed_at: Optional[str]


class SupervisorState(TypedDict):
    """State for supervisor routing decisions"""
    next_agent: str
    should_continue: bool
    reasoning: str
    iteration: int


class LiteratureSearchState(TypedDict):
    """State for literature search operations"""
    search_query: str
    search_id: int
    max_results: int


class SynthesisState(TypedDict):
    """State for synthesis operations"""
    papers_to_analyze: List[Dict[str, Any]]
    num_papers: int
    synthesis_complete: bool


class HypothesisGenerationState(TypedDict):
    """State for hypothesis generation"""
    synthesis_input: Dict[str, Any]
    num_hypotheses_to_generate: int
    creativity_level: float


class ValidationState(TypedDict):
    """State for validation operations"""
    hypotheses_to_validate: List[Dict[str, Any]]
    validation_complete: bool
    validation_criteria: List[str]