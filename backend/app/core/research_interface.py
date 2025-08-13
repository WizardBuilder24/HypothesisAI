"""
Public interface for the research system with multi-LLM support using LangChain
"""

from typing import Optional, Dict, Any, List, AsyncGenerator, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime

from app.core.llm_clients import (
    LLMProvider,
    LangChainLLMClient,
    create_llm_client
)
from app.agents.orchestrator import ResearchOrchestrator
from app.schemas import ResearchState, WorkflowStatus
from app.core.state_management import get_workflow_summary

logger = logging.getLogger(__name__)


class OutputFormat(str, Enum):
    """Output format options"""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


@dataclass
class ResearchConfig:
    """Configuration for research execution"""
    llm_provider: LLMProvider = LLMProvider.OPENAI
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    streaming: bool = False
    max_papers: int = 50
    creativity_temperature: float = 0.7
    strict_validation: bool = False
    output_format: OutputFormat = OutputFormat.JSON
    save_checkpoints: bool = True
    timeout_seconds: Optional[int] = 300
    
    # Advanced options
    system_prompt: Optional[str] = None
    max_tokens: int = 2000
    search_client: Optional[Any] = None
    additional_config: Dict[str, Any] = None


@dataclass
class ResearchResult:
    """Result of research execution"""
    workflow_id: str
    status: WorkflowStatus
    query: str
    papers_found: int
    hypotheses_generated: int
    valid_hypotheses: int
    execution_time_seconds: float
    data: Dict[str, Any]
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "query": self.query,
            "statistics": {
                "papers_found": self.papers_found,
                "hypotheses_generated": self.hypotheses_generated,
                "valid_hypotheses": self.valid_hypotheses,
                "execution_time_seconds": self.execution_time_seconds
            },
            "data": self.data,
            "errors": self.errors
        }
    
    def to_markdown(self) -> str:
        """Convert to markdown format"""
        md = f"""# Research Results

## Query
{self.query}

## Summary
- **Workflow ID**: {self.workflow_id}
- **Status**: {self.status.value}
- **Papers Found**: {self.papers_found}
- **Hypotheses Generated**: {self.hypotheses_generated}
- **Valid Hypotheses**: {self.valid_hypotheses}
- **Execution Time**: {self.execution_time_seconds:.2f} seconds

## Hypotheses
"""
        for i, hypothesis in enumerate(self.data.get("hypotheses", []), 1):
            md += f"\n### Hypothesis {i}\n"
            md += f"**Content**: {hypothesis.get('content', 'N/A')}\n\n"
            md += f"**Confidence**: {hypothesis.get('confidence_score', 0):.2f}\n\n"
            md += f"**Reasoning**: {hypothesis.get('reasoning', 'N/A')}\n\n"
        
        if self.errors:
            md += "\n## Errors\n"
            for error in self.errors:
                md += f"- {error}\n"
        
        return md
    
    def to_html(self) -> str:
        """Convert to HTML format"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Research Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .hypothesis {{ background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .error {{ color: #d00; }}
    </style>
</head>
<body>
    <h1>Research Results</h1>
    <h2>Query</h2>
    <p>{self.query}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li><strong>Workflow ID</strong>: {self.workflow_id}</li>
            <li><strong>Status</strong>: {self.status.value}</li>
            <li><strong>Papers Found</strong>: {self.papers_found}</li>
            <li><strong>Hypotheses Generated</strong>: {self.hypotheses_generated}</li>
            <li><strong>Valid Hypotheses</strong>: {self.valid_hypotheses}</li>
            <li><strong>Execution Time</strong>: {self.execution_time_seconds:.2f} seconds</li>
        </ul>
    </div>
"""
        
        if self.data.get("hypotheses"):
            html += "<h2>Hypotheses</h2>"
            for i, hypothesis in enumerate(self.data["hypotheses"], 1):
                html += f"""
    <div class="hypothesis">
        <h3>Hypothesis {i}</h3>
        <p><strong>Content</strong>: {hypothesis.get('content', 'N/A')}</p>
        <p><strong>Confidence</strong>: {hypothesis.get('confidence_score', 0):.2f}</p>
        <p><strong>Reasoning</strong>: {hypothesis.get('reasoning', 'N/A')}</p>
    </div>
"""
        
        if self.errors:
            html += "<h2>Errors</h2><ul class='error'>"
            for error in self.errors:
                html += f"<li>{error}</li>"
            html += "</ul>"
        
        html += "</body></html>"
        return html


class ResearchInterface:
    """
    Main public interface for the research system using LangChain
    """
    
    def __init__(self, config: Optional[ResearchConfig] = None):
        """
        Initialize the research interface
        
        Args:
            config: Research configuration
        """
        self.config = config or ResearchConfig()
        self.orchestrator = None
        self.llm_client = None
        
        # Initialize components
        self._initialize()
    
    def _initialize(self):
        """Initialize LLM client and orchestrator"""
        # Create LangChain LLM client
        self.llm_client = LangChainLLMClient(
            provider=self.config.llm_provider,
            api_key=self.config.llm_api_key,
            model=self.config.llm_model,
            temperature=self.config.creativity_temperature,
            max_tokens=self.config.max_tokens,
            streaming=self.config.streaming
        )
        
        # Create orchestrator
        self.orchestrator = ResearchOrchestrator(
            llm_client=self.llm_client,
            search_client=self.config.search_client,
            config={
                "creativity_temperature": self.config.creativity_temperature,
                "strict_validation": self.config.strict_validation,
                **(self.config.additional_config or {})
            }
        )
        
        logger.info(
            f"Research interface initialized with {self.config.llm_provider.value} "
            f"(model: {self.llm_client.get_model_name()}, "
            f"streaming={'enabled' if self.config.streaming else 'disabled'})"
        )
    
    async def run_research(
        self,
        query: str,
        max_papers: Optional[int] = None
    ) -> ResearchResult:
        """
        Run research workflow (non-streaming)
        
        Args:
            query: Research question
            max_papers: Maximum papers to analyze (overrides config)
            
        Returns:
            Research result
        """
        start_time = datetime.utcnow()
        max_papers = max_papers or self.config.max_papers
        
        logger.info(f"Starting research: {query[:100]}...")
        
        try:
            # Run with timeout if configured
            if self.config.timeout_seconds:
                result = await asyncio.wait_for(
                    self.orchestrator.run_research(query, max_papers),
                    timeout=self.config.timeout_seconds
                )
            else:
                result = await self.orchestrator.run_research(query, max_papers)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result object
            research_result = self._create_result(result, query, execution_time)
            
            # Format based on configuration
            return self._format_result(research_result)
            
        except asyncio.TimeoutError:
            logger.error(f"Research timeout after {self.config.timeout_seconds} seconds")
            raise TimeoutError(f"Research exceeded timeout of {self.config.timeout_seconds} seconds")
        except Exception as e:
            logger.error(f"Research failed: {e}")
            raise
    
    async def run_research_stream(
        self,
        query: str,
        max_papers: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run research workflow with streaming updates
        
        Args:
            query: Research question
            max_papers: Maximum papers to analyze
            
        Yields:
            Progress updates and final result
        """
        if not self.config.streaming:
            raise ValueError("Streaming not enabled in configuration")
        
        start_time = datetime.utcnow()
        max_papers = max_papers or self.config.max_papers
        
        logger.info(f"Starting streaming research: {query[:100]}...")
        
        try:
            async for state_update in self.orchestrator.run_research_stream(query, max_papers):
                # Format progress update
                if isinstance(state_update, dict):
                    progress = self._create_progress_update(state_update, start_time)
                    yield progress
            
            # Yield final result
            if isinstance(state_update, dict):
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                final_result = self._create_result(state_update, query, execution_time)
                yield {
                    "type": "final",
                    "result": self._format_result(final_result)
                }
                
        except Exception as e:
            logger.error(f"Streaming research failed: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def _create_result(
        self,
        state: Dict[str, Any],
        query: str,
        execution_time: float
    ) -> ResearchResult:
        """Create research result from final state"""
        # Count valid hypotheses
        valid_count = sum(
            1 for v in state.get("validation_results", [])
            if v.get("is_valid")
        )
        
        return ResearchResult(
            workflow_id=state.get("workflow_id", "unknown"),
            status=state.get("status", WorkflowStatus.FAILED),
            query=query,
            papers_found=len(state.get("papers", [])),
            hypotheses_generated=len(state.get("hypotheses", [])),
            valid_hypotheses=valid_count,
            execution_time_seconds=execution_time,
            data={
                "papers": state.get("papers", []),
                "synthesis": state.get("synthesis"),
                "hypotheses": state.get("hypotheses", []),
                "methodologies": state.get("methodologies", []),
                "validation_results": state.get("validation_results", [])
            },
            errors=state.get("errors", [])
        )
    
    def _format_result(self, result: ResearchResult) -> Union[Dict, str]:
        """Format result based on output configuration"""
        if self.config.output_format == OutputFormat.JSON:
            return result.to_dict()
        elif self.config.output_format == OutputFormat.MARKDOWN:
            return result.to_markdown()
        elif self.config.output_format == OutputFormat.HTML:
            return result.to_html()
        else:
            return result.to_dict()
    
    def _create_progress_update(
        self,
        state: Dict[str, Any],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create progress update from intermediate state"""
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "type": "progress",
            "workflow_id": state.get("workflow_id"),
            "current_agent": state.get("current_agent"),
            "status": state.get("status"),
            "elapsed_seconds": elapsed,
            "papers_found": len(state.get("papers", [])),
            "hypotheses_generated": len(state.get("hypotheses", [])),
            "message": self._get_progress_message(state)
        }
    
    def _get_progress_message(self, state: Dict[str, Any]) -> str:
        """Get human-readable progress message"""
        agent = state.get("current_agent", "unknown")
        status = state.get("status", "unknown")
        
        messages = {
            "literature_hunter": "Searching for relevant papers...",
            "knowledge_synthesizer": "Analyzing and synthesizing findings...",
            "hypothesis_generator": "Generating research hypotheses...",
            "methodology_designer": "Designing experimental methodologies...",
            "validation": "Validating hypotheses and methodologies...",
            "supervisor": "Coordinating workflow..."
        }
        
        return messages.get(agent, f"Processing {agent}...")
    
    async def get_supported_models(self, provider: LLMProvider) -> List[str]:
        """Get list of supported models for a provider"""
        models = {
            LLMProvider.OPENAI: [
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-3.5-turbo",
                "gpt-4-32k"
            ],
            LLMProvider.ANTHROPIC: [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229", 
                "claude-3-haiku-20240307",
                "claude-2.1"
            ],
            LLMProvider.GOOGLE: [
                "gemini-pro",
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ],
            LLMProvider.MOCK: ["fake-list-llm"]
        }
        
        return models.get(provider, [])