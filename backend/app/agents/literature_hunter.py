"""Literature Hunter Agent - Searches for relevant academic papers"""

import json
from typing import List, Dict, Any
from app.agents.base import BaseAgent
from app.state import ResearchState, Paper, WorkflowStatus
from app.agents.prompts import format_prompt
from app.core.state_management import update_state_status, add_error
import logging

logger = logging.getLogger(__name__)


class LiteratureHunterAgent(BaseAgent):
    """Agent responsible for searching and retrieving academic papers"""
    
    def __init__(self, llm_client=None, search_client=None):
        """
        Initialize Literature Hunter
        
        Args:
            search_client: Client for searching paper databases
        """
        super().__init__(
            name="literature_hunter",
            description="Searches multiple databases for relevant papers",
            llm_client=llm_client
        )
        self.search_client = search_client
    
    async def process(self, state: ResearchState) -> ResearchState:
        """
        Search for papers based on the research query
        
        Args:
            state: Current research state
            
        Returns:
            Updated state with papers
        """
        self.log_start(state)
        
        try:
            # Update status
            state = update_state_status(
                state, 
                WorkflowStatus.SEARCHING,
                self.name
            )
            
            # Get search prompt
            search_prompt = format_prompt(
                agent='literature_hunter',
                prompt_name='search',
                query=state["query"],
                max_papers=state["max_papers"]
            )
            
            # Search for papers (implement based on your search service)
            papers = await self._search_papers(
                query=search_prompt,
                max_results=state["max_papers"]
            )
            
            # If insufficient papers, try expanded search
            if len(papers) < 5:
                self.logger.info(f"Only found {len(papers)} papers, expanding search")
                
                expand_prompt = format_prompt(
                    agent='literature_hunter',
                    prompt_name='expand_search',
                    original_query=state["query"],
                    paper_count=len(papers),
                    min_papers=5
                )
                
                # Get expanded queries from LLM
                expanded_queries = await self._get_expanded_queries(expand_prompt)
                
                # Search with expanded queries
                for expanded_query in expanded_queries[:3]:  # Limit to 3 expansions
                    additional_papers = await self._search_papers(
                        query=expanded_query,
                        max_results=state["max_papers"] // 3
                    )
                    papers.extend(additional_papers)
                    
                    if len(papers) >= state["max_papers"]:
                        break
            
            # Deduplicate papers by title
            unique_papers = self._deduplicate_papers(papers)
            
            # Score and rank papers by relevance
            scored_papers = await self._score_relevance(unique_papers, state["query"])
            
            # Take top papers up to max_papers limit
            final_papers = scored_papers[:state["max_papers"]]
            
            # Convert to dict for state storage
            state["papers"] = [paper.dict() for paper in final_papers]
            
            self.logger.info(f"Found {len(state['papers'])} relevant papers")
            self.log_complete(state)
            
            return state
            
        except Exception as e:
            error_msg = f"Literature search failed: {str(e)}"
            self.log_error(error_msg, state)
            state = add_error(state, error_msg)
            state["should_continue"] = False
            return state
    
    async def _search_papers(self, query: str, max_results: int) -> List[Paper]:
        """
        Execute paper search
        
        This is a placeholder - implement based on your search service
        (e.g., arxiv API, PubMed API, Semantic Scholar API)
        """
        # Example implementation
        papers = []
        
        if self.search_client:
            # Use actual search client
            results = await self.search_client.search(
                query=query,
                limit=max_results
            )
            
            for result in results:
                paper = Paper(
                    title=result.get("title", ""),
                    abstract=result.get("abstract", ""),
                    authors=result.get("authors", []),
                    year=result.get("year"),
                    doi=result.get("doi"),
                    url=result.get("url"),
                    relevance_score=0.0  # Will be scored later
                )
                papers.append(paper)
        else:
            # Mock implementation for testing
            self.logger.warning("No search client configured, returning mock data")
            for i in range(min(3, max_results)):
                paper = Paper(
                    title=f"Paper about {query} - {i+1}",
                    abstract=f"This paper explores {query} in detail...",
                    authors=["Author A", "Author B"],
                    year=2024,
                    relevance_score=0.8 - (i * 0.1)
                )
                papers.append(paper)
        
        return papers
    
    async def _get_expanded_queries(self, prompt: str) -> List[str]:
        """
        Get expanded search queries using LLM
        
        Args:
            prompt: Expansion prompt
            
        Returns:
            List of expanded queries
        """
        if self.llm_client:
            response = await self.llm_client.generate(prompt)
            # Parse response to extract queries
            # Assuming response contains newline-separated queries
            queries = [q.strip() for q in response.split('\n') if q.strip()]
            return queries
        else:
            # Fallback expansion
            return [
                f"{prompt} machine learning",
                f"{prompt} deep learning",
                f"{prompt} artificial intelligence"
            ]
    
    async def _score_relevance(self, papers: List[Paper], query: str) -> List[Paper]:
        """
        Score papers by relevance to query
        
        Args:
            papers: List of papers to score
            query: Original research query
            
        Returns:
            Papers sorted by relevance score
        """
        if self.llm_client:
            # Use LLM to score relevance
            for paper in papers:
                score_prompt = f"""
                Rate the relevance of this paper to the query: "{query}"
                Title: {paper.title}
                Abstract: {paper.abstract[:500]}
                
                Provide a score from 0 to 1.
                """
                
                try:
                    score_response = await self.llm_client.generate(score_prompt)
                    paper.relevance_score = float(score_response.strip())
                except:
                    paper.relevance_score = 0.5
        else:
            # Simple keyword-based scoring
            query_words = set(query.lower().split())
            for paper in papers:
                title_words = set(paper.title.lower().split())
                abstract_words = set(paper.abstract.lower().split())
                
                title_overlap = len(query_words & title_words) / len(query_words)
                abstract_overlap = len(query_words & abstract_words) / len(query_words)
                
                paper.relevance_score = (title_overlap * 0.7 + abstract_overlap * 0.3)
        
        # Sort by relevance score
        return sorted(papers, key=lambda p: p.relevance_score, reverse=True)
    
    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers based on title"""
        seen_titles = set()
        unique_papers = []
        
        for paper in papers:
            title_lower = paper.title.lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_papers.append(paper)
        
        return unique_papers