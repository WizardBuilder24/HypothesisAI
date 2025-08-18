"""Base agent class for all research agents"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

from app.state import ResearchState


class BaseAgent(ABC):
    """Base class for all agents in the research workflow"""
    
    def __init__(self, name: str, description: str = "", llm_client=None):
        """
        Initialize base agent
        
        Args:
            name: Agent name
            description: Agent description
            llm_client: LLM client instance
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")
        self.llm_client = llm_client
        
    @abstractmethod
    async def process(self, state: ResearchState) -> ResearchState:
        """
        Process the state and return updated state
        
        Args:
            state: Current research state
            
        Returns:
            Updated research state
        """
        pass
    
    def log_start(self, state: ResearchState) -> None:
        """Log agent start"""
        self.logger.info(
            f"Starting {self.name} agent",
            extra={
                "workflow_id": state["workflow_id"],
                "query": state["query"][:100]  # Truncate long queries
            }
        )
    
    def log_complete(self, state: ResearchState) -> None:
        """Log agent completion"""
        self.logger.info(
            f"Completed {self.name} agent",
            extra={"workflow_id": state["workflow_id"]}
        )
    
    def log_error(self, error: str, state: ResearchState) -> None:
        """Log agent error"""
        self.logger.error(
            f"Error in {self.name} agent: {error}",
            extra={"workflow_id": state["workflow_id"]}
        )
    
    def validate_input(self, state: ResearchState) -> bool:
        """
        Validate that the agent has required input
        
        Args:
            state: Current state
            
        Returns:
            True if input is valid
        """
        return True  # Override in subclasses
    
    def format_output(self, output: Any) -> Dict[str, Any]:
        """
        Format agent output for state storage
        
        Args:
            output: Raw agent output
            
        Returns:
            Formatted output as dictionary
        """
        # Override in subclasses for custom formatting
        if hasattr(output, 'dict'):
            return output.dict()
        return output