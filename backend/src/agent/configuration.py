"""Configuration management for HypothesisAI research workflow.

Centralized configuration with environment variable support and type safety.
"""

import os
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from langchain_core.runnables import RunnableConfig


class LLMTemperatureSettings(BaseModel):
    """Temperature settings for different LLM operations."""
    
    supervisor: float = Field(default=0.3, ge=0.0, le=2.0)
    literature_search: float = Field(default=0.7, ge=0.0, le=2.0)
    synthesis: float = Field(default=0.5, ge=0.0, le=2.0)
    hypothesis_generation: float = Field(default=0.8, ge=0.0, le=2.0)
    validation: float = Field(default=0.3, ge=0.0, le=2.0)


class WorkflowLimits(BaseModel):
    """Workflow execution limits and thresholds."""
    
    max_papers: int = Field(default=5, ge=1, le=100)
    min_papers_for_synthesis: int = Field(default=3, ge=1)
    target_hypotheses_count: int = Field(default=2, ge=1, le=10)
    max_workflow_iterations: int = Field(default=5, ge=1, le=50)
    max_agent_retries: int = Field(default=2, ge=0, le=10)
    max_hypotheses_to_validate: int = Field(default=2, ge=1, le=20)


class QualityThresholds(BaseModel):
    """Quality control thresholds for filtering and validation."""
    
    min_hypothesis_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    min_synthesis_patterns: int = Field(default=2, ge=1)
    min_paper_relevance_score: float = Field(default=0.3, ge=0.0, le=1.0)


class ResearchWorkflowConfiguration(BaseModel):
    """Comprehensive configuration for the HypothesisAI research workflow."""
    
    # Model configurations
    default_llm_model: str = Field(default="gemini-2.0-flash-lite")
    llm_provider: str = Field(default="google")
    
    # Component configurations
    temperature_settings: LLMTemperatureSettings = Field(default_factory=LLMTemperatureSettings)
    workflow_limits: WorkflowLimits = Field(default_factory=WorkflowLimits)
    quality_thresholds: QualityThresholds = Field(default_factory=QualityThresholds)
    
    # Legacy property accessors
    @property
    def llm_model(self) -> str:
        """Legacy accessor for default LLM model."""
        return self.default_llm_model
    
    @property
    def max_papers(self) -> int:
        """Legacy accessor for max papers."""
        return self.workflow_limits.max_papers
    
    @property
    def num_hypotheses(self) -> int:
        """Legacy accessor for number of hypotheses."""
        return self.workflow_limits.target_hypotheses_count
    
    @property
    def max_hypotheses_to_validate(self) -> int:
        """Legacy accessor for max hypotheses to validate."""
        return self.workflow_limits.max_hypotheses_to_validate
    
    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "ResearchWorkflowConfiguration":
        """Create configuration from RunnableConfig with environment fallback."""
        configurable_values = cls._extract_configurable_values(config)
        environment_values = cls._extract_environment_values()
        
        # Merge values with priority: config > environment > defaults
        merged_values = {**environment_values, **configurable_values}
        
        return cls(**merged_values)
    
    @staticmethod
    def _extract_configurable_values(config: Optional[RunnableConfig]) -> Dict[str, Any]:
        """Extract values from RunnableConfig."""
        if not config or "configurable" not in config:
            return {}
        return config["configurable"]
    
    @classmethod
    def _extract_environment_values(cls) -> Dict[str, Any]:
        """Extract configuration values from environment variables."""
        env_mappings = {
            "default_llm_model": "LLM_MODEL",
            "llm_provider": "LLM_PROVIDER",
            "max_papers": "MAX_PAPERS",
            "target_hypotheses_count": "NUM_HYPOTHESES",
            "max_workflow_iterations": "MAX_ITERATIONS",
        }
        
        values = {}
        for config_key, env_var in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                values[config_key] = cls._convert_env_value(config_key, env_value)
        
        return values
    
    @classmethod
    def _convert_env_value(cls, key: str, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        if key in ["max_papers", "target_hypotheses_count", "max_workflow_iterations"]:
            return int(value)
        elif key.endswith("_threshold") or key.endswith("_score"):
            return float(value)
        return value
    
    def to_runnable_config(self) -> RunnableConfig:
        """Convert configuration to RunnableConfig format for LangGraph."""
        return RunnableConfig(
            configurable={
                "llm_model": self.default_llm_model,
                "llm_provider": self.llm_provider,
                "max_papers": self.workflow_limits.max_papers,
                "target_hypotheses_count": self.workflow_limits.target_hypotheses_count,
                "max_workflow_iterations": self.workflow_limits.max_workflow_iterations,
                "max_agent_retries": self.workflow_limits.max_agent_retries,
                "supervisor_temperature": self.temperature_settings.supervisor,
                "literature_search_temperature": self.temperature_settings.literature_search,
                "synthesis_temperature": self.temperature_settings.synthesis,
                "hypothesis_generation_temperature": self.temperature_settings.hypothesis_generation,
                "validation_temperature": self.temperature_settings.validation,
                "min_hypothesis_confidence": self.quality_thresholds.min_hypothesis_confidence,
                "min_paper_relevance_score": self.quality_thresholds.min_paper_relevance_score,
            }
        )


# Alias for backward compatibility
Configuration = ResearchWorkflowConfiguration