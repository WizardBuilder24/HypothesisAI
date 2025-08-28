"""
Pydantic schemas for HypothesisAI structured outputs
Adapted from Google's schema patterns
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ============================================================================
# SUPERVISOR SCHEMAS
# ============================================================================

class SupervisorDecision(BaseModel):
    """Supervisor routing decision"""
    next_agent: str = Field(
        description="Next agent to execute: literature_hunter, synthesizer, hypothesis_generator, validator, or end"
    )
    should_continue: bool = Field(
        description="Whether to continue the workflow"
    )
    reasoning: str = Field(
        description="Reasoning for the routing decision"
    )


# ============================================================================
# LITERATURE SEARCH SCHEMAS
# ============================================================================

class SearchQuery(BaseModel):
    """Individual search query"""
    query: str = Field(
        description="The search query string"
    )
    rationale: str = Field(
        description="Why this query is relevant"
    )


class SearchQueryList(BaseModel):
    """List of search queries for literature search"""
    queries: List[str] = Field(
        description="List of search query strings"
    )
    rationale: str = Field(
        description="Overall search strategy rationale"
    )


class SearchStrategy(BaseModel):
    """Individual arXiv search strategy"""
    query: str = Field(
        description="The arXiv search query string (optimized for arXiv API)"
    )
    focus: str = Field(
        description="Brief description of what this strategy targets"
    )
    expected_paper_types: str = Field(
        description="Types of papers this query should find"
    )
    priority: int = Field(
        description="Priority level 1-3 (1=highest priority, 3=exploratory)",
        ge=1, le=3
    )


class SearchStrategies(BaseModel):
    """Multiple search strategies for comprehensive literature search"""
    search_strategies: List[SearchStrategy] = Field(
        description="List of 2-4 complementary search strategies"
    )
    rationale: str = Field(
        description="Overall explanation of the multi-strategy approach"
    )
    coverage_analysis: str = Field(
        description="How these strategies complement each other"
    )


class SearchKeywords(BaseModel):
    """Keywords for arXiv search (deprecated - use SearchStrategies)"""
    keywords: List[str] = Field(
        description="List of 3-5 focused search keywords/phrases"
    )
    rationale: str = Field(
        description="Explanation of keyword selection strategy"
    )
    search_strategy: str = Field(
        description="Brief description of how keywords will be used"
    )


class Paper(BaseModel):
    """Research paper schema"""
    title: str = Field(description="Paper title")
    abstract: str = Field(description="Paper abstract")
    authors: List[str] = Field(description="List of authors")
    date_published: str = Field(description="Publication date (ISO format)")
    source: str = Field(description="Source (arxiv, biorxiv, etc.)")
    url: str = Field(description="Paper URL")
    categories: List[str] = Field(default=[], description="Categories/subjects")
    doi: Optional[str] = Field(default=None, description="DOI")
    citations: int = Field(default=0, description="Citation count")
    version: int = Field(default=1, description="Version number")
    pdf_url: Optional[str] = Field(default=None, description="PDF URL")
    relevance_score: float = Field(default=0.0, description="Relevance score (0-1)")
    quality_score: float = Field(default=0.0, description="Quality score (0-1)")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    
    # Legacy compatibility
    @property
    def year(self) -> Optional[int]:
        """Extract year from date_published for backward compatibility"""
        try:
            from datetime import datetime
            if isinstance(self.date_published, str):
                dt = datetime.fromisoformat(self.date_published.replace('Z', '+00:00'))
                return dt.year
            return None
        except:
            return None


class PaperList(BaseModel):
    """List of papers from literature search"""
    papers: List[Paper] = Field(description="List of papers found")
    total_found: int = Field(description="Total papers found")
    search_strategy: str = Field(description="Search strategy used")


# ============================================================================
# SYNTHESIS SCHEMAS
# ============================================================================

class Pattern(BaseModel):
    """Pattern identified in literature"""
    description: str = Field(description="Pattern description")
    paper_ids: List[str] = Field(description="Supporting paper IDs")
    confidence: float = Field(description="Confidence score (0-1)")


class SynthesisResult(BaseModel):
    """Knowledge synthesis result"""
    patterns: List[Pattern] = Field(description="Patterns identified")
    key_findings: List[str] = Field(description="Key findings")
    research_gaps: List[str] = Field(description="Research gaps identified")
    total_papers_analyzed: int = Field(description="Number of papers analyzed")


# ============================================================================
# HYPOTHESIS SCHEMAS
# ============================================================================

class Hypothesis(BaseModel):
    """Research hypothesis"""
    content: str = Field(description="Hypothesis statement")
    reasoning: str = Field(description="Reasoning behind hypothesis")
    confidence_score: float = Field(description="Confidence (0-1)")
    supporting_papers: List[str] = Field(default=[], description="Supporting paper IDs")
    novelty_score: float = Field(default=0.5, description="Novelty score (0-1)")
    feasibility_score: float = Field(default=0.5, description="Feasibility (0-1)")


class HypothesisList(BaseModel):
    """List of generated hypotheses"""
    hypotheses: List[Hypothesis] = Field(description="Generated hypotheses")
    generation_strategy: str = Field(description="Strategy used for generation")


# ============================================================================
# VALIDATION SCHEMAS
# ============================================================================

class ValidationResult(BaseModel):
    """Hypothesis validation result"""
    hypothesis_id: Optional[str] = Field(default=None, description="Hypothesis ID")
    is_valid: bool = Field(description="Whether hypothesis is valid")
    confidence: float = Field(description="Validation confidence (0-1)")
    issues: List[str] = Field(default=[], description="Issues found")
    recommendations: List[str] = Field(default=[], description="Recommendations")


class ValidationReport(BaseModel):
    """Complete validation report"""
    validation_results: List[ValidationResult] = Field(description="All validation results")
    overall_quality: float = Field(description="Overall quality score (0-1)")
    summary: str = Field(description="Validation summary")


# ============================================================================
# REFLECTION SCHEMAS (similar to Google's)
# ============================================================================

class Reflection(BaseModel):
    """Reflection on current research state"""
    is_sufficient: bool = Field(
        description="Whether current information is sufficient"
    )
    knowledge_gap: str = Field(
        description="Description of what's missing or needs clarification"
    )
    follow_up_queries: List[str] = Field(
        description="Follow-up queries to address gaps"
    )