"""
Configuration for HypothesisAI research workflow
Adapted from Google's configuration pattern
"""

import os
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal
from langchain_core.runnables import RunnableConfig


class Configuration(BaseModel):
    """The configuration for the HypothesisAI agent"""
    
    # Model configurations for each agent
    supervisor_model: str = Field(
        default="gemini-2.0-flash-exp",
        metadata={
            "description": "Model for the supervisor agent"
        },
    )
    
    literature_model: str = Field(
        default="gemini-2.0-flash-exp",
        metadata={
            "description": "Model for literature search"
        },
    )
    
    synthesis_model: str = Field(
        default="gemini-2.0-flash-exp",
        metadata={
            "description": "Model for knowledge synthesis"
        },
    )
    
    hypothesis_model: str = Field(
        default="gemini-2.0-flash-exp",
        metadata={
            "description": "Model for hypothesis generation"
        },
    )
    
    validation_model: str = Field(
        default="gemini-2.0-flash-exp",
        metadata={
            "description": "Model for hypothesis validation"
        },
    )
    
    # Workflow parameters
    max_papers: int = Field(
        default=20,
        metadata={"description": "Maximum number of papers to analyze"},
    )
    
    min_papers_threshold: int = Field(
        default=5,
        metadata={"description": "Minimum papers needed for synthesis"},
    )
    
    num_hypotheses: int = Field(
        default=3,
        metadata={"description": "Number of hypotheses to generate"},
    )
    
    max_iterations: int = Field(
        default=10,
        metadata={"description": "Maximum supervisor iterations before stopping"},
    )
    
    max_retries_per_agent: int = Field(
        default=3,
        metadata={"description": "Maximum retries for each agent on failure"},
    )
    
    # Quality thresholds
    min_confidence_threshold: float = Field(
        default=0.5,
        metadata={"description": "Minimum confidence score for hypotheses"},
    )
    
    min_patterns_for_synthesis: int = Field(
        default=2,
        metadata={"description": "Minimum patterns needed for good synthesis"},
    )
    
    # Temperature settings for different agents
    supervisor_temperature: float = Field(
        default=0.3,
        metadata={"description": "Temperature for supervisor (lower = more deterministic)"},
    )
    
    literature_temperature: float = Field(
        default=0.7,
        metadata={"description": "Temperature for literature search"},
    )
    
    synthesis_temperature: float = Field(
        default=0.5,
        metadata={"description": "Temperature for synthesis"},
    )
    
    hypothesis_temperature: float = Field(
        default=0.8,
        metadata={"description": "Temperature for hypothesis generation (higher = more creative)"},
    )
    
    validation_temperature: float = Field(
        default=0.3,
        metadata={"description": "Temperature for validation (lower = more strict)"},
    )
    
    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig"""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        
        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }
        
        # Convert string values to appropriate types
        for key, value in raw_values.items():
            if value is not None and isinstance(value, str):
                if key.endswith("_temperature") or key.endswith("_threshold"):
                    raw_values[key] = float(value)
                elif key.startswith("max_") or key.startswith("min_") or key.startswith("num_"):
                    if not key.endswith("_threshold"):
                        raw_values[key] = int(value)
        
        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}
        
        return cls(**values)