"""Enumeration types for the research workflow"""

from enum import Enum


class AgentType(str, Enum):
    """Types of agents in the system"""
    SUPERVISOR = "supervisor"
    LITERATURE_HUNTER = "literature_hunter"
    KNOWLEDGE_SYNTHESIZER = "knowledge_synthesizer"
    HYPOTHESIS_GENERATOR = "hypothesis_generator"
    METHODOLOGY_DESIGNER = "methodology_designer"
    VALIDATION = "validation"


class WorkflowStatus(str, Enum):
    """Overall workflow execution status"""
    INITIALIZED = "initialized"
    SEARCHING = "searching"
    SYNTHESIZING = "synthesizing"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"