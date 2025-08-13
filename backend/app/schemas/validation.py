"""Validation schemas"""

from typing import List
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Minimal validation result"""
    hypothesis_id: str
    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)  # 0-1
    issues: List[str]  # List of potential issues found
    recommendations: List[str]