"""Paper-related schemas"""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class Paper(BaseModel):
    """Minimal paper representation"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    abstract: str
    authors: List[str]  # Simple list of author names
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    relevance_score: float = 0.0  # How relevant to the query
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Deep Learning in Medical Imaging",
                "abstract": "This paper explores...",
                "authors": ["John Doe", "Jane Smith"],
                "year": 2024,
                "doi": "10.1234/example",
                "relevance_score": 0.95
            }
        }