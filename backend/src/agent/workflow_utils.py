"""
Core utilities for HypothesisAI research workflow.
Provides common functionality used across multiple nodes.
"""

import os
import time
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from agent.configuration import ResearchWorkflowConfiguration
from agent.state import ResearchState
from agent.tools.preprint_apis import ArxivAPI, Paper as PreprintPaper


class WorkflowLogger:
    """Handles logging of workflow stages for debugging and transparency."""
    
    @staticmethod
    def record_stage(
        state: ResearchState, 
        agent_name: str, 
        prompt: str, 
        response: Any,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a workflow stage with error handling."""
        try:
            if "stages" not in state:
                state["stages"] = []
            
            stage_data = {
                "agent": agent_name,
                "prompt": prompt,
                "response": response.model_dump() if hasattr(response, 'model_dump') else str(response),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            if additional_data:
                stage_data.update(additional_data)
            
            state["stages"].append(stage_data)
        except Exception:
            # Non-critical: don't fail workflow if recording stages fails
            pass


class LLMProvider:
    """Factory for creating LLM instances based on configuration."""
    
    @staticmethod
    def create_llm(configurable: ResearchWorkflowConfiguration, temperature: float = 0.7):
        """Create the appropriate LLM based on configuration."""
        provider = configurable.llm_provider.lower()
        
        llm_factories = {
            "openai": lambda: ChatOpenAI(
                model=configurable.llm_model,
                temperature=temperature,
                api_key=os.getenv("OPENAI_API_KEY"),
            ),
            "anthropic": lambda: ChatAnthropic(
                model=configurable.llm_model,
                temperature=temperature,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            ),
            "google": lambda: ChatGoogleGenerativeAI(
                model=configurable.llm_model,
                temperature=temperature,
                api_key=os.getenv("GEMINI_API_KEY"),
            ),
        }
        
        factory = llm_factories.get(provider, llm_factories["google"])
        return factory()


class PaperSearcher:
    """Handles arXiv paper searching with async/sync compatibility."""
    
    @staticmethod
    async def search_papers_async(query: str, max_results: int) -> List[PreprintPaper]:
        """Perform async paper search."""
        async with ArxivAPI() as arxiv_api:
            return await arxiv_api.search(query, max_results=max_results)
    
    @staticmethod
    def search_papers_sync(query: str, max_results: int) -> List[PreprintPaper]:
        """Perform sync paper search with proper async handling."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Run in thread pool if already in event loop
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        PaperSearcher.search_papers_async(query, max_results)
                    )
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(
                    PaperSearcher.search_papers_async(query, max_results)
                )
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(PaperSearcher.search_papers_async(query, max_results))


class PaperProcessor:
    """Handles paper processing, deduplication, and ranking."""
    
    @staticmethod
    def deduplicate_papers(papers: List[PreprintPaper]) -> List[PreprintPaper]:
        """Remove duplicate papers based on ID."""
        seen_ids = set()
        unique_papers = []
        
        for paper in papers:
            if paper.id not in seen_ids:
                seen_ids.add(paper.id)
                unique_papers.append(paper)
        
        return unique_papers
    
    @staticmethod
    def calculate_paper_score(paper_dict: Dict[str, Any]) -> float:
        """Calculate combined score for paper ranking."""
        base_score = (
            paper_dict.get("relevance_score", 0.5) + 
            paper_dict.get("quality_score", 0.5)
        ) / 2
        
        # Add recency boost for papers from last 2 years
        try:
            pub_date = datetime.fromisoformat(
                paper_dict["date_published"].replace("Z", "+00:00")
            )
            days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
            if days_old < 730:  # 2 years
                recency_boost = 0.1 * (1 - days_old / 730)
                base_score += recency_boost
        except Exception:
            pass  # Use base score if date parsing fails
            
        return base_score
    
    @staticmethod
    def convert_papers_to_dict(papers: List[PreprintPaper]) -> List[Dict[str, Any]]:
        """Convert PreprintPaper objects to dict format for state storage."""
        paper_dicts = []
        
        for paper in papers:
            paper_dict = {
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "authors": paper.authors,
                "date_published": paper.date_published.isoformat(),
                "source": paper.source,
                "url": paper.url,
                "categories": paper.categories,
                "doi": paper.doi,
                "citations": paper.citations,
                "version": paper.version,
                "pdf_url": paper.pdf_url,
                "relevance_score": paper.relevance_score,
                "quality_score": paper.quality_score,
                "metadata": paper.metadata
            }
            paper_dicts.append(paper_dict)
        
        return paper_dicts
    
    @staticmethod
    def rank_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank papers by combined relevance, quality, and recency."""
        return sorted(papers, key=PaperProcessor.calculate_paper_score, reverse=True)


class RateLimiter:
    """Handles rate limiting for API calls."""
    
    @staticmethod
    def apply_rate_limit(delay_seconds: float = 2.5) -> None:
        """Apply rate limiting delay."""
        time.sleep(delay_seconds)
    
    @staticmethod
    def apply_search_delay(delay_seconds: float = 1.0) -> None:
        """Apply delay between search operations."""
        time.sleep(delay_seconds)


class StateValidator:
    """Validates and safely accesses state data."""
    
    @staticmethod
    def get_query(state: ResearchState) -> str:
        """Safely get query from state."""
        return state.get("query", "")
    
    @staticmethod
    def get_max_papers(state: ResearchState) -> int:
        """Safely get max papers setting from state."""
        return state.get("max_papers", 20)
    
    @staticmethod
    def get_papers(state: ResearchState) -> List[Dict[str, Any]]:
        """Safely get papers from state."""
        return state.get("papers", [])
    
    @staticmethod
    def get_synthesis(state: ResearchState) -> Optional[Dict[str, Any]]:
        """Safely get synthesis from state."""
        return state.get("synthesis")
    
    @staticmethod
    def get_hypotheses(state: ResearchState) -> List[Dict[str, Any]]:
        """Safely get hypotheses from state."""
        return state.get("hypotheses", [])
    
    @staticmethod
    def get_validation_results(state: ResearchState) -> List[Dict[str, Any]]:
        """Safely get validation results from state."""
        return state.get("validation_results", [])
    
    @staticmethod
    def get_errors(state: ResearchState) -> List[str]:
        """Safely get errors from state."""
        return state.get("errors", [])
    
    @staticmethod
    def get_iteration(state: ResearchState) -> int:
        """Safely get iteration count from state."""
        return state.get("iteration", 0)
    
    @staticmethod
    def get_stages(state: ResearchState) -> List[Dict[str, Any]]:
        """Safely get workflow stages from state."""
        return state.get("stages", [])
    
    @staticmethod
    def get_messages(state: ResearchState) -> List[Any]:
        """Safely get messages from state."""
        return state.get("messages", [])


class MessageBuilder:
    """Builds standardized messages for workflow communication."""
    
    @staticmethod
    def build_search_complete_message(
        paper_count: int, 
        strategy_count: int, 
        strategy_summary: str
    ) -> AIMessage:
        """Build message for completed literature search."""
        return AIMessage(
            content=f"Found {paper_count} relevant papers using {strategy_count} "
                   f"search strategies: {strategy_summary}"
        )
    
    @staticmethod
    def build_synthesis_complete_message(pattern_count: int, gap_count: int) -> AIMessage:
        """Build message for completed synthesis."""
        return AIMessage(
            content=f"Identified {pattern_count} patterns and {gap_count} research gaps"
        )
    
    @staticmethod
    def build_hypothesis_complete_message(hypothesis_count: int) -> AIMessage:
        """Build message for completed hypothesis generation."""
        return AIMessage(
            content=f"Generated {hypothesis_count} research hypotheses"
        )
    
    @staticmethod
    def build_validation_complete_message(valid_count: int, total_count: int) -> AIMessage:
        """Build message for completed validation."""
        return AIMessage(
            content=f"Validation complete: {valid_count}/{total_count} hypotheses validated"
        )
