"""Validation Agent - Validates hypotheses and methodologies"""

from typing import List, Dict, Any
from app.agents.base import BaseAgent
from app.schemas import ResearchState, ValidationResult, WorkflowStatus
from app.agents.prompts import format_prompt
from app.core.state_management import update_state_status, add_error
import json
import logging

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """Agent responsible for validating research outputs"""
    
    def __init__(self, llm_client=None, strict_mode: bool = False):
        """
        Initialize Validation Agent
        
        Args:
            llm_client: LLM client for validation
            strict_mode: If True, apply stricter validation criteria
        """
        super().__init__(
            name="validation",
            description="Validates hypotheses and methodologies"
        )
        self.llm_client = llm_client
        self.strict_mode = strict_mode
    
    async def process(self, state: ResearchState) -> ResearchState:
        """
        Validate hypotheses and methodologies
        
        Args:
            state: Current research state
            
        Returns:
            Updated state with validation results
        """
        self.log_start(state)
        
        try:
            # Validate input
            if not state.get("hypotheses") or not state.get("methodologies"):
                raise ValueError("Missing hypotheses or methodologies for validation")
            
            # Update status
            state = update_state_status(
                state,
                WorkflowStatus.VALIDATING,
                self.name
            )
            
            validation_results = []
            
            # Validate each hypothesis-methodology pair
            for hypothesis_dict in state["hypotheses"]:
                # Find corresponding methodology
                methodology_dict = self._find_methodology(
                    hypothesis_dict["id"],
                    state["methodologies"]
                )
                
                if not methodology_dict:
                    self.logger.warning(f"No methodology found for hypothesis {hypothesis_dict['id']}")
                    continue
                
                # Prepare validation prompt
                evidence = self._gather_evidence(hypothesis_dict, state["papers"])
                
                validation_prompt = format_prompt(
                    agent='validation_agent',
                    prompt_name='validate',
                    hypothesis=hypothesis_dict["content"],
                    methodology=self._format_methodology(methodology_dict),
                    evidence=evidence
                )
                
                # Perform validation
                validation_result = await self._validate(
                    hypothesis_dict,
                    methodology_dict,
                    validation_prompt
                )
                
                validation_results.append(validation_result)
            
            # Store results
            state["validation_results"] = [v.dict() for v in validation_results]
            
            # Mark workflow as complete
            state["should_continue"] = False
            state = update_state_status(
                state,
                WorkflowStatus.COMPLETED,
                self.name
            )
            
            self.logger.info(
                f"Validation complete: {len(validation_results)} results, "
                f"{sum(1 for v in validation_results if v.is_valid)} valid"
            )
            
            self.log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            self.log_error(error_msg, state)
            state = add_error(state, error_msg)
            
            # Create minimal validation to complete workflow
            if state.get("hypotheses"):
                fallback_validation = ValidationResult(
                    hypothesis_id=state["hypotheses"][0]["id"],
                    is_valid=True,
                    confidence=0.3,
                    issues=["Validation incomplete"],
                    recommendations=["Manual review recommended"]
                )
                state["validation_results"] = [fallback_validation.dict()]
            
            state["should_continue"] = False
            return state
    
    def _find_methodology(
        self,
        hypothesis_id: str,
        methodologies: List[Dict]
    ) -> Dict:
        """Find methodology for a given hypothesis"""
        for methodology in methodologies:
            if methodology.get("hypothesis_id") == hypothesis_id:
                return methodology
        return None
    
    def _gather_evidence(
        self,
        hypothesis: Dict,
        papers: List[Dict]
    ) -> str:
        """Gather evidence from papers supporting the hypothesis"""
        supporting_paper_ids = hypothesis.get("supporting_papers", [])
        
        if not supporting_paper_ids:
            return "No specific supporting papers identified"
        
        evidence_parts = []
        
        for paper_id in supporting_paper_ids[:5]:  # Limit to 5 papers
            paper = self._find_paper_by_id(paper_id, papers)
            if paper:
                evidence_parts.append(
                    f"- {paper['title']} ({paper.get('year', 'n.d.')}): "
                    f"{paper['abstract'][:200]}..."
                )
        
        return "\n".join(evidence_parts) if evidence_parts else "Limited evidence available"
    
    def _find_paper_by_id(self, paper_id: str, papers: List[Dict]) -> Dict:
        """Find paper by ID"""
        for paper in papers:
            if paper.get("id") == paper_id:
                return paper
        return None
    
    def _format_methodology(self, methodology: Dict) -> str:
        """Format methodology for prompt"""
        parts = [
            f"Approach: {methodology.get('approach', 'Not specified')}",
            f"Sample Size: {methodology.get('sample_size', 'Not specified')}",
            f"Duration: {methodology.get('estimated_duration', 'Not specified')}",
            f"Requirements: {', '.join(methodology.get('key_requirements', ['Not specified']))}"
        ]
        return "\n".join(parts)
    
    async def _validate(
        self,
        hypothesis: Dict,
        methodology: Dict,
        prompt: str
    ) -> ValidationResult:
        """
        Perform validation using LLM
        
        Args:
            hypothesis: Hypothesis to validate
            methodology: Methodology to validate
            prompt: Validation prompt
            
        Returns:
            ValidationResult object
        """
        if self.llm_client:
            # Get validation from LLM
            response = await self.llm_client.generate(prompt)
            
            # Parse response
            validation = self._parse_validation_response(
                response,
                hypothesis["id"]
            )
            
        else:
            # Mock validation for testing
            self.logger.warning("No LLM client configured, generating mock validation")
            
            # Apply different validation based on confidence score
            confidence = hypothesis.get("confidence_score", 0.5)
            
            if confidence > 0.7:
                validation = ValidationResult(
                    hypothesis_id=hypothesis["id"],
                    is_valid=True,
                    confidence=0.8,
                    issues=[
                        "Sample size may need adjustment based on power analysis"
                    ],
                    recommendations=[
                        "Consider pilot study first",
                        "Ensure proper control groups",
                        "Plan for interim analysis"
                    ]
                )
            else:
                validation = ValidationResult(
                    hypothesis_id=hypothesis["id"],
                    is_valid=True if confidence > 0.5 else False,
                    confidence=confidence,
                    issues=[
                        "Limited supporting evidence",
                        "Methodology may be too ambitious"
                    ],
                    recommendations=[
                        "Gather more preliminary data",
                        "Consider simpler initial approach",
                        "Review similar studies for best practices"
                    ]
                )
        
        # Apply strict mode if enabled
        if self.strict_mode and validation.confidence < 0.7:
            validation.is_valid = False
            validation.issues.append("Does not meet strict validation criteria")
        
        return validation
    
    def _parse_validation_response(
        self,
        response: str,
        hypothesis_id: str
    ) -> ValidationResult:
        """
        Parse LLM response into ValidationResult
        
        Args:
            response: LLM response
            hypothesis_id: ID of validated hypothesis
            
        Returns:
            ValidationResult object
        """
        try:
            # If response is JSON
            if response.strip().startswith('{'):
                data = json.loads(response)
                
                return ValidationResult(
                    hypothesis_id=hypothesis_id,
                    is_valid=data.get("is_valid", data.get("valid", False)),
                    confidence=float(data.get("confidence", 0.5)),
                    issues=data.get("issues", []),
                    recommendations=data.get("recommendations", [])
                )
            
            # Parse text response
            validation_data = {
                "hypothesis_id": hypothesis_id,
                "is_valid": False,
                "confidence": 0.5,
                "issues": [],
                "recommendations": []
            }
            
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                line_lower = line.lower()
                
                # Check for validity
                if 'valid' in line_lower:
                    if 'invalid' in line_lower or 'not valid' in line_lower:
                        validation_data['is_valid'] = False
                    elif 'is valid' in line_lower or 'valid:' in line_lower:
                        validation_data['is_valid'] = True
                
                # Check for confidence
                if 'confidence' in line_lower:
                    import re
                    numbers = re.findall(r'[\d.]+', line)
                    if numbers:
                        conf = float(numbers[0])
                        validation_data['confidence'] = conf / 100 if conf > 1 else conf
                
                # Identify sections
                if 'issue' in line_lower or 'problem' in line_lower or 'concern' in line_lower:
                    current_section = 'issues'
                elif 'recommend' in line_lower or 'suggest' in line_lower:
                    current_section = 'recommendations'
                
                # Parse list items
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    content = line.lstrip('-•* ').strip()
                    
                    if current_section == 'issues':
                        validation_data['issues'].append(content)
                    elif current_section == 'recommendations':
                        validation_data['recommendations'].append(content)
            
            # Ensure we have some content
            if not validation_data['issues']:
                validation_data['issues'] = ["Validation completed"]
            
            if not validation_data['recommendations']:
                validation_data['recommendations'] = ["Proceed with caution"]
            
            return ValidationResult(**validation_data)
            
        except Exception as e:
            self.logger.error(f"Failed to parse validation response: {e}")
            
            # Return basic validation
            return ValidationResult(
                hypothesis_id=hypothesis_id,
                is_valid=True,
                confidence=0.5,
                issues=["Unable to fully parse validation"],
                recommendations=["Manual review recommended"]
            )