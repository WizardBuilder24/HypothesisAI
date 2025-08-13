"""
LangGraph Agent Schema for HypothesisAI Multi-Agent Research Platform
This module defines all Pydantic models and state schemas for agent communication
"""

from typing import TypedDict, List, Dict, Optional, Any, Literal, Annotated, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, conint, confloat
from uuid import UUID, uuid4
from langgraph.graph import StateGraph, MessagesState


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class AgentType(str, Enum):
    """Types of agents in the system"""
    SUPERVISOR = "supervisor"
    LITERATURE_HUNTER = "literature_hunter"
    KNOWLEDGE_SYNTHESIZER = "knowledge_synthesizer"
    HYPOTHESIS_GENERATOR = "hypothesis_generator"
    METHODOLOGY_DESIGNER = "methodology_designer"
    VALIDATION = "validation"


class DatabaseSource(str, Enum):
    """Available literature databases"""
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    BIORXIV = "biorxiv"
    CORE = "core"
    IEEE = "ieee"
    ACM = "acm"


class HypothesisStatus(str, Enum):
    """Status of generated hypotheses"""
    DRAFT = "draft"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"
    REVISED = "revised"


class WorkflowStatus(str, Enum):
    """Overall workflow execution status"""
    INITIALIZED = "initialized"
    SEARCHING = "searching"
    SYNTHESIZING = "synthesizing"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaperType(str, Enum):
    """Types of academic papers"""
    RESEARCH_ARTICLE = "research_article"
    REVIEW = "review"
    META_ANALYSIS = "meta_analysis"
    CASE_STUDY = "case_study"
    CLINICAL_TRIAL = "clinical_trial"
    PREPRINT = "preprint"
    CONFERENCE = "conference"
    THESIS = "thesis"


class StudyDesignType(str, Enum):
    """Types of study designs for methodology"""
    RCT = "randomized_controlled_trial"
    COHORT = "cohort_study"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    SYSTEMATIC_REVIEW = "systematic_review"
    EXPERIMENTAL = "experimental"
    OBSERVATIONAL = "observational"


class ValidationFlag(str, Enum):
    """Types of validation warnings"""
    P_HACKING = "p_hacking"
    PUBLICATION_BIAS = "publication_bias"
    CONFLICT_OF_INTEREST = "conflict_of_interest"
    RETRACTED_CITATION = "retracted_citation"
    SMALL_SAMPLE_SIZE = "small_sample_size"
    METHODOLOGICAL_FLAW = "methodological_flaw"
    STATISTICAL_ERROR = "statistical_error"


# ============================================================================
# BASE MODELS
# ============================================================================

class Author(BaseModel):
    """Author information"""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    email: Optional[str] = None


class Citation(BaseModel):
    """Citation information"""
    paper_id: str
    title: str
    authors: List[str]
    year: Optional[int] = None
    doi: Optional[str] = None


class SearchFilter(BaseModel):
    """Search filters for literature queries"""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    publication_types: List[PaperType] = Field(default_factory=list)
    min_citations: Optional[int] = Field(None, ge=0)
    max_citations: Optional[int] = Field(None, ge=0)
    authors: List[str] = Field(default_factory=list)
    journals: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    exclude_keywords: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=lambda: ["en"])
    open_access_only: bool = False


# ============================================================================
# PAPER AND DOCUMENT MODELS
# ============================================================================

class Paper(BaseModel):
    """Complete paper representation"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    doi: Optional[str] = None
    title: str
    abstract: Optional[str] = None
    authors: List[Author]
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    paper_type: Optional[PaperType] = None
    source_database: DatabaseSource
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    citation_count: int = 0
    keywords: List[str] = Field(default_factory=list)
    full_text: Optional[str] = None
    embedding: Optional[List[float]] = None
    quality_score: Optional[confloat(ge=0, le=1)] = None
    relevance_score: Optional[confloat(ge=0, le=1)] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    indexed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# ============================================================================
# SYNTHESIS MODELS
# ============================================================================

class Pattern(BaseModel):
    """Pattern identified across papers"""
    pattern_type: Literal["trend", "contradiction", "consensus", "gap", "emerging"]
    description: str
    evidence_papers: List[str]  # Paper IDs
    confidence: confloat(ge=0, le=1)
    temporal_trend: Optional[Dict[str, Any]] = None
    statistical_significance: Optional[float] = None


class KnowledgeCluster(BaseModel):
    """Cluster of related knowledge"""
    cluster_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    papers: List[str]  # Paper IDs
    key_concepts: List[str]
    relationships: Dict[str, List[str]]  # Concept relationships
    central_theme: str
    sub_themes: List[str] = Field(default_factory=list)


class ResearchGap(BaseModel):
    """Identified research gap"""
    gap_id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    importance: confloat(ge=0, le=1)
    related_papers: List[str]  # Papers that touch on but don't address the gap
    suggested_approaches: List[str]
    estimated_impact: str
    difficulty_level: Literal["low", "medium", "high"]


class SynthesisResult(BaseModel):
    """Complete synthesis output"""
    synthesis_id: str = Field(default_factory=lambda: str(uuid4()))
    patterns: List[Pattern]
    clusters: List[KnowledgeCluster]
    gaps: List[ResearchGap]
    key_findings: List[str]
    contradictions: List[Dict[str, Any]]
    consensus_points: List[Dict[str, Any]]
    statistical_summary: Dict[str, Any]
    temporal_analysis: Optional[Dict[str, Any]] = None
    network_analysis: Optional[Dict[str, Any]] = None  # Citation network
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# HYPOTHESIS MODELS
# ============================================================================

class Evidence(BaseModel):
    """Evidence supporting or contradicting a hypothesis"""
    paper_id: str
    paper_title: str
    excerpt: str
    support_type: Literal["supports", "contradicts", "neutral", "partial"]
    strength: confloat(ge=0, le=1)
    page_number: Optional[int] = None
    section: Optional[str] = None


class HypothesisReasoning(BaseModel):
    """Reasoning chain for hypothesis generation"""
    premise: str
    logical_steps: List[str]
    assumptions: List[str]
    cross_domain_connections: List[Dict[str, str]]  # Connections from different fields
    novelty_assessment: str
    theoretical_framework: Optional[str] = None


class Hypothesis(BaseModel):
    """Generated hypothesis"""
    hypothesis_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: Optional[str] = None
    content: str
    short_description: str
    hypothesis_type: Literal["mechanistic", "correlational", "interventional", "theoretical"]
    confidence_score: confloat(ge=0, le=1)
    novelty_score: confloat(ge=0, le=1)
    feasibility_score: confloat(ge=0, le=1)
    impact_score: confloat(ge=0, le=1)
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    reasoning: HypothesisReasoning
    testable_predictions: List[str]
    required_resources: List[str]
    estimated_validation_time: Optional[str] = None
    cross_domain_applications: List[str] = Field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.DRAFT
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: AgentType = AgentType.HYPOTHESIS_GENERATOR


# ============================================================================
# METHODOLOGY MODELS
# ============================================================================

class SampleSize(BaseModel):
    """Sample size calculation"""
    recommended_n: int
    power: float = 0.8
    alpha: float = 0.05
    effect_size: float
    calculation_method: str
    justification: str


class ExperimentalDesign(BaseModel):
    """Experimental design specification"""
    design_type: StudyDesignType
    description: str
    variables: Dict[str, List[str]]  # independent, dependent, control
    sample_size: SampleSize
    duration: str
    data_collection_methods: List[str]
    control_conditions: List[str]
    randomization_strategy: Optional[str] = None
    blinding_approach: Optional[str] = None
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]


class ResourceRequirement(BaseModel):
    """Resource requirements for methodology"""
    equipment: List[str]
    personnel: List[Dict[str, str]]  # role and expertise needed
    estimated_cost: Optional[float] = None
    cost_breakdown: Optional[Dict[str, float]] = None
    timeline: str
    facilities: List[str]
    software: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)


class StatisticalAnalysisPlan(BaseModel):
    """Statistical analysis plan"""
    primary_analysis: str
    secondary_analyses: List[str]
    statistical_tests: List[str]
    correction_methods: List[str]  # Multiple testing corrections
    missing_data_strategy: str
    sensitivity_analyses: List[str]
    software_requirements: List[str]


class Methodology(BaseModel):
    """Complete methodology for testing hypothesis"""
    methodology_id: str = Field(default_factory=lambda: str(uuid4()))
    hypothesis_id: str
    title: str
    experimental_design: ExperimentalDesign
    resources: ResourceRequirement
    statistical_plan: StatisticalAnalysisPlan
    ethical_considerations: List[str]
    potential_limitations: List[str]
    alternative_approaches: List[Dict[str, str]]
    pilot_study_recommendation: Optional[str] = None
    risk_assessment: Dict[str, str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# VALIDATION MODELS
# ============================================================================

class ValidationIssue(BaseModel):
    """Issue identified during validation"""
    issue_type: ValidationFlag
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    affected_papers: List[str]
    recommendation: str
    supporting_data: Optional[Dict[str, Any]] = None


class ValidationMetrics(BaseModel):
    """Metrics from validation process"""
    statistical_rigor_score: confloat(ge=0, le=1)
    methodology_quality_score: confloat(ge=0, le=1)
    evidence_consistency_score: confloat(ge=0, le=1)
    replication_likelihood: confloat(ge=0, le=1)
    bias_assessment: Dict[str, float]


class ValidationResult(BaseModel):
    """Complete validation result"""
    validation_id: str = Field(default_factory=lambda: str(uuid4()))
    hypothesis_id: str
    overall_validity: Literal["valid", "partially_valid", "invalid", "requires_revision"]
    confidence_level: confloat(ge=0, le=1)
    issues: List[ValidationIssue]
    metrics: ValidationMetrics
    recommendations: List[str]
    alternative_interpretations: List[str]
    replication_suggestions: List[str]
    peer_review_readiness: bool
    validated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# AGENT COMMUNICATION MODELS
# ============================================================================

class AgentMessage(BaseModel):
    """Message passed between agents"""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    from_agent: AgentType
    to_agent: AgentType
    message_type: Literal["request", "response", "error", "status", "data"]
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=10)


class AgentTaskRequest(BaseModel):
    """Task request for an agent"""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    task_type: str
    parameters: Dict[str, Any]
    deadline: Optional[datetime] = None
    priority: int = Field(default=5, ge=1, le=10)
    retry_count: int = Field(default=0, ge=0, le=3)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)


class AgentTaskResponse(BaseModel):
    """Response from agent task execution"""
    task_id: str
    status: Literal["success", "failure", "partial", "timeout"]
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MAIN RESEARCH STATE
# ============================================================================

class ResearchState(TypedDict):
    """
    Global state for the research workflow.
    This is the main state that gets passed between all agents.
    """
    # Workflow metadata
    workflow_id: str
    project_id: str
    user_id: str
    workflow_status: WorkflowStatus
    current_agent: AgentType
    
    # Input parameters
    research_query: str
    databases: List[DatabaseSource]
    search_filters: Optional[Dict[str, Any]]
    max_papers: int
    
    # Agent outputs
    papers: List[Dict[str, Any]]  # List of Paper models as dicts
    synthesis: Optional[Dict[str, Any]]  # SynthesisResult as dict
    hypotheses: List[Dict[str, Any]]  # List of Hypothesis models as dicts
    methodologies: List[Dict[str, Any]]  # List of Methodology models as dicts
    validation_results: List[Dict[str, Any]]  # List of ValidationResult as dicts
    
    # Execution tracking
    agent_messages: List[Dict[str, Any]]  # List of AgentMessage as dicts
    execution_history: List[Dict[str, Any]]
    error_log: List[str]
    performance_metrics: Dict[str, Any]
    
    # Control flow
    should_continue: bool
    requires_human_input: bool
    human_feedback: Optional[str]
    
    # Results and scoring
    confidence_scores: Dict[str, float]
    quality_metrics: Dict[str, Any]
    final_recommendations: List[str]
    
    # Timestamps
    started_at: str  # ISO format timestamp
    completed_at: Optional[str]  # ISO format timestamp
    last_updated: str  # ISO format timestamp


# ============================================================================
# AGENT-SPECIFIC STATES
# ============================================================================

class LiteratureHunterState(BaseModel):
    """State specific to Literature Hunter agent"""
    search_queries: List[str]
    databases_searched: List[DatabaseSource]
    total_papers_found: int
    papers_filtered: int
    search_iterations: int
    semantic_clusters: List[Dict[str, Any]]
    query_expansions: List[str]
    failed_searches: List[Dict[str, str]]


class KnowledgeSynthesizerState(BaseModel):
    """State specific to Knowledge Synthesizer agent"""
    papers_analyzed: int
    patterns_identified: int
    clusters_formed: int
    gaps_identified: int
    synthesis_methods_used: List[str]
    confidence_threshold: float
    minimum_evidence_papers: int


class HypothesisGeneratorState(BaseModel):
    """State specific to Hypothesis Generator agent"""
    generation_strategies: List[str]
    hypotheses_generated: int
    hypotheses_filtered: int
    novelty_threshold: float
    cross_domain_connections: int
    creativity_temperature: float


class MethodologyDesignerState(BaseModel):
    """State specific to Methodology Designer agent"""
    designs_considered: List[str]
    feasibility_assessments: Dict[str, float]
    resource_constraints: Dict[str, Any]
    ethical_review_required: bool
    alternative_approaches: int


class ValidationAgentState(BaseModel):
    """State specific to Validation agent"""
    validation_criteria: List[str]
    issues_found: int
    critical_issues: int
    papers_flagged: List[str]
    statistical_tests_performed: List[str]
    confidence_threshold: float


# ============================================================================
# SUPERVISOR DECISION MODELS
# ============================================================================

class SupervisorDecision(BaseModel):
    """Decision made by supervisor agent"""
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    decision_type: Literal["route", "retry", "escalate", "complete", "abort"]
    next_agent: Optional[AgentType] = None
    reason: str
    confidence: confloat(ge=0, le=1)
    requires_human_approval: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowTransition(BaseModel):
    """Transition between workflow states"""
    from_state: WorkflowStatus
    to_state: WorkflowStatus
    triggered_by: AgentType
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_snapshot: Optional[Dict[str, Any]] = None


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class AgentConfig(BaseModel):
    """Configuration for individual agents"""
    agent_type: AgentType
    enabled: bool = True
    timeout_seconds: int = 300
    max_retries: int = 3
    llm_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)


class WorkflowConfig(BaseModel):
    """Configuration for entire workflow"""
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    agent_configs: List[AgentConfig]
    max_execution_time: int = 3600  # seconds
    human_in_loop: bool = True
    auto_retry_on_failure: bool = True
    notification_webhooks: List[str] = Field(default_factory=list)
    quality_thresholds: Dict[str, float] = Field(default_factory=dict)


# ============================================================================
# RESULT AGGREGATION MODELS
# ============================================================================

class ResearchReport(BaseModel):
    """Final research report combining all agent outputs"""
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    title: str
    executive_summary: str
    
    # Research findings
    papers_analyzed: int
    key_papers: List[Paper]
    synthesis_summary: SynthesisResult
    
    # Generated content
    top_hypotheses: List[Hypothesis]
    recommended_methodologies: List[Methodology]
    validation_summary: List[ValidationResult]
    
    # Insights
    major_findings: List[str]
    research_gaps: List[ResearchGap]
    future_directions: List[str]
    interdisciplinary_opportunities: List[str]
    
    # Metadata
    confidence_score: confloat(ge=0, le=1)
    quality_score: confloat(ge=0, le=1)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_time_seconds: int
    
    # Visualizations data
    knowledge_graph: Optional[Dict[str, Any]] = None
    trend_analysis: Optional[Dict[str, Any]] = None
    citation_network: Optional[Dict[str, Any]] = None


# ============================================================================
# ERROR HANDLING MODELS
# ============================================================================

class AgentError(BaseModel):
    """Error from agent execution"""
    error_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_type: AgentType
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recoverable: bool = True
    suggested_action: Optional[str] = None


# ============================================================================
# HELPER FUNCTIONS FOR STATE MANAGEMENT
# ============================================================================

def serialize_state(state: ResearchState) -> Dict[str, Any]:
    """Serialize state for storage or transmission"""
    return {
        k: v if not isinstance(v, (BaseModel, datetime)) else (
            v.dict() if isinstance(v, BaseModel) else v.isoformat()
        )
        for k, v in state.items()
    }


def deserialize_state(data: Dict[str, Any]) -> ResearchState:
    """Deserialize state from storage"""
    # Convert ISO strings back to datetime objects where needed
    if 'started_at' in data and isinstance(data['started_at'], str):
        data['started_at'] = data['started_at']
    if 'completed_at' in data and data['completed_at'] and isinstance(data['completed_at'], str):
        data['completed_at'] = data['completed_at']
    if 'last_updated' in data and isinstance(data['last_updated'], str):
        data['last_updated'] = data['last_updated']
    
    return ResearchState(**data)


def create_initial_state(
    research_query: str,
    databases: List[DatabaseSource],
    project_id: str,
    user_id: str,
    **kwargs
) -> ResearchState:
    """Create initial state for workflow"""
    now = datetime.utcnow().isoformat()
    
    return ResearchState(
        workflow_id=str(uuid4()),
        project_id=project_id,
        user_id=user_id,
        workflow_status=WorkflowStatus.INITIALIZED,
        current_agent=AgentType.SUPERVISOR,
        research_query=research_query,
        databases=databases,
        search_filters=kwargs.get('search_filters'),
        max_papers=kwargs.get('max_papers', 100),
        papers=[],
        synthesis=None,
        hypotheses=[],
        methodologies=[],
        validation_results=[],
        agent_messages=[],
        execution_history=[],
        error_log=[],
        performance_metrics={},
        should_continue=True,
        requires_human_input=False,
        human_feedback=None,
        confidence_scores={},
        quality_metrics={},
        final_recommendations=[],
        started_at=now,
        completed_at=None,
        last_updated=now
    )


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_paper_quality(paper: Paper) -> bool:
    """Validate paper quality based on various metrics"""
    if not paper.title or not paper.abstract:
        return False
    if paper.quality_score and paper.quality_score < 0.3:
        return False
    if len(paper.abstract) < 100:  # Too short abstract
        return False
    return True


def validate_hypothesis_quality(hypothesis: Hypothesis) -> bool:
    """Validate hypothesis quality"""
    if hypothesis.confidence_score < 0.5:
        return False
    if len(hypothesis.supporting_evidence) < 2:
        return False
    if hypothesis.feasibility_score < 0.3:
        return False
    return True


def validate_methodology(methodology: Methodology) -> bool:
    """Validate methodology completeness"""
    if not methodology.experimental_design:
        return False
    if not methodology.statistical_plan:
        return False
    if methodology.resources.estimated_cost and methodology.resources.estimated_cost > 10000000:  # $10M limit
        return False
    return True


# ============================================================================
# WORKFLOW TRACKING MODELS
# ============================================================================

class WorkflowMetrics(BaseModel):
    """Metrics for workflow execution"""
    total_papers_processed: int = 0
    total_hypotheses_generated: int = 0
    total_execution_time_ms: int = 0
    agent_execution_times: Dict[str, int] = Field(default_factory=dict)
    cache_hit_rate: float = 0.0
    api_calls_made: Dict[str, int] = Field(default_factory=dict)
    tokens_consumed: Dict[str, int] = Field(default_factory=dict)
    error_rate: float = 0.0
    retry_count: int = 0


class QualityMetrics(BaseModel):
    """Quality metrics for research output"""
    paper_relevance_avg: float = 0.0
    hypothesis_novelty_avg: float = 0.0
    hypothesis_confidence_avg: float = 0.0
    validation_rigor_avg: float = 0.0
    cross_domain_connections: int = 0
    unique_insights: int = 0
    actionable_recommendations: int = 0


# ============================================================================
# COLLABORATION MODELS
# ============================================================================

class CollaborationEvent(BaseModel):
    """Event in collaborative research"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: Literal["comment", "annotation", "revision", "approval", "rejection"]
    user_id: str
    target_type: Literal["paper", "hypothesis", "methodology", "validation"]
    target_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserFeedback(BaseModel):
    """User feedback on generated content"""
    feedback_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    target_type: str
    target_id: str
    rating: Optional[conint(ge=1, le=5)] = None
    feedback_text: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# CACHING MODELS
# ============================================================================

class CacheEntry(BaseModel):
    """Cache entry for storing intermediate results"""
    key: str
    value: Any
    cache_type: Literal["search", "synthesis", "hypothesis", "validation"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    size_bytes: Optional[int] = None


# ============================================================================
# EXTERNAL API MODELS
# ============================================================================

class ExternalAPICall(BaseModel):
    """Track external API calls"""
    api_name: str
    endpoint: str
    method: str
    request_data: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LiteratureSearchRequest(BaseModel):
    """Request for literature search"""
    query: str
    databases: List[DatabaseSource]
    filters: Optional[SearchFilter] = None
    max_results: int = Field(default=100, ge=1, le=1000)
    sort_by: Literal["relevance", "date", "citations"] = "relevance"
    include_full_text: bool = False
    semantic_search: bool = True
    query_expansion: bool = True


class LiteratureSearchResponse(BaseModel):
    """Response from literature search"""
    request_id: str
    total_results: int
    returned_results: int
    papers: List[Paper]
    search_metadata: Dict[str, Any]
    execution_time_ms: int
    cached: bool = False


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

class PromptTemplate(BaseModel):
    """Template for agent prompts"""
    template_id: str
    agent_type: AgentType
    template_name: str
    template_text: str
    variables: List[str]
    version: str = "1.0"
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    
    def format(self, **kwargs) -> str:
        """Format template with provided variables"""
        return self.template_text.format(**kwargs)


# ============================================================================
# ADVANCED HYPOTHESIS MODELS
# ============================================================================

class HypothesisEvolution(BaseModel):
    """Track hypothesis evolution over iterations"""
    hypothesis_id: str
    version: int
    previous_version_id: Optional[str] = None
    changes: List[str]
    change_reason: str
    improved_metrics: Dict[str, float]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrossDomainConnection(BaseModel):
    """Connection between different research domains"""
    connection_id: str = Field(default_factory=lambda: str(uuid4()))
    source_domain: str
    target_domain: str
    connection_type: Literal["analogy", "method_transfer", "concept_mapping", "theoretical_bridge"]
    description: str
    strength: confloat(ge=0, le=1)
    evidence: List[str]  # Paper IDs
    potential_impact: str
    novelty_score: confloat(ge=0, le=1)


# ============================================================================
# ADVANCED VALIDATION MODELS
# ============================================================================

class StatisticalTest(BaseModel):
    """Statistical test performed during validation"""
    test_name: str
    test_type: Literal["parametric", "non_parametric", "bayesian"]
    null_hypothesis: str
    alternative_hypothesis: str
    test_statistic: float
    p_value: Optional[float] = None
    confidence_interval: Optional[List[float]] = None
    effect_size: Optional[float] = None
    power: Optional[float] = None
    assumptions_met: bool
    assumptions_tested: List[str]
    interpretation: str


class ReplicationAssessment(BaseModel):
    """Assessment of replication likelihood"""
    replication_score: confloat(ge=0, le=1)
    required_sample_size: int
    estimated_cost: float
    time_required: str
    key_challenges: List[str]
    success_predictors: List[str]
    previous_replication_attempts: List[Dict[str, Any]]


# ============================================================================
# KNOWLEDGE GRAPH MODELS
# ============================================================================

class KnowledgeNode(BaseModel):
    """Node in knowledge graph"""
    node_id: str = Field(default_factory=lambda: str(uuid4()))
    node_type: Literal["concept", "paper", "author", "method", "finding", "hypothesis"]
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    importance_score: confloat(ge=0, le=1) = 0.5


class KnowledgeEdge(BaseModel):
    """Edge in knowledge graph"""
    edge_id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    edge_type: Literal["cites", "supports", "contradicts", "extends", "applies", "related_to"]
    weight: confloat(ge=0, le=1) = 0.5
    properties: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraph(BaseModel):
    """Complete knowledge graph"""
    graph_id: str = Field(default_factory=lambda: str(uuid4()))
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_node_degree(self, node_id: str) -> int:
        """Get degree of a node"""
        return sum(1 for edge in self.edges 
                  if edge.source_id == node_id or edge.target_id == node_id)
    
    def get_connected_nodes(self, node_id: str) -> List[str]:
        """Get all nodes connected to a given node"""
        connected = set()
        for edge in self.edges:
            if edge.source_id == node_id:
                connected.add(edge.target_id)
            elif edge.target_id == node_id:
                connected.add(edge.source_id)
        return list(connected)


# ============================================================================
# EXPORT AND REPORTING MODELS
# ============================================================================

class ExportFormat(str, Enum):
    """Available export formats"""
    JSON = "json"
    PDF = "pdf"
    DOCX = "docx"
    LATEX = "latex"
    MARKDOWN = "markdown"
    HTML = "html"
    BIBTEX = "bibtex"


class ExportRequest(BaseModel):
    """Request for exporting research results"""
    export_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    format: ExportFormat
    include_sections: List[str] = Field(default_factory=lambda: ["all"])
    include_visualizations: bool = True
    include_raw_data: bool = False
    include_appendices: bool = True
    custom_styling: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VisualizationSpec(BaseModel):
    """Specification for data visualization"""
    viz_id: str = Field(default_factory=lambda: str(uuid4()))
    viz_type: Literal["network", "timeline", "heatmap", "scatter", "bar", "sankey", "wordcloud"]
    data_source: str
    title: str
    config: Dict[str, Any]
    interactive: bool = True
    export_formats: List[str] = Field(default_factory=lambda: ["png", "svg"])


# ============================================================================
# MONITORING AND ALERTING MODELS
# ============================================================================

class PerformanceAlert(BaseModel):
    """Performance alert"""
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_type: Literal["latency", "error_rate", "resource_usage", "quality_threshold"]
    severity: Literal["info", "warning", "error", "critical"]
    message: str
    metric_value: float
    threshold_value: float
    agent_type: Optional[AgentType] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class SystemHealth(BaseModel):
    """System health status"""
    status: Literal["healthy", "degraded", "unhealthy"]
    uptime_seconds: int
    active_workflows: int
    queued_tasks: int
    error_rate_1m: float
    error_rate_5m: float
    avg_latency_ms: float
    cpu_usage_percent: float
    memory_usage_percent: float
    agent_statuses: Dict[str, str]
    last_check: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def merge_synthesis_results(results: List[SynthesisResult]) -> SynthesisResult:
    """Merge multiple synthesis results into one"""
    if not results:
        raise ValueError("No synthesis results to merge")
    
    if len(results) == 1:
        return results[0]
    
    merged = SynthesisResult(
        synthesis_id=str(uuid4()),
        patterns=[],
        clusters=[],
        gaps=[],
        key_findings=[],
        contradictions=[],
        consensus_points=[],
        statistical_summary={},
        generated_at=datetime.utcnow()
    )
    
    # Merge patterns, removing duplicates based on description
    seen_patterns = set()
    for result in results:
        for pattern in result.patterns:
            if pattern.description not in seen_patterns:
                merged.patterns.append(pattern)
                seen_patterns.add(pattern.description)
    
    # Merge other fields similarly
    for result in results:
        merged.clusters.extend(result.clusters)
        merged.gaps.extend(result.gaps)
        merged.key_findings.extend(result.key_findings)
        merged.contradictions.extend(result.contradictions)
        merged.consensus_points.extend(result.consensus_points)
    
    return merged


def calculate_hypothesis_composite_score(hypothesis: Hypothesis) -> float:
    """Calculate composite score for hypothesis ranking"""
    weights = {
        'confidence': 0.3,
        'novelty': 0.25,
        'feasibility': 0.2,
        'impact': 0.25
    }
    
    score = (
        weights['confidence'] * hypothesis.confidence_score +
        weights['novelty'] * hypothesis.novelty_score +
        weights['feasibility'] * hypothesis.feasibility_score +
        weights['impact'] * hypothesis.impact_score
    )
    
    # Adjust based on evidence
    evidence_factor = len(hypothesis.supporting_evidence) / (len(hypothesis.supporting_evidence) + len(hypothesis.contradicting_evidence) + 1)
    
    return score * (0.5 + 0.5 * evidence_factor)


def filter_high_quality_papers(papers: List[Paper], min_quality: float = 0.7) -> List[Paper]:
    """Filter papers by quality score"""
    return [p for p in papers if p.quality_score and p.quality_score >= min_quality]


def group_papers_by_year(papers: List[Paper]) -> Dict[int, List[Paper]]:
    """Group papers by publication year"""
    grouped = {}
    for paper in papers:
        if paper.publication_date:
            year = paper.publication_date.year
            if year not in grouped:
                grouped[year] = []
            grouped[year].append(paper)
    return grouped


def extract_top_keywords(papers: List[Paper], top_n: int = 20) -> List[tuple[str, int]]:
    """Extract most common keywords from papers"""
    from collections import Counter
    
    all_keywords = []
    for paper in papers:
        all_keywords.extend(paper.keywords)
    
    keyword_counts = Counter(all_keywords)
    return keyword_counts.most_common(top_n)


# ============================================================================
# EXPORT THE COMPLETE SCHEMA
# ============================================================================

__all__ = [
    # Main state
    'ResearchState',
    
    # Enums
    'AgentType', 'DatabaseSource', 'HypothesisStatus', 'WorkflowStatus',
    'PaperType', 'StudyDesignType', 'ValidationFlag', 'ExportFormat',
    
    # Core models
    'Paper', 'Author', 'Citation', 'SearchFilter',
    'SynthesisResult', 'Pattern', 'KnowledgeCluster', 'ResearchGap',
    'Hypothesis', 'Evidence', 'HypothesisReasoning', 'HypothesisEvolution',
    'Methodology', 'ExperimentalDesign', 'ResourceRequirement', 'StatisticalAnalysisPlan',
    'ValidationResult', 'ValidationIssue', 'ValidationMetrics', 'StatisticalTest',
    
    # Agent models
    'AgentMessage', 'AgentTaskRequest', 'AgentTaskResponse',
    'SupervisorDecision', 'WorkflowTransition',
    'LiteratureHunterState', 'KnowledgeSynthesizerState',
    'HypothesisGeneratorState', 'MethodologyDesignerState', 'ValidationAgentState',
    
    # Supporting models
    'WorkflowConfig', 'AgentConfig', 'ResearchReport',
    'WorkflowMetrics', 'QualityMetrics',
    'KnowledgeGraph', 'KnowledgeNode', 'KnowledgeEdge',
    'CollaborationEvent', 'UserFeedback',
    'CacheEntry', 'ExternalAPICall',
    'PromptTemplate', 'ExportRequest', 'VisualizationSpec',
    'PerformanceAlert', 'SystemHealth',
    
    # Utility functions
    'create_initial_state', 'serialize_state', 'deserialize_state',
    'validate_paper_quality', 'validate_hypothesis_quality', 'validate_methodology',
    'merge_synthesis_results', 'calculate_hypothesis_composite_score',
    'filter_high_quality_papers', 'group_papers_by_year', 'extract_top_keywords'
]