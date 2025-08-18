"""Synthesis-related schemas"""

from typing import List
from pydantic import BaseModel, Field


class Pattern(BaseModel):
    """Pattern identified across papers"""
    description: str
    paper_ids: List[str]  # Papers supporting this pattern
    confidence: float = Field(ge=0.0, le=1.0)  # 0-1 confidence score


class Synthesis(BaseModel):
    """Minimal synthesis output"""
    patterns: List[Pattern]
    key_findings: List[str]
    research_gaps: List[str]
    total_papers_analyzed: int = Field(ge=0)