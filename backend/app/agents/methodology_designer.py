"""Methodology Designer Agent - Designs experimental approaches"""

from typing import List, Dict, Any
from app.agents.base import BaseAgent
from app.state import ResearchState, Methodology, WorkflowStatus
from app.agents.prompts import format_prompt
from app.core.state_management import update_state_status, add_error
import json
import logging

logger = logging.getLogger(__name__)


class MethodologyDesignerAgent(BaseAgent):
    """Agent responsible for designing research methodologies"""
    
    def __init__(self, llm_client=None):
        """
        Initialize Methodology Designer
        
        Args:
            llm_client: LLM client for methodology design
        """
        super().__init__(
            name="methodology_designer",
            description="Designs experimental methodologies for hypotheses",
            llm_client=llm_client
        )
    
    async def process(self, state: ResearchState) -> ResearchState:
        """
        Design methodologies for generated hypotheses
        
        Args:
            state: Current research state with hypotheses
            
        Returns:
            Updated state with methodologies
        """
        self.log_start(state)
        
        try:
            # Validate input
            if not state.get("hypotheses"):
                raise ValueError("No hypotheses available for methodology design")
            
            # Update status (stays in GENERATING)
            state = update_state_status(
                state,
                WorkflowStatus.GENERATING,
                self.name
            )
            
            methodologies = []
            
            # Design methodology for each hypothesis
            for hypothesis_dict in state["hypotheses"][:3]:  # Limit to top 3 hypotheses
                methodology_prompt = format_prompt(
                    agent='methodology_designer',
                    prompt_name='design',
                    hypothesis=hypothesis_dict["content"]
                )
                
                methodology = await self._design_methodology(
                    hypothesis_dict,
                    methodology_prompt
                )
                
                methodologies.append(methodology)
            
            # Store in state
            state["methodologies"] = [m.dict() for m in methodologies]
            
            self.logger.info(f"Designed {len(state['methodologies'])} methodologies")
            
            self.log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Methodology design failed: {str(e)}"
            self.log_error(error_msg, state)
            state = add_error(state, error_msg)
            
            # Create basic methodology to continue
            if state.get("hypotheses"):
                fallback_methodology = Methodology(
                    hypothesis_id=state["hypotheses"][0]["id"],
                    approach="Standard experimental approach",
                    sample_size=30,
                    estimated_duration="6 months",
                    key_requirements=["Basic research infrastructure"]
                )
                state["methodologies"] = [fallback_methodology.dict()]
            else:
                state["methodologies"] = []
            
            return state
    
    async def _design_methodology(
        self,
        hypothesis: Dict,
        prompt: str
    ) -> Methodology:
        """
        Design methodology for a single hypothesis
        
        Args:
            hypothesis: Hypothesis dictionary
            prompt: Design prompt
            
        Returns:
            Methodology object
        """
        if self.llm_client:
            # Get methodology from LLM
            response = await self.llm_client.generate(prompt)
            
            # Parse response
            methodology = self._parse_methodology_response(
                response,
                hypothesis["id"]
            )
            
        else:
            # Mock methodology for testing
            self.logger.warning("No LLM client configured, generating mock methodology")
            
            methodology = Methodology(
                hypothesis_id=hypothesis["id"],
                approach="Randomized controlled trial with three treatment groups",
                sample_size=100,
                estimated_duration="12 months",
                key_requirements=[
                    "Research team with statistical expertise",
                    "Data collection infrastructure",
                    "IRB approval for human subjects",
                    "Computing resources for analysis"
                ]
            )
        
        return methodology
    
    def _parse_methodology_response(
        self,
        response: str,
        hypothesis_id: str
    ) -> Methodology:
        """
        Parse LLM response into Methodology object
        
        Args:
            response: LLM response
            hypothesis_id: ID of the hypothesis
            
        Returns:
            Methodology object
        """
        try:
            # If response is JSON
            if response.strip().startswith('{'):
                data = json.loads(response)
                
                return Methodology(
                    hypothesis_id=hypothesis_id,
                    approach=data.get("approach", ""),
                    sample_size=data.get("sample_size"),
                    estimated_duration=data.get("duration", data.get("timeline")),
                    key_requirements=data.get("requirements", data.get("resources", []))
                )
            
            # Parse text response
            methodology_data = {
                "hypothesis_id": hypothesis_id,
                "approach": "",
                "sample_size": None,
                "estimated_duration": None,
                "key_requirements": []
            }
            
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                line_lower = line.lower()
                
                if 'approach' in line_lower or 'method' in line_lower or 'design' in line_lower:
                    current_section = 'approach'
                    if ':' in line:
                        methodology_data['approach'] = line.split(':', 1)[1].strip()
                
                elif 'sample' in line_lower:
                    current_section = 'sample'
                    # Try to extract number
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        methodology_data['sample_size'] = int(numbers[0])
                
                elif 'duration' in line_lower or 'timeline' in line_lower or 'time' in line_lower:
                    current_section = 'duration'
                    if ':' in line:
                        methodology_data['estimated_duration'] = line.split(':', 1)[1].strip()
                
                elif 'requirement' in line_lower or 'resource' in line_lower or 'need' in line_lower:
                    current_section = 'requirements'
                
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    content = line.lstrip('-•* ').strip()
                    
                    if current_section == 'requirements':
                        methodology_data['key_requirements'].append(content)
                    elif current_section == 'approach' and not methodology_data['approach']:
                        methodology_data['approach'] = content
                
                elif current_section == 'approach' and not methodology_data['approach']:
                    methodology_data['approach'] = line
            
            # Ensure we have at least some content
            if not methodology_data['approach']:
                methodology_data['approach'] = "Experimental study design"
            
            if not methodology_data['key_requirements']:
                methodology_data['key_requirements'] = ["Standard research resources"]
            
            return Methodology(**methodology_data)
            
        except Exception as e:
            self.logger.error(f"Failed to parse methodology response: {e}")
            
            # Return basic methodology
            return Methodology(
                hypothesis_id=hypothesis_id,
                approach="Standard research approach",
                sample_size=50,
                estimated_duration="6-12 months",
                key_requirements=["Basic research infrastructure"]
            )