"""Workflow configuration and constants"""

from typing import Dict, Any
from app.schemas import AgentType, WorkflowStatus


# Agent timeout settings (in seconds)
AGENT_TIMEOUTS = {
    AgentType.SUPERVISOR: 10,
    AgentType.LITERATURE_HUNTER: 60,
    AgentType.KNOWLEDGE_SYNTHESIZER: 45,
    AgentType.HYPOTHESIS_GENERATOR: 30,
    AgentType.METHODOLOGY_DESIGNER: 30,
    AgentType.VALIDATION: 20,
}

# Maximum retry attempts for each agent
AGENT_MAX_RETRIES = {
    AgentType.SUPERVISOR: 1,
    AgentType.LITERATURE_HUNTER: 3,
    AgentType.KNOWLEDGE_SYNTHESIZER: 2,
    AgentType.HYPOTHESIS_GENERATOR: 2,
    AgentType.METHODOLOGY_DESIGNER: 2,
    AgentType.VALIDATION: 1,
}

# Workflow status transitions
VALID_TRANSITIONS = {
    WorkflowStatus.INITIALIZED: [WorkflowStatus.SEARCHING, WorkflowStatus.FAILED],
    WorkflowStatus.SEARCHING: [WorkflowStatus.SYNTHESIZING, WorkflowStatus.FAILED],
    WorkflowStatus.SYNTHESIZING: [WorkflowStatus.GENERATING, WorkflowStatus.FAILED],
    WorkflowStatus.GENERATING: [WorkflowStatus.VALIDATING, WorkflowStatus.FAILED],
    WorkflowStatus.VALIDATING: [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED],
    WorkflowStatus.COMPLETED: [],
    WorkflowStatus.FAILED: []
}


def get_workflow_config() -> Dict[str, Any]:
    """Get default workflow configuration"""
    return {
        "max_execution_time": 300,  # 5 minutes total
        "enable_caching": True,
        "enable_retries": True,
        "log_level": "INFO",
        "save_intermediate_results": True
    }


def is_valid_transition(current: WorkflowStatus, next: WorkflowStatus) -> bool:
    """Check if a status transition is valid"""
    return next in VALID_TRANSITIONS.get(current, [])