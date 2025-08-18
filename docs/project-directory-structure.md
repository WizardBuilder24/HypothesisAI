# HypothesisAI - Project Directory Structure

```
hypothesis-ai/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI app initialization
│   │   ├── config.py                    # Configuration management
│   │   │
│   │   ├── agents/                      # LangGraph agents
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Base agent class
│   │   │   ├── supervisor.py            # Supervisor agent
│   │   │   ├── literature_hunter.py     # Literature search agent
│   │   │   ├── knowledge_synthesizer.py # Synthesis agent
│   │   │   ├── hypothesis_generator.py  # Hypothesis generation agent
│   │   │   ├── methodology_designer.py  # Methodology design agent
│   │   │   └── validation_agent.py      # Validation agent
│   │   │
│   │   ├── graph/                       # LangGraph workflow
│   │   │   ├── __init__.py
│   │   │   ├── workflow.py              # Main workflow definition
│   │   │   ├── state.py                 # State definitions
│   │   │   ├── nodes.py                 # Node implementations
│   │   │   └── edges.py                 # Edge conditions
│   │   │
│   │   ├── schemas/                     # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Base schemas and enums
│   │   │   ├── papers.py                # Paper-related schemas
│   │   │   ├── synthesis.py             # Synthesis schemas
│   │   │   ├── hypothesis.py            # Hypothesis schemas
│   │   │   ├── methodology.py           # Methodology schemas
│   │   │   ├── validation.py            # Validation schemas
│   │   │   └── requests.py              # API request/response schemas
│   │   │
│   │   ├── services/                    # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── research_service.py      # Main research orchestration
│   │   │   ├── llm_service.py           # LLM client management
│   │   │   ├── search_service.py        # Literature search service
│   │   │   ├── storage_service.py       # Data persistence
│   │   │   └── export_service.py        # Export functionality
│   │   │
│   │   ├── api/                         # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                  # Dependencies
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── research.py          # Research endpoints
│   │   │       ├── projects.py          # Project management
│   │   │       ├── health.py            # Health checks
│   │   │       └── websocket.py         # WebSocket for streaming
│   │   │
│   │   ├── core/                        # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── llm_clients.py           # LangChain LLM clients
│   │   │   ├── state_management.py      # State helpers
│   │   │   ├── exceptions.py            # Custom exceptions
│   │   │   ├── logging.py               # Logging configuration
│   │   │   └── security.py              # Auth & security
│   │   │
│   │   ├── integrations/                # External integrations
│   │   │   ├── __init__.py
│   │   │   ├── arxiv/
│   │   │   │   ├── __init__.py
│   │   │   │   └── client.py
│   │   │   ├── pubmed/
│   │   │   │   ├── __init__.py
│   │   │   │   └── client.py
│   │   │   ├── semantic_scholar/
│   │   │   │   ├── __init__.py
│   │   │   │   └── client.py
│   │   │   └── vector_db/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       └── qdrant_client.py
│   │   │
│   │   ├── models/                      # Database models (if using)
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── project.py
│   │   │   ├── workflow.py
│   │   │   └── user.py
│   │   │
│   │   ├── prompts/                     # Prompt management
│   │   │   ├── __init__.py
│   │   │   ├── prompt_manager.py
│   │   │   └── templates/
│   │   │       ├── research_prompts.yaml
│   │   │       ├── system_prompts.yaml
│   │   │       └── domain_prompts.yaml
│   │   │
│   │   └── utils/                       # Utility functions
│   │       ├── __init__.py
│   │       ├── formatting.py
│   │       ├── validation.py
│   │       └── helpers.py
│   │
│   ├── tests/                           # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py                  # Pytest fixtures
│   │   ├── unit/
│   │   │   ├── test_agents.py
│   │   │   ├── test_schemas.py
│   │   │   └── test_services.py
│   │   ├── integration/
│   │   │   ├── test_workflow.py
│   │   │   ├── test_api.py
│   │   │   └── test_llm_clients.py
│   │   └── e2e/
│   │       └── test_research_flow.py
│   │
│   ├── scripts/                         # Utility scripts
│   │   ├── seed_db.py
│   │   ├── validate_prompts.py
│   │   └── test_llm_connection.py
│   │
│   ├── .env.example                     # Environment variables template
│   ├── requirements.txt                 # Python dependencies
│   ├── requirements-dev.txt             # Development dependencies
│   └── README.md                        # Backend documentation
│
├── frontend/                            # Frontend application (if needed)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   └── README.md
│
├── notebooks/                           # Jupyter notebooks
│   ├── examples/
│   │   ├── basic_research.ipynb
│   │   ├── streaming_demo.ipynb
│   │   └── multi_llm_comparison.ipynb
│   └── experiments/
│       ├── prompt_engineering.ipynb
│       └── agent_testing.ipynb
│
├── docs/                                # Documentation
│   ├── api/
│   │   └── openapi.yaml
│   ├── architecture/
│   │   ├── system_design.md
│   │   ├── agent_flow.md
│   │   └── diagrams/
│   ├── guides/
│   │   ├── getting_started.md
│   │   ├── deployment.md
│   │   └── configuration.md
│   └── development/
│       ├── contributing.md
│       └── code_standards.md
│
├── deployment/                          # Deployment configurations
│   ├── kubernetes/
│   │   ├── app-deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── terraform/
│   │   ├── main.tf
│   │   └── variables.tf
│   └── scripts/
│       ├── deploy.sh
│       └── rollback.sh
│
├── .github/                            # GitHub Actions
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── tests.yml
│
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml                  # Docker Compose for entire stack
├── docker-compose.dev.yml              # Development overrides
├── docker-compose.prod.yml             # Production overrides
├── Dockerfile                          # Multi-stage Dockerfile
├── .dockerignore                       # Docker ignore file
├── .env.example                        # Environment variables template
├── pyproject.toml                      # Python project configuration
├── Makefile                            # Common commands
├── LICENSE
└── README.md                           # Project documentation
```

## File Organization by Module

### 1. **Graph Module** (`app/graph/`)
Separates LangGraph-specific logic:
- `workflow.py`: Main graph construction
- `state.py`: State definitions (ResearchState)
- `nodes.py`: Node function implementations
- `edges.py`: Routing logic and conditions

### 2. **Services Module** (`app/services/`)
Business logic layer:
- `research_service.py`: High-level research interface
- `llm_service.py`: LLM provider management
- `search_service.py`: Paper search orchestration
- `storage_service.py`: Result persistence
- `export_service.py`: Export to various formats

### 3. **API Module** (`app/api/v1/`)
RESTful endpoints:
- `research.py`: Research workflow endpoints
- `projects.py`: Project CRUD operations
- `health.py`: Health and readiness checks
- `websocket.py`: Real-time streaming

### 4. **Integrations Module** (`app/integrations/`)
External service clients:
- Each integration in its own subdirectory
- Base classes for common patterns
- Easily extensible for new sources

### 5. **Prompts Module** (`app/prompts/`)
Centralized prompt management:
- YAML templates in `templates/`
- `prompt_manager.py` for loading and formatting
- Environment-specific prompts support

## Key Improvements Over Flat Structure

### 1. **Clear Separation of Concerns**
- Graph logic separate from business logic
- API layer independent of implementation
- Integrations isolated from core

### 2. **Better Testability**
- Each module can be tested independently
- Clear boundaries for mocking
- Separate test directories by type

### 3. **Scalability**
- Easy to add new agents
- Simple to add new integrations
- Clear places for new features

### 4. **Maintainability**
- Related code grouped together
- Clear import paths
- Consistent patterns across modules

## Migration Guide

### From Current Structure to New Structure:

1. **Move agent implementations**:
   - `app/agents/*.py` → `backend/app/agents/`

2. **Extract graph logic**:
   - `orchestrator.py` → Split into `graph/workflow.py`, `graph/nodes.py`, `graph/edges.py`

3. **Move schemas**:
   - `app/schemas/*.py` → `backend/app/schemas/`

4. **Create service layer**:
   - Extract business logic from agents → `services/`

5. **Organize prompts**:
   - Move YAML files → `prompts/templates/`

6. **Setup API layer**:
   - Create FastAPI endpoints in `api/v1/`

## Example File Contents

### `backend/app/graph/workflow.py`
```python
from langgraph.graph import StateGraph
from app.graph.state import ResearchState
from app.graph.nodes import create_nodes
from app.graph.edges import create_edges

def create_research_graph() -> StateGraph:
    """Create the main research workflow graph"""
    graph = StateGraph(ResearchState)
    
    # Add nodes
    nodes = create_nodes()
    for name, node in nodes.items():
        graph.add_node(name, node)
    
    # Add edges
    edges = create_edges()
    for edge in edges:
        graph.add_edge(**edge)
    
    return graph
```

### `backend/app/services/research_service.py`
```python
from app.graph.workflow import create_research_graph
from app.schemas.requests import ResearchRequest
from app.core.llm_clients import create_llm_client

class ResearchService:
    """High-level research orchestration service"""
    
    def __init__(self, config):
        self.graph = create_research_graph()
        self.llm_client = create_llm_client(config)
    
    async def run_research(self, request: ResearchRequest):
        # Implementation
        pass
```

### `backend/app/api/v1/research.py`
```python
from fastapi import APIRouter, Depends
from app.services.research_service import ResearchService
from app.schemas.requests import ResearchRequest, ResearchResponse

router = APIRouter(prefix="/research", tags=["research"])

@router.post("/", response_model=ResearchResponse)
async def create_research(
    request: ResearchRequest,
    service: ResearchService = Depends(get_research_service)
):
    return await service.run_research(request)
```

This structure provides:
- **Clear organization** following best practices
- **Modularity** for easy testing and maintenance
- **Scalability** for growing the application
- **Flexibility** to add new features
- **Separation** between LangGraph logic and business logic