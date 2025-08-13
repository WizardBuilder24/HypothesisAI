"""State management utilities for the research workflow"""

from datetime import datetime
from uuid import uuid4
from typing import Optional

from app.schemas import (
    ResearchState, 
    WorkflowStatus, 
    AgentType
)


def create_initial_state(query: str, max_papers: int = 50) -> ResearchState:
    """
    Create initial state for workflow
    
    Args:
        query: The research question
        max_papers: Maximum number of papers to analyze
    
    Returns:
        Initial ResearchState
    """
    now = datetime.utcnow().isoformat()
    
    return ResearchState(
        workflow_id=str(uuid4()),
        status=WorkflowStatus.INITIALIZED,
        current_agent=AgentType.SUPERVISOR,
        query=query,
        max_papers=max_papers,
        papers=[],
        synthesis=None,
        hypotheses=[],
        methodologies=[],
        validation_results=[],
        errors=[],
        should_continue=True,
        started_at=now,
        updated_at=now
    )


def update_state_status(
    state: ResearchState, 
    status: WorkflowStatus, 
    agent: AgentType
) -> ResearchState:
    """
    Helper to update state status and current agent
    
    Args:
        state: Current state
        status: New workflow status
        agent: Current agent
    
    Returns:
        Updated state
    """
    state["status"] = status
    state["current_agent"] = agent
    state["updated_at"] = datetime.utcnow().isoformat()
    return state


def add_error(state: ResearchState, error: str) -> ResearchState:
    """
    Helper to add error to state
    
    Args:
        state: Current state
        error: Error message
    
    Returns:
        Updated state with error
    """
    state["errors"].append(f"[{state['current_agent']}] {error}")
    state["updated_at"] = datetime.utcnow().isoformat()
    return state


def is_workflow_complete(state: ResearchState) -> bool:
    """Check if workflow is complete"""
    return (
        state["status"] == WorkflowStatus.COMPLETED or
        state["status"] == WorkflowStatus.FAILED or
        not state["should_continue"]
    )


def get_workflow_summary(state: ResearchState) -> dict:
    """Get summary of workflow execution"""
    return {
        "workflow_id": state["workflow_id"],
        "status": state["status"],
        "query": state["query"],
        "papers_found": len(state["papers"]),
        "hypotheses_generated": len(state["hypotheses"]),
        "errors": len(state["errors"]),
        "started_at": state["started_at"],
        "updated_at": state["updated_at"]
    }