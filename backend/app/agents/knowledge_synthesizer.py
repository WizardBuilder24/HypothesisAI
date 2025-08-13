"""Knowledge Synthesizer Agent - Identifies patterns and synthesizes findings"""

from typing import List, Dict, Any
from app.agents.base import BaseAgent
from app.schemas import ResearchState, Pattern, Synthesis, WorkflowStatus
from app.agents.prompts import format_prompt
from app.core.state_management import update_state_status, add_error
import json
import logging

logger = logging.getLogger(__name__)


class KnowledgeSynthesizerAgent(BaseAgent):
    """Agent responsible for synthesizing patterns from papers"""
    
    def __init__(self, llm_client=None):
        """
        Initialize Knowledge Synthesizer
        
        Args:
            llm_client: LLM client for synthesis
        """
        super().__init__(
            name="knowledge_synthesizer",
            description="Synthesizes patterns and findings from papers"
        )
        self.llm_client = llm_client
    
    async def process(self, state: ResearchState) -> ResearchState:
        """
        Synthesize patterns from collected papers
        
        Args:
            state: Current research state with papers
            
        Returns:
            Updated state with synthesis
        """
        self.log_start(state)
        
        try:
            # Validate input
            if not state["papers"]:
                raise ValueError("No papers available for synthesis")
            
            # Update status
            state = update_state_status(
                state,
                WorkflowStatus.SYNTHESIZING,
                self.name
            )
            
            # Prepare papers summary for prompt
            papers_summary = self._prepare_papers_summary(state["papers"])
            
            # Get synthesis prompt
            synthesis_prompt = format_prompt(
                agent='knowledge_synthesizer',
                prompt_name='synthesis',
                num_papers=len(state["papers"]),
                papers_summary=papers_summary
            )
            
            # Perform synthesis
            synthesis_result = await self._synthesize_papers(
                synthesis_prompt,
                state["papers"]
            )
            
            # Store synthesis in state
            state["synthesis"] = synthesis_result.model_dump()
            
            self.logger.info(
                f"Synthesis complete: {len(synthesis_result.patterns)} patterns, "
                f"{len(synthesis_result.key_findings)} findings, "
                f"{len(synthesis_result.research_gaps)} gaps"
            )
            
            self.log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Synthesis failed: {str(e)}"
            self.log_error(error_msg, state)
            state = add_error(state, error_msg)
            
            # Create minimal synthesis to allow workflow to continue
            state["synthesis"] = Synthesis(
                patterns=[],
                key_findings=["Synthesis failed - using papers as-is"],
                research_gaps=["Unable to identify gaps"],
                total_papers_analyzed=len(state.get("papers", []))
            ).dict()
            
            return state
    
    def _prepare_papers_summary(self, papers: List[Dict]) -> str:
        """
        Prepare a summary of papers for the synthesis prompt
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Formatted summary string
        """
        summary_lines = []
        
        for i, paper in enumerate(papers[:20], 1):  # Limit to 20 papers for prompt
            summary_lines.append(
                f"Paper {i} (ID: {paper.get('id', i)}):\n"
                f"Title: {paper['title']}\n"
                f"Year: {paper.get('year', 'Unknown')}\n"
                f"Abstract: {paper['abstract'][:300]}...\n"
            )
        
        if len(papers) > 20:
            summary_lines.append(f"\n... and {len(papers) - 20} more papers")
        
        return "\n".join(summary_lines)
    
    async def _synthesize_papers(
        self, 
        prompt: str, 
        papers: List[Dict]
    ) -> Synthesis:
        """
        Perform synthesis using LLM
        
        Args:
            prompt: Synthesis prompt
            papers: List of papers to synthesize
            
        Returns:
            Synthesis object
        """
        if self.llm_client:
            # Get synthesis from LLM
            response = await self.llm_client.generate(prompt)
            
            # Parse LLM response into Synthesis object
            synthesis = self._parse_synthesis_response(response, papers)
            
        else:
            # Mock synthesis for testing
            self.logger.warning("No LLM client configured, generating mock synthesis")
            
            synthesis = Synthesis(
                patterns=[
                    Pattern(
                        description="Common use of deep learning methods",
                        paper_ids=[p["id"] for p in papers[:5]],
                        confidence=0.8
                    ),
                    Pattern(
                        description="Focus on reproducibility challenges",
                        paper_ids=[p["id"] for p in papers[2:7]],
                        confidence=0.7
                    ),
                    Pattern(
                        description="Emerging trend in federated approaches",
                        paper_ids=[p["id"] for p in papers[5:10]],
                        confidence=0.6
                    )
                ],
                key_findings=[
                    "Deep learning consistently outperforms traditional methods",
                    "Data quality is more important than model complexity",
                    "Interdisciplinary approaches show promise",
                    "Reproducibility remains a major challenge",
                    "Real-world deployment faces scalability issues"
                ],
                research_gaps=[
                    "Limited work on explainability in production systems",
                    "Insufficient studies on long-term performance",
                    "Need for standardized evaluation metrics"
                ],
                total_papers_analyzed=len(papers)
            )
        
        return synthesis
    
    def _parse_synthesis_response(self, response: str, papers: List[Dict]) -> Synthesis:
        """
        Parse LLM response into Synthesis object
        
        This is a simplified parser - adjust based on your LLM's output format
        """
        try:
            # If LLM returns JSON
            if response.strip().startswith('{'):
                data = json.loads(response)
                
                patterns = [
                    Pattern(
                        description=p.get("description", ""),
                        paper_ids=p.get("paper_ids", []),
                        confidence=p.get("confidence", 0.5)
                    )
                    for p in data.get("patterns", [])
                ]
                
                return Synthesis(
                    patterns=patterns,
                    key_findings=data.get("key_findings", []),
                    research_gaps=data.get("research_gaps", []),
                    total_papers_analyzed=len(papers)
                )
            
            # Otherwise, parse text response
            # This is a simplified text parser - enhance as needed
            lines = response.split('\n')
            
            patterns = []
            key_findings = []
            research_gaps = []
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if 'pattern' in line.lower():
                    current_section = 'patterns'
                elif 'finding' in line.lower():
                    current_section = 'findings'
                elif 'gap' in line.lower():
                    current_section = 'gaps'
                elif line.startswith('-') or line.startswith('•'):
                    content = line.lstrip('-•').strip()
                    
                    if current_section == 'patterns':
                        patterns.append(Pattern(
                            description=content,
                            paper_ids=[p["id"] for p in papers[:3]],  # Simplified
                            confidence=0.7
                        ))
                    elif current_section == 'findings':
                        key_findings.append(content)
                    elif current_section == 'gaps':
                        research_gaps.append(content)
            
            return Synthesis(
                patterns=patterns or [Pattern(
                    description="General pattern identified",
                    paper_ids=[papers[0]["id"]],
                    confidence=0.5
                )],
                key_findings=key_findings or ["Key findings extracted from papers"],
                research_gaps=research_gaps or ["Research gaps identified"],
                total_papers_analyzed=len(papers)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse synthesis response: {e}")
            
            # Return minimal valid synthesis
            return Synthesis(
                patterns=[Pattern(
                    description="Analysis completed",
                    paper_ids=[p["id"] for p in papers[:3]],
                    confidence=0.5
                )],
                key_findings=["Analysis of papers completed"],
                research_gaps=["Further research needed"],
                total_papers_analyzed=len(papers)
            )