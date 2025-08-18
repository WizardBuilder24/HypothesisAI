"""Research workflow state schema"""

from typing import TypedDict, List, Dict, Optional, Any
from pydantic import BaseModel, Field

# Note: We import enums separately to avoid circular imports
from .enums import AgentType, WorkflowStatus


class ResearchState(TypedDict):
    """
    Core state for the research workflow.
    This is the main state that gets passed between all agents.
    """
    # Workflow control
    workflow_id: str
    status: WorkflowStatus
    current_agent: AgentType
    
    # User input
    query: str  # The research question
    max_papers: int  # Maximum papers to analyze
    
    # Agent outputs (these get populated as agents run)
    papers: List[Dict[str, Any]]  # List of Paper dicts
    synthesis: Optional[Dict[str, Any]]  # Synthesis dict
    hypotheses: List[Dict[str, Any]]  # List of Hypothesis dicts
    methodologies: List[Dict[str, Any]]  # List of Methodology dicts
    validation_results: List[Dict[str, Any]]  # List of ValidationResult dicts
    
    # Execution tracking
    errors: List[str]  # Any errors that occur
    should_continue: bool  # Whether to continue workflow
    
    # Timestamps
    started_at: str  # ISO format
    updated_at: str  # ISO format


class SupervisorDecision(BaseModel):
    """Decision made by supervisor agent"""
    next_agent: Optional[AgentType] = None
    should_continue: bool = True
    reason: str = ""