"""Hypothesis and methodology schemas"""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class Hypothesis(BaseModel):
    """Generated hypothesis - minimal version"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str  # The hypothesis statement
    confidence_score: float = Field(ge=0.0, le=1.0)  # 0-1
    supporting_papers: List[str]  # Paper IDs
    reasoning: str  # Why this hypothesis was generated


class Methodology(BaseModel):
    """Basic methodology for testing hypothesis"""
    hypothesis_id: str
    approach: str  # Description of the experimental approach
    sample_size: Optional[int] = Field(None, ge=1)
    estimated_duration: Optional[str] = None  # e.g., "6 months"
    key_requirements: List[str]  # Main resources needed