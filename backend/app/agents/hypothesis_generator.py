"""Hypothesis Generator Agent - Creates novel research hypotheses"""

from typing import List, Dict, Any
from app.agents.base import BaseAgent
from app.state import ResearchState, Hypothesis, WorkflowStatus
from app.agents.prompts import format_prompt
from app.core.state_management import update_state_status, add_error
import json
import logging

logger = logging.getLogger(__name__)


class HypothesisGeneratorAgent(BaseAgent):
    """Agent responsible for generating novel hypotheses"""
    
    def __init__(self, llm_client=None, creativity_temperature: float = 0.7):
        """
        Initialize Hypothesis Generator
        
        Args:
            llm_client: LLM client for generation
            creativity_temperature: Temperature for creative generation (0-1)
        """
        super().__init__(
            name="hypothesis_generator",
            description="Generates novel research hypotheses",
            llm_client=llm_client
        )
        self.creativity_temperature = creativity_temperature
    
    async def process(self, state: ResearchState) -> ResearchState:
        """
        Generate hypotheses based on synthesis
        
        Args:
            state: Current research state with synthesis
            
        Returns:
            Updated state with hypotheses
        """
        self.log_start(state)
        
        try:
            # Validate input
            if not state.get("synthesis"):
                raise ValueError("No synthesis available for hypothesis generation")
            
            # Update status
            state = update_state_status(
                state,
                WorkflowStatus.GENERATING,
                self.name
            )
            
            # Prepare synthesis summary
            synthesis_summary = self._prepare_synthesis_summary(state["synthesis"])
            
            # Determine number of hypotheses to generate
            num_hypotheses = min(5, max(3, len(state["synthesis"].get("research_gaps", []))))
            
            # Get generation prompt
            generation_prompt = format_prompt(
                agent='hypothesis_generator',
                prompt_name='generate',
                synthesis=synthesis_summary,
                num_hypotheses=num_hypotheses
            )
            
            # Generate hypotheses
            hypotheses = await self._generate_hypotheses(
                generation_prompt,
                state["synthesis"],
                state["papers"]
            )
            
            # Filter high-quality hypotheses
            quality_hypotheses = self._filter_hypotheses(hypotheses)
            
            # Store in state
            state["hypotheses"] = [h.model_dump() for h in quality_hypotheses]

            self.logger.info(f"Generated {len(state['hypotheses'])} hypotheses")
            
            self.log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Hypothesis generation failed: {str(e)}"
            self.log_error(error_msg, state)
            state = add_error(state, error_msg)
            
            # Generate at least one basic hypothesis to continue
            fallback_hypothesis = Hypothesis(
                content="Further investigation needed based on synthesis",
                confidence_score=0.3,
                supporting_papers=[],
                reasoning="Fallback hypothesis due to generation failure"
            )
            state["hypotheses"] = [fallback_hypothesis.dict()]
            
            return state
    
    def _prepare_synthesis_summary(self, synthesis: Dict) -> str:
        """
        Prepare synthesis summary for hypothesis generation
        
        Args:
            synthesis: Synthesis dictionary
            
        Returns:
            Formatted summary string
        """
        summary_parts = []
        
        # Add patterns
        patterns = synthesis.get("patterns", [])
        if patterns:
            summary_parts.append("Key Patterns Identified:")
            for pattern in patterns[:5]:  # Limit to top 5
                summary_parts.append(f"- {pattern['description']} (confidence: {pattern['confidence']})")
        
        # Add key findings
        findings = synthesis.get("key_findings", [])
        if findings:
            summary_parts.append("\nKey Findings:")
            for finding in findings[:5]:
                summary_parts.append(f"- {finding}")
        
        # Add research gaps
        gaps = synthesis.get("research_gaps", [])
        if gaps:
            summary_parts.append("\nResearch Gaps:")
            for gap in gaps[:5]:
                summary_parts.append(f"- {gap}")
        
        return "\n".join(summary_parts)
    
    async def _generate_hypotheses(
        self,
        prompt: str,
        synthesis: Dict,
        papers: List[Dict]
    ) -> List[Hypothesis]:
        """
        Generate hypotheses using LLM
        
        Args:
            prompt: Generation prompt
            synthesis: Synthesis data
            papers: Papers data
            
        Returns:
            List of generated hypotheses
        """
        if self.llm_client:
            # Generate with LLM
            response = await self.llm_client.generate(
                prompt,
                temperature=self.creativity_temperature
            )
            
            # Parse response into hypotheses
            hypotheses = self._parse_hypothesis_response(response, papers)
            
        else:
            # Mock hypotheses for testing
            self.logger.warning("No LLM client configured, generating mock hypotheses")
            
            hypotheses = [
                Hypothesis(
                    content="Combining approaches from papers 1 and 3 could yield improved results",
                    confidence_score=0.75,
                    supporting_papers=[papers[0]["id"], papers[2]["id"]] if len(papers) > 2 else [],
                    reasoning="Synthesis shows complementary methods that haven't been combined"
                ),
                Hypothesis(
                    content="The gap identified in reproducibility could be addressed through standardized protocols",
                    confidence_score=0.65,
                    supporting_papers=[papers[1]["id"]] if len(papers) > 1 else [],
                    reasoning="Multiple papers highlight reproducibility issues without proposing solutions"
                ),
                Hypothesis(
                    content="Cross-domain application of the main finding could open new research areas",
                    confidence_score=0.60,
                    supporting_papers=[p["id"] for p in papers[:3]],
                    reasoning="The patterns suggest broader applicability than currently explored"
                )
            ]
        
        return hypotheses
    
    def _parse_hypothesis_response(
        self,
        response: str,
        papers: List[Dict]
    ) -> List[Hypothesis]:
        """
        Parse LLM response into Hypothesis objects
        
        Args:
            response: LLM response
            papers: Available papers for reference
            
        Returns:
            List of Hypothesis objects
        """
        hypotheses = []
        
        try:
            # If response is JSON
            if response.strip().startswith('[') or response.strip().startswith('{'):
                data = json.loads(response)
                
                if isinstance(data, dict):
                    data = data.get("hypotheses", [data])
                elif not isinstance(data, list):
                    data = [data]
                
                for item in data:
                    hypothesis = Hypothesis(
                        content=item.get("content", item.get("hypothesis", "")),
                        confidence_score=float(item.get("confidence", 0.5)),
                        supporting_papers=item.get("supporting_papers", []),
                        reasoning=item.get("reasoning", "")
                    )
                    hypotheses.append(hypothesis)
            
            else:
                # Parse text response
                # Simple parser - enhance based on your LLM output
                current_hypothesis = {}
                
                for line in response.split('\n'):
                    line = line.strip()
                    
                    if line.startswith('Hypothesis:') or line.startswith('H:'):
                        if current_hypothesis:
                            hypotheses.append(self._create_hypothesis_from_dict(
                                current_hypothesis, papers
                            ))
                        current_hypothesis = {'content': line.split(':', 1)[1].strip()}
                    
                    elif line.startswith('Reasoning:') or line.startswith('R:'):
                        current_hypothesis['reasoning'] = line.split(':', 1)[1].strip()
                    
                    elif line.startswith('Confidence:') or line.startswith('C:'):
                        try:
                            conf = line.split(':', 1)[1].strip()
                            # Extract number from string like "0.7" or "70%"
                            conf = conf.replace('%', '')
                            conf_value = float(conf) / 100 if float(conf) > 1 else float(conf)
                            current_hypothesis['confidence'] = conf_value
                        except:
                            current_hypothesis['confidence'] = 0.5
                    
                    elif line.startswith('Papers:') or line.startswith('P:'):
                        # Extract paper references
                        paper_refs = line.split(':', 1)[1].strip()
                        current_hypothesis['papers'] = self._extract_paper_ids(paper_refs, papers)
                
                # Add last hypothesis
                if current_hypothesis:
                    hypotheses.append(self._create_hypothesis_from_dict(
                        current_hypothesis, papers
                    ))
            
        except Exception as e:
            self.logger.error(f"Failed to parse hypothesis response: {e}")
            
            # Create a single hypothesis from the response
            hypotheses.append(Hypothesis(
                content=response[:500] if len(response) > 500 else response,
                confidence_score=0.5,
                supporting_papers=[papers[0]["id"]] if papers else [],
                reasoning="Parsed from response"
            ))
        
        return hypotheses
    
    def _create_hypothesis_from_dict(
        self,
        data: Dict,
        papers: List[Dict]
    ) -> Hypothesis:
        """Create Hypothesis object from parsed data"""
        return Hypothesis(
            content=data.get('content', 'Hypothesis'),
            confidence_score=data.get('confidence', 0.5),
            supporting_papers=data.get('papers', [papers[0]["id"]] if papers else []),
            reasoning=data.get('reasoning', 'Generated from synthesis')
        )
    
    def _extract_paper_ids(self, paper_refs: str, papers: List[Dict]) -> List[str]:
        """Extract paper IDs from reference string"""
        paper_ids = []
        
        # Try to extract numbers from string
        import re
        numbers = re.findall(r'\d+', paper_refs)
        
        for num in numbers:
            idx = int(num) - 1  # Assuming 1-indexed references
            if 0 <= idx < len(papers):
                paper_ids.append(papers[idx]["id"])
        
        return paper_ids if paper_ids else [papers[0]["id"]] if papers else []
    
    def _filter_hypotheses(self, hypotheses: List[Hypothesis]) -> List[Hypothesis]:
        """
        Filter hypotheses by quality criteria
        
        Args:
            hypotheses: List of generated hypotheses
            
        Returns:
            Filtered list of high-quality hypotheses
        """
        # Filter by confidence score
        quality_hypotheses = [
            h for h in hypotheses
            if h.confidence_score >= 0.4  # Minimum confidence threshold
        ]
        
        # Sort by confidence
        quality_hypotheses.sort(key=lambda h: h.confidence_score, reverse=True)
        
        # Return top 5
        return quality_hypotheses[:5]