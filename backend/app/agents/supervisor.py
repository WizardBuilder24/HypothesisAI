"""
Supervisor Agent - The orchestration brain of the research workflow
Makes intelligent routing decisions based on workflow state
"""

from typing import Optional, Dict, Any, List
from app.agents.base import BaseAgent
from app.state import (
    ResearchState, 
    AgentType, 
    WorkflowStatus, 
    SupervisorDecision
)
from app.core.state_management import update_state_status, add_error
from app.agents.prompts import format_prompt
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that orchestrates the workflow by making routing decisions
    """
    
    def __init__(self, llm_client=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Supervisor Agent
        
        Args:
            llm_client: Optional LLM client for complex decisions
            config: Configuration including thresholds and retry limits
        """
        super().__init__(
            name="supervisor",
            description="Orchestrates workflow and makes routing decisions",
            llm_client=llm_client
        )
        
        # Configuration with defaults
        self.config = config or {}
        self.max_retries = self.config.get('max_retries', {
            AgentType.LITERATURE_HUNTER: 3,
            AgentType.KNOWLEDGE_SYNTHESIZER: 2,
            AgentType.HYPOTHESIS_GENERATOR: 2,
            AgentType.METHODOLOGY_DESIGNER: 2,
            AgentType.VALIDATION: 1
        })
        
        self.quality_thresholds = self.config.get('quality_thresholds', {
            'min_papers': 5,
            'min_patterns': 2,
            'min_hypotheses': 1,
            'min_confidence': 0.5,
            'max_errors': 5
        })
        
        # Track retry attempts
        self.retry_counts = {}
    
    async def process(self, state: ResearchState) -> ResearchState:
        """
        Analyze state and determine next action
        
        Args:
            state: Current research state
            
        Returns:
            Updated state with routing decision
        """
        self.log_start(state)
        
        try:
            # Check for terminal conditions first
            if self._should_terminate(state):
                return self._handle_termination(state)
            
            # Check for error conditions
            if self._has_critical_errors(state):
                return self._handle_critical_errors(state)
            
            # Make routing decision based on current state
            decision = await self._make_routing_decision(state)
            
            # Apply the decision to state
            state = self._apply_decision(state, decision)
            
            # Log the decision
            self._log_decision(state, decision)
            
            self.log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Supervisor error: {str(e)}"
            self.log_error(error_msg, state)
            state = add_error(state, error_msg)
            state["should_continue"] = False
            return state
    
    async def _make_routing_decision(self, state: ResearchState) -> SupervisorDecision:
        """
        Core routing logic - determines next agent based on workflow state
        
        Args:
            state: Current research state
            
        Returns:
            Routing decision
        """
        status = state["status"]
        workflow_id = state["workflow_id"]
        
        # Track retry counts per workflow
        if workflow_id not in self.retry_counts:
            self.retry_counts[workflow_id] = {}
        
        # INITIALIZED -> Start with literature search
        if status == WorkflowStatus.INITIALIZED:
            return SupervisorDecision(
                next_agent=AgentType.LITERATURE_HUNTER,
                should_continue=True,
                reason="Starting workflow with literature search"
            )
        
        # SEARCHING -> Check search results
        elif status == WorkflowStatus.SEARCHING:
            return await self._handle_search_results(state)
        
        # SYNTHESIZING -> Check synthesis results
        elif status == WorkflowStatus.SYNTHESIZING:
            return await self._handle_synthesis_results(state)
        
        # GENERATING -> Route between hypothesis and methodology
        elif status == WorkflowStatus.GENERATING:
            return await self._handle_generation_phase(state)
        
        # VALIDATING -> Check if complete
        elif status == WorkflowStatus.VALIDATING:
            return self._handle_validation_results(state)
        
        # COMPLETED or FAILED -> End workflow
        elif status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            return SupervisorDecision(
                next_agent=None,
                should_continue=False,
                reason=f"Workflow {status.value}"
            )
        
        else:
            # Unknown state - use LLM if available, otherwise fail safely
            if self.llm_client:
                return await self._llm_routing_decision(state)
            else:
                return SupervisorDecision(
                    next_agent=None,
                    should_continue=False,
                    reason=f"Unknown workflow status: {status}"
                )
    
    async def _handle_search_results(self, state: ResearchState) -> SupervisorDecision:
        """Handle routing after literature search"""
        papers = state.get("papers", [])
        paper_count = len(papers)
        min_papers = self.quality_thresholds['min_papers']
        
        # Check if we have enough papers
        if paper_count >= min_papers:
            logger.info(f"Found {paper_count} papers, proceeding to synthesis")
            return SupervisorDecision(
                next_agent=AgentType.KNOWLEDGE_SYNTHESIZER,
                should_continue=True,
                reason=f"Sufficient papers found ({paper_count})"
            )
        
        # Not enough papers - check retry count
        retry_key = f"{state['workflow_id']}_{AgentType.LITERATURE_HUNTER}"
        current_retries = self.retry_counts[state['workflow_id']].get(
            AgentType.LITERATURE_HUNTER, 0
        )
        
        if current_retries < self.max_retries[AgentType.LITERATURE_HUNTER]:
            # Retry with adjusted parameters
            self.retry_counts[state['workflow_id']][AgentType.LITERATURE_HUNTER] = current_retries + 1
            
            # Adjust search parameters for retry
            state["max_papers"] = min(state["max_papers"] * 2, 200)
            
            logger.info(
                f"Only {paper_count} papers found (min: {min_papers}). "
                f"Retry {current_retries + 1}/{self.max_retries[AgentType.LITERATURE_HUNTER]}"
            )
            
            return SupervisorDecision(
                next_agent=AgentType.LITERATURE_HUNTER,
                should_continue=True,
                reason=f"Retrying search with expanded parameters (attempt {current_retries + 1})"
            )
        
        # Max retries reached - proceed with what we have or fail
        if paper_count > 0:
            logger.warning(f"Proceeding with only {paper_count} papers after max retries")
            return SupervisorDecision(
                next_agent=AgentType.KNOWLEDGE_SYNTHESIZER,
                should_continue=True,
                reason=f"Proceeding with {paper_count} papers after max retries"
            )
        else:
            return SupervisorDecision(
                next_agent=None,
                should_continue=False,
                reason="No papers found after maximum retries"
            )
    
    async def _handle_synthesis_results(self, state: ResearchState) -> SupervisorDecision:
        """Handle routing after synthesis"""
        synthesis = state.get("synthesis")
        
        if not synthesis:
            # Synthesis failed - check if we should retry
            current_retries = self.retry_counts[state['workflow_id']].get(
                AgentType.KNOWLEDGE_SYNTHESIZER, 0
            )
            
            if current_retries < self.max_retries[AgentType.KNOWLEDGE_SYNTHESIZER]:
                self.retry_counts[state['workflow_id']][AgentType.KNOWLEDGE_SYNTHESIZER] = current_retries + 1
                
                return SupervisorDecision(
                    next_agent=AgentType.KNOWLEDGE_SYNTHESIZER,
                    should_continue=True,
                    reason=f"Retrying synthesis (attempt {current_retries + 1})"
                )
            else:
                # Create minimal synthesis to continue
                state["synthesis"] = {
                    "patterns": [],
                    "key_findings": ["Unable to synthesize patterns"],
                    "research_gaps": ["Further analysis needed"],
                    "total_papers_analyzed": len(state.get("papers", []))
                }
                
                return SupervisorDecision(
                    next_agent=AgentType.HYPOTHESIS_GENERATOR,
                    should_continue=True,
                    reason="Proceeding with minimal synthesis after retries"
                )
        
        # Check synthesis quality
        patterns = synthesis.get("patterns", [])
        gaps = synthesis.get("research_gaps", [])
        
        if len(patterns) >= self.quality_thresholds['min_patterns'] or len(gaps) > 0:
            return SupervisorDecision(
                next_agent=AgentType.HYPOTHESIS_GENERATOR,
                should_continue=True,
                reason=f"Good synthesis with {len(patterns)} patterns and {len(gaps)} gaps"
            )
        else:
            # Poor synthesis - try to get more papers
            if len(state.get("papers", [])) < 20:
                state["max_papers"] = 50
                return SupervisorDecision(
                    next_agent=AgentType.LITERATURE_HUNTER,
                    should_continue=True,
                    reason="Poor synthesis - getting more papers"
                )
            else:
                # Proceed anyway
                return SupervisorDecision(
                    next_agent=AgentType.HYPOTHESIS_GENERATOR,
                    should_continue=True,
                    reason="Proceeding with limited synthesis"
                )
    
    async def _handle_generation_phase(self, state: ResearchState) -> SupervisorDecision:
        """Handle routing during generation phase (hypotheses and methodologies)"""
        hypotheses = state.get("hypotheses", [])
        methodologies = state.get("methodologies", [])
        
        # If no hypotheses yet, we're waiting for hypothesis generation
        if not hypotheses:
            # This shouldn't happen, but handle it
            return SupervisorDecision(
                next_agent=AgentType.HYPOTHESIS_GENERATOR,
                should_continue=True,
                reason="Generating hypotheses"
            )
        
        # If we have hypotheses but no methodologies, generate them
        if hypotheses and not methodologies:
            # Check hypothesis quality first
            if not self._validate_hypotheses_quality(hypotheses):
                # Try regenerating hypotheses
                current_retries = self.retry_counts[state['workflow_id']].get(
                    AgentType.HYPOTHESIS_GENERATOR, 0
                )
                
                if current_retries < self.max_retries[AgentType.HYPOTHESIS_GENERATOR]:
                    self.retry_counts[state['workflow_id']][AgentType.HYPOTHESIS_GENERATOR] = current_retries + 1
                    
                    return SupervisorDecision(
                        next_agent=AgentType.HYPOTHESIS_GENERATOR,
                        should_continue=True,
                        reason=f"Regenerating higher quality hypotheses (attempt {current_retries + 1})"
                    )
            
            return SupervisorDecision(
                next_agent=AgentType.METHODOLOGY_DESIGNER,
                should_continue=True,
                reason=f"Designing methodologies for {len(hypotheses)} hypotheses"
            )
        
        # If we have both hypotheses and methodologies, move to validation
        if hypotheses and methodologies:
            return SupervisorDecision(
                next_agent=AgentType.VALIDATION,
                should_continue=True,
                reason="Moving to validation phase"
            )
        
        # Shouldn't reach here, but fail safely
        return SupervisorDecision(
            next_agent=None,
            should_continue=False,
            reason="Unexpected state in generation phase"
        )
    
    def _handle_validation_results(self, state: ResearchState) -> SupervisorDecision:
        """Handle routing after validation"""
        validation_results = state.get("validation_results", [])
        
        if validation_results:
            # Count valid hypotheses
            valid_count = sum(1 for v in validation_results if v.get("is_valid"))
            
            logger.info(
                f"Validation complete: {valid_count}/{len(validation_results)} "
                f"hypotheses validated successfully"
            )
            
            return SupervisorDecision(
                next_agent=None,
                should_continue=False,
                reason=f"Workflow complete with {valid_count} valid hypotheses"
            )
        else:
            # No validation results - this is an error
            return SupervisorDecision(
                next_agent=None,
                should_continue=False,
                reason="Validation completed but no results generated"
            )
    
    def _validate_hypotheses_quality(self, hypotheses: List[Dict]) -> bool:
        """Check if hypotheses meet quality standards"""
        if len(hypotheses) < self.quality_thresholds['min_hypotheses']:
            return False
        
        # Check average confidence
        avg_confidence = sum(
            h.get("confidence_score", 0) for h in hypotheses
        ) / len(hypotheses)
        
        return avg_confidence >= self.quality_thresholds['min_confidence']
    
    async def _llm_routing_decision(self, state: ResearchState) -> SupervisorDecision:
        """Use LLM for complex routing decisions"""
        if not self.llm_client:
            return SupervisorDecision(
                next_agent=None,
                should_continue=False,
                reason="Cannot make decision without LLM"
            )
        
        try:
            # Prepare state summary for LLM
            prompt = format_prompt(
                agent='supervisor',
                prompt_name='routing_decision',
                status=state["status"],
                papers_count=len(state.get("papers", [])),
                has_synthesis=bool(state.get("synthesis")),
                hypotheses_count=len(state.get("hypotheses", [])),
                error_count=len(state.get("errors", []))
            )
            
            # Get LLM decision
            response = await self.llm_client.generate(prompt)
            
            # Parse LLM response into decision
            return self._parse_llm_decision(response)
            
        except Exception as e:
            logger.error(f"LLM routing decision failed: {e}")
            return SupervisorDecision(
                next_agent=None,
                should_continue=False,
                reason="LLM decision failed"
            )
    
    def _parse_llm_decision(self, response: str) -> SupervisorDecision:
        """Parse LLM response into SupervisorDecision"""
        # Simple parsing - enhance based on your LLM's response format
        response_lower = response.lower()
        
        # Determine next agent
        next_agent = None
        if "literature" in response_lower or "search" in response_lower:
            next_agent = AgentType.LITERATURE_HUNTER
        elif "synthesis" in response_lower or "synthesize" in response_lower:
            next_agent = AgentType.KNOWLEDGE_SYNTHESIZER
        elif "hypothesis" in response_lower or "generate" in response_lower:
            next_agent = AgentType.HYPOTHESIS_GENERATOR
        elif "methodology" in response_lower or "design" in response_lower:
            next_agent = AgentType.METHODOLOGY_DESIGNER
        elif "validation" in response_lower or "validate" in response_lower:
            next_agent = AgentType.VALIDATION
        
        # Determine if should continue
        should_continue = (
            "continue" in response_lower or 
            "next" in response_lower or
            next_agent is not None
        )
        
        return SupervisorDecision(
            next_agent=next_agent,
            should_continue=should_continue,
            reason=response[:200]  # First 200 chars as reason
        )
    
    def _should_terminate(self, state: ResearchState) -> bool:
        """Check if workflow should terminate"""
        # Check explicit termination flag
        if not state.get("should_continue", True):
            return True
        
        # Check if we've completed validation
        if state["status"] == WorkflowStatus.COMPLETED:
            return True
        
        # Check if we've hit max errors
        if len(state.get("errors", [])) >= self.quality_thresholds['max_errors']:
            return True
        
        # Check for timeout (if configured)
        if self.config.get('max_duration_seconds'):
            started = datetime.fromisoformat(state["started_at"])
            elapsed = (datetime.utcnow() - started).total_seconds()
            if elapsed > self.config['max_duration_seconds']:
                logger.warning(f"Workflow timeout: {elapsed}s")
                return True
        
        return False
    
    def _has_critical_errors(self, state: ResearchState) -> bool:
        """Check for critical errors that should stop the workflow"""
        errors = state.get("errors", [])
        
        # Check for specific critical error patterns
        critical_patterns = [
            "api key",
            "rate limit",
            "authentication",
            "unauthorized",
            "quota exceeded"
        ]
        
        for error in errors:
            error_lower = error.lower()
            if any(pattern in error_lower for pattern in critical_patterns):
                return True
        
        return False
    
    def _handle_termination(self, state: ResearchState) -> ResearchState:
        """Handle workflow termination"""
        logger.info(f"Terminating workflow {state['workflow_id']}")
        
        # Set final status if not already set
        if state["status"] not in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            if state.get("validation_results"):
                state = update_state_status(state, WorkflowStatus.COMPLETED, self.name)
            else:
                state = update_state_status(state, WorkflowStatus.FAILED, self.name)
        
        state["should_continue"] = False
        state["completed_at"] = datetime.utcnow().isoformat()
        
        return state
    
    def _handle_critical_errors(self, state: ResearchState) -> ResearchState:
        """Handle critical errors"""
        logger.error(f"Critical errors detected in workflow {state['workflow_id']}")
        
        state = update_state_status(state, WorkflowStatus.FAILED, self.name)
        state["should_continue"] = False
        state["completed_at"] = datetime.utcnow().isoformat()
        
        return state
    
    def _apply_decision(
        self, 
        state: ResearchState, 
        decision: SupervisorDecision
    ) -> ResearchState:
        """Apply routing decision to state"""
        if decision.next_agent:
            # Map agent to workflow status
            status_map = {
                AgentType.LITERATURE_HUNTER: WorkflowStatus.SEARCHING,
                AgentType.KNOWLEDGE_SYNTHESIZER: WorkflowStatus.SYNTHESIZING,
                AgentType.HYPOTHESIS_GENERATOR: WorkflowStatus.GENERATING,
                AgentType.METHODOLOGY_DESIGNER: WorkflowStatus.GENERATING,
                AgentType.VALIDATION: WorkflowStatus.VALIDATING
            }
            
            new_status = status_map.get(decision.next_agent, state["status"])
            state = update_state_status(state, new_status, decision.next_agent)
        
        state["should_continue"] = decision.should_continue
        
        # Add decision to execution history
        if "execution_history" not in state:
            state["execution_history"] = []
        
        state["execution_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "supervisor",
            "decision": {
                "next_agent": decision.next_agent.value if decision.next_agent else None,
                "should_continue": decision.should_continue,
                "reason": decision.reason
            }
        })
        
        return state
    
    def _log_decision(self, state: ResearchState, decision: SupervisorDecision):
        """Log the routing decision"""
        logger.info(
            f"Supervisor decision for workflow {state['workflow_id']}: "
            f"Next={decision.next_agent.value if decision.next_agent else 'END'}, "
            f"Continue={decision.should_continue}, "
            f"Reason='{decision.reason}'"
        )
    
    def reset_retry_counts(self, workflow_id: str):
        """Reset retry counts for a workflow"""
        if workflow_id in self.retry_counts:
            del self.retry_counts[workflow_id]