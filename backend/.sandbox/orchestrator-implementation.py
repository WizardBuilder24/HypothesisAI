# ============================================================================
# app/agents/orchestrator.py
# ============================================================================
"""
Main LangGraph Orchestrator for the Research Workflow
This orchestrates all agents using LangGraph's StateGraph
"""

from typing import Dict, Any, Optional, List, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver, BaseCheckpointSaver
from langgraph.graph.graph import CompiledGraph
import logging
from datetime import datetime

from app.schemas import (
    ResearchState,
    AgentType,
    WorkflowStatus,
    SupervisorDecision
)
from app.core.state_management import (
    create_initial_state,
    update_state_status,
    is_workflow_complete,
    add_error
)

# Import all agents
from app.agents.supervisor import SupervisorAgent
from app.agents.literature_hunter import LiteratureHunterAgent
from app.agents.knowledge_synthesizer import KnowledgeSynthesizerAgent
from app.agents.hypothesis_generator import HypothesisGeneratorAgent
from app.agents.methodology_designer import MethodologyDesignerAgent
from app.agents.validation_agent import ValidationAgent

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """
    Main orchestrator that manages the research workflow using LangGraph
    """
    
    def __init__(
        self,
        llm_client=None,
        search_client=None,
        checkpointer: Optional[BaseCheckpointSaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Research Orchestrator
        
        Args:
            llm_client: LLM client for agents
            search_client: Search client for literature hunter
            checkpointer: LangGraph checkpointer for state persistence
            config: Additional configuration
        """
        self.llm_client = llm_client
        self.search_client = search_client
        self.checkpointer = checkpointer or MemorySaver()
        self.config = config or {}
        
        # Initialize all agents
        self.agents = self._initialize_agents()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        # Compile the graph
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("Research Orchestrator initialized")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agent instances"""
        return {
            AgentType.SUPERVISOR: SupervisorAgent(),
            AgentType.LITERATURE_HUNTER: LiteratureHunterAgent(
                llm_client=self.llm_client,
                search_client=self.search_client
            ),
            AgentType.KNOWLEDGE_SYNTHESIZER: KnowledgeSynthesizerAgent(
                llm_client=self.llm_client
            ),
            AgentType.HYPOTHESIS_GENERATOR: HypothesisGeneratorAgent(
                llm_client=self.llm_client,
                creativity_temperature=self.config.get("creativity_temperature", 0.7)
            ),
            AgentType.METHODOLOGY_DESIGNER: MethodologyDesignerAgent(
                llm_client=self.llm_client
            ),
            AgentType.VALIDATION: ValidationAgent(
                llm_client=self.llm_client,
                strict_mode=self.config.get("strict_validation", False)
            )
        }
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow
        
        Returns:
            Configured StateGraph
        """
        # Create the graph with ResearchState
        workflow = StateGraph(ResearchState)
        
        # Add all agent nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("literature_hunter", self._literature_hunter_node)
        workflow.add_node("knowledge_synthesizer", self._synthesizer_node)
        workflow.add_node("hypothesis_generator", self._hypothesis_node)
        workflow.add_node("methodology_designer", self._methodology_node)
        workflow.add_node("validation", self._validation_node)
        
        # Set the entry point
        workflow.set_entry_point("supervisor")
        
        # Add edges with conditional routing
        workflow.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "literature_hunter": "literature_hunter",
                "knowledge_synthesizer": "knowledge_synthesizer",
                "hypothesis_generator": "hypothesis_generator",
                "methodology_designer": "methodology_designer",
                "validation": "validation",
                "end": END
            }
        )
        
        # Add edges from each agent back to supervisor
        workflow.add_edge("literature_hunter", "supervisor")
        workflow.add_edge("knowledge_synthesizer", "supervisor")
        workflow.add_edge("hypothesis_generator", "supervisor")
        workflow.add_edge("methodology_designer", "supervisor")
        workflow.add_edge("validation", "supervisor")
        
        return workflow
    
    # ========================================================================
    # Node Functions - Each node wraps an agent
    # ========================================================================
    
    async def _supervisor_node(self, state: ResearchState) -> ResearchState:
        """Supervisor node - makes routing decisions"""
        logger.info(f"Supervisor node processing workflow {state['workflow_id']}")
        
        try:
            supervisor = self.agents[AgentType.SUPERVISOR]
            state = await supervisor.process(state)
            
            # Log decision
            logger.info(
                f"Supervisor decision - Status: {state['status']}, "
                f"Continue: {state['should_continue']}"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Supervisor node error: {e}")
            state = add_error(state, f"Supervisor error: {str(e)}")
            state["should_continue"] = False
            return state
    
    async def _literature_hunter_node(self, state: ResearchState) -> ResearchState:
        """Literature Hunter node - searches for papers"""
        logger.info(f"Literature Hunter processing: {state['query'][:100]}")
        
        try:
            agent = self.agents[AgentType.LITERATURE_HUNTER]
            state = await agent.process(state)
            
            logger.info(f"Literature Hunter found {len(state.get('papers', []))} papers")
            return state
            
        except Exception as e:
            logger.error(f"Literature Hunter error: {e}")
            state = add_error(state, f"Literature search failed: {str(e)}")
            # Don't stop workflow, supervisor will decide
            return state
    
    async def _synthesizer_node(self, state: ResearchState) -> ResearchState:
        """Knowledge Synthesizer node - synthesizes patterns"""
        logger.info(f"Synthesizer processing {len(state.get('papers', []))} papers")
        
        try:
            agent = self.agents[AgentType.KNOWLEDGE_SYNTHESIZER]
            state = await agent.process(state)
            
            if state.get('synthesis'):
                patterns = len(state['synthesis'].get('patterns', []))
                logger.info(f"Synthesizer identified {patterns} patterns")
            
            return state
            
        except Exception as e:
            logger.error(f"Synthesizer error: {e}")
            state = add_error(state, f"Synthesis failed: {str(e)}")
            return state
    
    async def _hypothesis_node(self, state: ResearchState) -> ResearchState:
        """Hypothesis Generator node - generates hypotheses"""
        logger.info("Hypothesis Generator processing synthesis")
        
        try:
            agent = self.agents[AgentType.HYPOTHESIS_GENERATOR]
            state = await agent.process(state)
            
            logger.info(f"Generated {len(state.get('hypotheses', []))} hypotheses")
            return state
            
        except Exception as e:
            logger.error(f"Hypothesis Generator error: {e}")
            state = add_error(state, f"Hypothesis generation failed: {str(e)}")
            return state
    
    async def _methodology_node(self, state: ResearchState) -> ResearchState:
        """Methodology Designer node - designs methodologies"""
        logger.info(f"Methodology Designer processing {len(state.get('hypotheses', []))} hypotheses")
        
        try:
            agent = self.agents[AgentType.METHODOLOGY_DESIGNER]
            state = await agent.process(state)
            
            logger.info(f"Designed {len(state.get('methodologies', []))} methodologies")
            return state
            
        except Exception as e:
            logger.error(f"Methodology Designer error: {e}")
            state = add_error(state, f"Methodology design failed: {str(e)}")
            return state
    
    async def _validation_node(self, state: ResearchState) -> ResearchState:
        """Validation node - validates hypotheses and methodologies"""
        logger.info("Validation Agent processing")
        
        try:
            agent = self.agents[AgentType.VALIDATION]
            state = await agent.process(state)
            
            valid_count = sum(
                1 for v in state.get('validation_results', [])
                if v.get('is_valid')
            )
            logger.info(f"Validation complete: {valid_count} valid hypotheses")
            
            return state
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            state = add_error(state, f"Validation failed: {str(e)}")
            state["should_continue"] = False
            return state
    
    # ========================================================================
    # Routing Logic
    # ========================================================================
    
    def _route_from_supervisor(
        self, 
        state: ResearchState
    ) -> Literal["literature_hunter", "knowledge_synthesizer", 
                 "hypothesis_generator", "methodology_designer", 
                 "validation", "end"]:
        """
        Determine next node based on supervisor decision
        
        Args:
            state: Current research state
            
        Returns:
            Name of next node or "end"
        """
        # Check if workflow should end
        if not state.get("should_continue", True):
            logger.info("Workflow ending - should_continue is False")
            return "end"
        
        if is_workflow_complete(state):
            logger.info("Workflow complete")
            return "end"
        
        # Route based on current agent set by supervisor
        current_agent = state.get("current_agent")
        
        if current_agent == AgentType.LITERATURE_HUNTER:
            return "literature_hunter"
        elif current_agent == AgentType.KNOWLEDGE_SYNTHESIZER:
            return "knowledge_synthesizer"
        elif current_agent == AgentType.HYPOTHESIS_GENERATOR:
            return "hypothesis_generator"
        elif current_agent == AgentType.METHODOLOGY_DESIGNER:
            return "methodology_designer"
        elif current_agent == AgentType.VALIDATION:
            return "validation"
        else:
            # Default to end if no clear next step
            logger.warning(f"No routing for agent: {current_agent}")
            return "end"
    
    # ========================================================================
    # Public Interface
    # ========================================================================
    
    async def run_research(
        self,
        query: str,
        max_papers: int = 50,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete research workflow
        
        Args:
            query: Research query
            max_papers: Maximum papers to analyze
            config: Runtime configuration
            
        Returns:
            Final state with all results
        """
        # Create initial state
        initial_state = create_initial_state(query, max_papers)
        
        logger.info(
            f"Starting research workflow {initial_state['workflow_id']} "
            f"for query: {query[:100]}"
        )
        
        # Run configuration
        run_config = {
            "configurable": {
                "thread_id": initial_state["workflow_id"]
            }
        }
        
        if config:
            run_config.update(config)
        
        try:
            # Run the workflow
            final_state = await self.app.ainvoke(
                initial_state,
                config=run_config
            )
            
            logger.info(
                f"Workflow {initial_state['workflow_id']} completed "
                f"with status: {final_state.get('status')}"
            )
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            raise
    
    async def run_research_stream(
        self,
        query: str,
        max_papers: int = 50,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Run research workflow with streaming updates
        
        Args:
            query: Research query
            max_papers: Maximum papers to analyze
            config: Runtime configuration
            
        Yields:
            State updates as the workflow progresses
        """
        # Create initial state
        initial_state = create_initial_state(query, max_papers)
        
        logger.info(f"Starting streaming research for: {query[:100]}")
        
        # Run configuration
        run_config = {
            "configurable": {
                "thread_id": initial_state["workflow_id"]
            }
        }
        
        if config:
            run_config.update(config)
        
        try:
            # Stream the workflow execution
            async for state in self.app.astream(
                initial_state,
                config=run_config
            ):
                # Yield intermediate states
                yield state
                
                # Log progress
                if isinstance(state, dict):
                    current = state.get("current_agent", "unknown")
                    logger.info(f"Workflow progress: {current}")
                    
        except Exception as e:
            logger.error(f"Streaming workflow error: {e}")
            raise
    
    def get_graph_visualization(self) -> str:
        """
        Get a visualization of the workflow graph
        
        Returns:
            Mermaid diagram string
        """
        try:
            # LangGraph's built-in visualization
            return self.app.get_graph().draw_mermaid()
        except:
            # Fallback visualization
            return """
            graph TD
                Start --> Supervisor
                Supervisor --> LiteratureHunter
                Supervisor --> KnowledgeSynthesizer
                Supervisor --> HypothesisGenerator
                Supervisor --> MethodologyDesigner
                Supervisor --> Validation
                Supervisor --> End
                
                LiteratureHunter --> Supervisor
                KnowledgeSynthesizer --> Supervisor
                HypothesisGenerator --> Supervisor
                MethodologyDesigner --> Supervisor
                Validation --> Supervisor
            """
    
    async def get_workflow_state(
        self, 
        workflow_id: str
    ) -> Optional[ResearchState]:
        """
        Get the current state of a workflow
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Current state or None if not found
        """
        try:
            config = {"configurable": {"thread_id": workflow_id}}
            state = await self.app.aget_state(config)
            return state.values if state else None
        except Exception as e:
            logger.error(f"Error getting workflow state: {e}")
            return None
    
    async def update_workflow_state(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> ResearchState:
        """
        Update a workflow's state (for human-in-the-loop)
        
        Args:
            workflow_id: Workflow ID
            updates: State updates to apply
            
        Returns:
            Updated state
        """
        try:
            config = {"configurable": {"thread_id": workflow_id}}
            
            # Get current state
            current = await self.app.aget_state(config)
            if not current:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Apply updates
            updated_state = {**current.values, **updates}
            updated_state["updated_at"] = datetime.utcnow().isoformat()
            
            # Update the state
            await self.app.aupdate_state(config, updated_state)
            
            logger.info(f"Updated workflow {workflow_id} state")
            return updated_state
            
        except Exception as e:
            logger.error(f"Error updating workflow state: {e}")
            raise


# ============================================================================
# app/agents/__init__.py
# ============================================================================
"""
Agents package initialization
Export main orchestrator and agents
"""

from app.agents.orchestrator import ResearchOrchestrator
from app.agents.supervisor import SupervisorAgent
from app.agents.literature_hunter import LiteratureHunterAgent
from app.agents.knowledge_synthesizer import KnowledgeSynthesizerAgent
from app.agents.hypothesis_generator import HypothesisGeneratorAgent
from app.agents.methodology_designer import MethodologyDesignerAgent
from app.agents.validation_agent import ValidationAgent

__all__ = [
    'ResearchOrchestrator',
    'SupervisorAgent',
    'LiteratureHunterAgent',
    'KnowledgeSynthesizerAgent',
    'HypothesisGeneratorAgent',
    'MethodologyDesignerAgent',
    'ValidationAgent'
]


# ============================================================================
# Example Usage
# ============================================================================
"""
Example: app/main.py or app/api/research.py
"""

import asyncio
from app.agents import ResearchOrchestrator


async def run_example():
    """Example of running the research workflow"""
    
    # Initialize orchestrator (with mock clients for testing)
    orchestrator = ResearchOrchestrator(
        llm_client=None,  # Will use mock data
        search_client=None,  # Will use mock data
        config={
            "creativity_temperature": 0.8,
            "strict_validation": False
        }
    )
    
    # Run research
    query = "What are the latest advances in quantum computing for drug discovery?"
    
    # Option 1: Run complete workflow
    result = await orchestrator.run_research(
        query=query,
        max_papers=20
    )
    
    print(f"Research complete!")
    print(f"Papers found: {len(result.get('papers', []))}")
    print(f"Hypotheses generated: {len(result.get('hypotheses', []))}")
    print(f"Validation results: {len(result.get('validation_results', []))}")
    
    # Option 2: Stream workflow updates
    print("\nStreaming workflow:")
    async for update in orchestrator.run_research_stream(query, max_papers=10):
        if isinstance(update, dict):
            agent = update.get("current_agent", "unknown")
            status = update.get("status", "unknown")
            print(f"  -> Agent: {agent}, Status: {status}")
    
    # Get workflow visualization
    print("\nWorkflow Graph:")
    print(orchestrator.get_graph_visualization())


# Run example if this file is executed directly
if __name__ == "__main__":
    asyncio.run(run_example())