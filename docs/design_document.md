# HypothesisAI System Design Document
## Comprehensive Software Architecture and Design Blueprint

**Document Version:** 1.0  
**Date:** January 2025  
**Document Type:** System Design Specification  
**Project Phase:** Design Phase  
**Status:** Draft for Review  
**IEEE Std 1016-2009 Compliant**  

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [System Architecture Design](#2-system-architecture-design)
3. [Component Design](#3-component-design)
4. [Data Architecture](#4-data-architecture)
5. [Interface Design](#5-interface-design)
6. [API Design](#6-api-design)
7. [Security Architecture](#7-security-architecture)
8. [Infrastructure Design](#8-infrastructure-design)
9. [Design Decisions and Rationale](#9-design-decisions-and-rationale)
10. [Appendices](#10-appendices)

---

## 1. Introduction

### 1.1 Purpose
This System Design Document provides the comprehensive architectural blueprint for the HypothesisAI Multi-Agent Scientific Research Platform. It serves as the authoritative reference for developers, architects, and stakeholders throughout the implementation phase.

### 1.2 Scope
This document covers:
- System architecture and component design
- Data models and database schemas
- User interface specifications
- API contracts and integration patterns
- Security and infrastructure design
- Design patterns and best practices

### 1.3 Design Principles

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Modularity** | Loosely coupled, highly cohesive components | Microservices architecture |
| **Scalability** | Horizontal scaling capability | Kubernetes, load balancing |
| **Reliability** | Fault tolerance and resilience | Circuit breakers, retries |
| **Security** | Defense in depth | Multi-layer security |
| **Performance** | Sub-2 second response times | Caching, optimization |
| **Maintainability** | Clean code, documentation | Design patterns, standards |

### 1.4 Technology Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│         React 18 • TypeScript • TailwindCSS • Redux         │
├─────────────────────────────────────────────────────────────┤
│                         API Gateway                          │
│              Kong • Rate Limiting • Authentication          │
├─────────────────────────────────────────────────────────────┤
│                     Application Services                     │
│     Python 3.11 • FastAPI • LangGraph • Celery • Redis     │
├─────────────────────────────────────────────────────────────┤
│                        Data Layer                           │
│     PostgreSQL 14 • Qdrant • Redis • S3 • Elasticsearch   │
├─────────────────────────────────────────────────────────────┤
│                     Infrastructure Layer                     │
│        Docker • Kubernetes • AWS/GCP • Terraform           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. System Architecture Design

### 2.1 High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Application]
        API_CLIENT[API Clients]
    end
    
    subgraph "Edge Layer"
        CDN[CloudFlare CDN]
        LB[Load Balancer]
    end
    
    subgraph "API Gateway Layer"
        KONG[Kong Gateway]
        AUTH[Auth Service]
    end
    
    subgraph "Application Layer"
        subgraph "Core Services"
            USER_SVC[User Service]
            PROJECT_SVC[Project Service]
            SEARCH_SVC[Search Service]
        end
        
        subgraph "Agent Services"
            ORCHESTRATOR[Agent Orchestrator]
            LITERATURE[Literature Hunter]
            SYNTHESIS[Knowledge Synthesizer]
            HYPOTHESIS[Hypothesis Generator]
        end
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        QDRANT[(Qdrant)]
        REDIS[(Redis)]
        S3[(S3 Storage)]
    end
    
    subgraph "External Services"
        ARXIV[arXiv API]
        PUBMED[PubMed API]
        OPENAI[OpenAI API]
    end
    
    WEB --> CDN
    API_CLIENT --> CDN
    CDN --> LB
    LB --> KONG
    KONG --> AUTH
    KONG --> USER_SVC
    KONG --> PROJECT_SVC
    KONG --> SEARCH_SVC
    SEARCH_SVC --> ORCHESTRATOR
    ORCHESTRATOR --> LITERATURE
    ORCHESTRATOR --> SYNTHESIS
    ORCHESTRATOR --> HYPOTHESIS
    
    USER_SVC --> PG
    PROJECT_SVC --> PG
    LITERATURE --> QDRANT
    SYNTHESIS --> REDIS
    
    LITERATURE --> ARXIV
    LITERATURE --> PUBMED
    HYPOTHESIS --> OPENAI
```

### 2.2 Architectural Patterns

#### 2.2.1 Microservices Architecture

| Service | Responsibility | Technology | Communication |
|---------|---------------|------------|---------------|
| User Service | Authentication, profiles | FastAPI | REST/gRPC |
| Project Service | Project management | FastAPI | REST/gRPC |
| Search Service | Literature search | FastAPI | REST/gRPC |
| Agent Orchestrator | Agent coordination | LangGraph | Async Queue |
| Literature Hunter | Paper discovery | Python | Message Queue |
| Knowledge Synthesizer | Pattern recognition | Python | Message Queue |
| Hypothesis Generator | Hypothesis creation | Python | Message Queue |
| Notification Service | Email, webhooks | FastAPI | Event-driven |

#### 2.2.2 Event-Driven Architecture

```python
# Event Bus Design
class EventBus:
    """
    Central event bus for inter-service communication
    """
    def __init__(self):
        self.topics = {
            "user.created": ["notification.service", "analytics.service"],
            "search.completed": ["project.service", "cache.service"],
            "hypothesis.generated": ["notification.service", "project.service"],
            "paper.processed": ["vector.service", "cache.service"]
        }
    
    def publish(self, event_type: str, payload: dict):
        """Publish event to all subscribers"""
        pass
    
    def subscribe(self, service: str, event_type: str):
        """Subscribe service to event type"""
        pass
```

### 2.3 LangGraph Agent Architecture

```python
from typing import TypedDict, Annotated, List, Literal
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolExecutor
from langgraph.checkpoint import MemorySaver

class ResearchState(TypedDict):
    """Global state for research workflow"""
    query: str
    papers: List[dict]
    synthesis: dict
    hypotheses: List[dict]
    confidence_scores: List[float]
    current_agent: str
    workflow_status: str
    error_log: List[str]

class AgentOrchestrator:
    """
    Main orchestrator for multi-agent research system
    """
    def __init__(self):
        self.workflow = StateGraph(ResearchState)
        self.memory = MemorySaver()
        self._build_workflow()
    
    def _build_workflow(self):
        # Add nodes for each agent
        self.workflow.add_node("supervisor", self.supervisor_agent)
        self.workflow.add_node("literature_hunter", self.literature_hunter_agent)
        self.workflow.add_node("synthesizer", self.knowledge_synthesizer_agent)
        self.workflow.add_node("hypothesis_gen", self.hypothesis_generator_agent)
        self.workflow.add_node("validator", self.validation_agent)
        
        # Define edges
        self.workflow.add_edge("supervisor", "literature_hunter")
        self.workflow.add_edge("literature_hunter", "synthesizer")
        self.workflow.add_edge("synthesizer", "hypothesis_gen")
        self.workflow.add_edge("hypothesis_gen", "validator")
        self.workflow.add_edge("validator", "supervisor")
        
        # Set entry point
        self.workflow.set_entry_point("supervisor")
    
    def supervisor_agent(self, state: ResearchState) -> ResearchState:
        """Route and coordinate agent tasks"""
        # Implementation
        pass
    
    def literature_hunter_agent(self, state: ResearchState) -> ResearchState:
        """Search and retrieve relevant papers"""
        # Implementation
        pass
```

### 2.4 Service Communication Patterns

#### 2.4.1 Synchronous Communication (REST)
```yaml
# OpenAPI Specification Example
openapi: 3.0.0
paths:
  /api/v1/search:
    post:
      summary: Execute literature search
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                query:
                  type: string
                databases:
                  type: array
                  items:
                    type: string
                filters:
                  type: object
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  results:
                    type: array
                  total:
                    type: integer
                  query_id:
                    type: string
```

#### 2.4.2 Asynchronous Communication (Message Queue)
```python
# Celery Task Definition
from celery import Celery, Task
from typing import Dict, List

app = Celery('hypothesisai', broker='redis://localhost:6379')

class AgentTask(Task):
    """Base class for agent tasks"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True

@app.task(base=AgentTask, bind=True)
def process_literature_search(self, query: str, databases: List[str]) -> Dict:
    """
    Asynchronous literature search task
    """
    try:
        results = []
        for db in databases:
            # Search each database
            db_results = search_database(db, query)
            results.extend(db_results)
        
        # Store results in cache
        cache_key = f"search:{self.request.id}"
        redis_client.setex(cache_key, 3600, json.dumps(results))
        
        return {
            'task_id': self.request.id,
            'status': 'completed',
            'result_count': len(results)
        }
    except Exception as e:
        self.retry(exc=e)
```

---

## 3. Component Design

### 3.1 Frontend Components

#### 3.1.1 Component Hierarchy

```
src/
├── components/
│   ├── common/
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── Forms/
│   │   │   ├── SearchForm.tsx
│   │   │   ├── ProjectForm.tsx
│   │   │   └── ValidationSchema.ts
│   │   └── UI/
│   │       ├── Button.tsx
│   │       ├── Modal.tsx
│   │       └── Table.tsx
│   ├── features/
│   │   ├── Search/
│   │   │   ├── SearchContainer.tsx
│   │   │   ├── SearchResults.tsx
│   │   │   └── SearchFilters.tsx
│   │   ├── Projects/
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectDetail.tsx
│   │   │   └── ProjectTree.tsx
│   │   ├── Hypothesis/
│   │   │   ├── HypothesisGenerator.tsx
│   │   │   ├── HypothesisResults.tsx
│   │   │   └── ConfidenceScore.tsx
│   │   └── Synthesis/
│   │       ├── SynthesisView.tsx
│   │       ├── KnowledgeGraph.tsx
│   │       └── PatternDisplay.tsx
│   └── hooks/
│       ├── useAuth.ts
│       ├── useSearch.ts
│       └── useWebSocket.ts
```

#### 3.1.2 State Management (Redux)

```typescript
// Store Structure
interface AppState {
  auth: AuthState;
  projects: ProjectState;
  search: SearchState;
  synthesis: SynthesisState;
  hypothesis: HypothesisState;
  ui: UIState;
}

// Example Slice: Search State
interface SearchState {
  queries: Record<string, SearchQuery>;
  results: Record<string, SearchResult[]>;
  loading: boolean;
  error: string | null;
  filters: SearchFilters;
  pagination: PaginationState;
}

// Redux Toolkit Slice
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const executeSearch = createAsyncThunk(
  'search/execute',
  async (params: SearchParams) => {
    const response = await searchAPI.search(params);
    return response.data;
  }
);

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setFilters: (state, action) => {
      state.filters = action.payload;
    },
    clearResults: (state) => {
      state.results = {};
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(executeSearch.pending, (state) => {
        state.loading = true;
      })
      .addCase(executeSearch.fulfilled, (state, action) => {
        state.loading = false;
        state.results[action.meta.requestId] = action.payload;
      })
      .addCase(executeSearch.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});
```

### 3.2 Backend Service Components

#### 3.2.1 Service Layer Architecture

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

T = TypeVar('T')
ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)

class BaseService(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class with CRUD operations
    """
    def __init__(self, model: ModelType):
        self.model = model
    
    @abstractmethod
    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """Create new object"""
        pass
    
    @abstractmethod
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get object by ID"""
        pass
    
    @abstractmethod
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple objects"""
        pass
    
    @abstractmethod
    def update(self, db: Session, id: int, obj_in: UpdateSchemaType) -> ModelType:
        """Update object"""
        pass
    
    @abstractmethod
    def delete(self, db: Session, id: int) -> ModelType:
        """Delete object"""
        pass

class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate]):
    """
    Service for project management
    """
    def __init__(self):
        super().__init__(Project)
        self.cache = RedisCache()
        self.search_engine = ElasticsearchClient()
    
    def create(self, db: Session, obj_in: ProjectCreate, user_id: int) -> Project:
        """Create new project with associated resources"""
        project = Project(
            **obj_in.dict(),
            owner_id=user_id,
            created_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Index in search engine
        self.search_engine.index('projects', project.id, project.to_dict())
        
        # Invalidate cache
        self.cache.delete(f"user_projects:{user_id}")
        
        return project
    
    def add_paper_to_project(self, db: Session, project_id: int, paper: Paper) -> None:
        """Add paper to project with vector embedding"""
        # Get paper embedding
        embedding = self.get_paper_embedding(paper)
        
        # Store in vector database
        self.vector_db.add_vector(
            collection="project_papers",
            id=f"{project_id}_{paper.id}",
            vector=embedding,
            metadata=paper.to_dict()
        )
        
        # Update project
        project = self.get(db, project_id)
        project.papers.append(paper)
        db.commit()
```

#### 3.2.2 Repository Pattern

```python
from typing import Generic, TypeVar, Optional, List, Type
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Base repository with common database operations
    """
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: dict
    ) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

class ProjectRepository(BaseRepository[Project]):
    """Repository for project-specific operations"""
    
    def get_by_owner(
        self,
        db: Session,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        return (
            db.query(self.model)
            .filter(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search(
        self,
        db: Session,
        *,
        query: str,
        owner_id: Optional[int] = None
    ) -> List[Project]:
        q = db.query(self.model).filter(
            Project.name.contains(query) | 
            Project.description.contains(query)
        )
        if owner_id:
            q = q.filter(Project.owner_id == owner_id)
        return q.all()
```

---

## 4. Data Architecture

### 4.1 Database Schema Design

#### 4.1.1 Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ PROJECT : owns
    USER ||--o{ TEAM_MEMBER : belongs_to
    TEAM ||--o{ TEAM_MEMBER : has
    TEAM ||--o{ PROJECT : owns
    PROJECT ||--o{ PROJECT_PAPER : contains
    PAPER ||--o{ PROJECT_PAPER : belongs_to
    PROJECT ||--o{ HYPOTHESIS : generates
    PROJECT ||--o{ SYNTHESIS : creates
    PAPER ||--o{ CITATION : references
    PAPER ||--o{ ANNOTATION : has
    USER ||--o{ ANNOTATION : creates
    HYPOTHESIS ||--o{ VALIDATION : undergoes
    
    USER {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        json profile
        timestamp created_at
        timestamp updated_at
        boolean is_active
        string role
    }
    
    PROJECT {
        uuid id PK
        string name
        text description
        uuid owner_id FK
        uuid team_id FK
        json settings
        timestamp created_at
        timestamp updated_at
        string status
    }
    
    PAPER {
        uuid id PK
        string doi UK
        string title
        text abstract
        json authors
        date publication_date
        string source_database
        json metadata
        vector embedding
        timestamp indexed_at
    }
    
    HYPOTHESIS {
        uuid id PK
        uuid project_id FK
        text content
        float confidence_score
        json evidence
        json reasoning
        timestamp generated_at
        string status
    }
```

#### 4.1.2 PostgreSQL Schema

```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    profile JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    role VARCHAR(50) DEFAULT 'user',
    two_factor_secret VARCHAR(255),
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role) WHERE is_active = true;

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    tags TEXT[],
    is_public BOOLEAN DEFAULT false
);

CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_team ON projects(team_id);
CREATE INDEX idx_projects_tags ON projects USING GIN(tags);

-- Papers
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doi VARCHAR(255) UNIQUE,
    title TEXT NOT NULL,
    abstract TEXT,
    authors JSONB,
    publication_date DATE,
    source_database VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    full_text TEXT,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    citation_count INTEGER DEFAULT 0,
    quality_score FLOAT
);

CREATE INDEX idx_papers_doi ON papers(doi) WHERE doi IS NOT NULL;
CREATE INDEX idx_papers_publication_date ON papers(publication_date);
CREATE INDEX idx_papers_source ON papers(source_database);
CREATE INDEX idx_papers_title_trgm ON papers USING gin(title gin_trgm_ops);

-- Hypotheses
CREATE TABLE hypotheses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    evidence JSONB DEFAULT '[]',
    reasoning JSONB DEFAULT '{}',
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    generated_by VARCHAR(50), -- agent identifier
    status VARCHAR(50) DEFAULT 'draft',
    validation_results JSONB,
    user_feedback JSONB
);

CREATE INDEX idx_hypotheses_project ON hypotheses(project_id);
CREATE INDEX idx_hypotheses_confidence ON hypotheses(confidence_score DESC);
CREATE INDEX idx_hypotheses_status ON hypotheses(status);

-- Search History
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    filters JSONB DEFAULT '{}',
    results_count INTEGER,
    databases TEXT[],
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    cached BOOLEAN DEFAULT false
);

CREATE INDEX idx_search_history_user ON search_history(user_id);
CREATE INDEX idx_search_history_executed ON search_history(executed_at DESC);
```

### 4.2 Vector Database Schema (Qdrant)

```python
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct,
    CollectionInfo, OptimizersConfigDiff
)

class VectorSchemaManager:
    """
    Manages vector database collections and schemas
    """
    def __init__(self, client: QdrantClient):
        self.client = client
        self.collections = {
            "papers": {
                "size": 1536,  # OpenAI embedding dimension
                "distance": Distance.COSINE
            },
            "hypotheses": {
                "size": 1536,
                "distance": Distance.COSINE
            },
            "users": {
                "size": 768,  # User preference embedding
                "distance": Distance.EUCLID
            }
        }
    
    def initialize_collections(self):
        """Create all required collections"""
        for name, config in self.collections.items():
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=config["size"],
                    distance=config["distance"]
                ),
                optimizers_config=OptimizersConfigDiff(
                    indexing_threshold=20000,
                    memmap_threshold=50000
                ),
                shard_number=2
            )
    
    def add_paper_embedding(self, paper_id: str, embedding: List[float], metadata: dict):
        """Add paper embedding with metadata"""
        self.client.upsert(
            collection_name="papers",
            points=[
                PointStruct(
                    id=paper_id,
                    vector=embedding,
                    payload={
                        "title": metadata.get("title"),
                        "doi": metadata.get("doi"),
                        "authors": metadata.get("authors"),
                        "publication_date": metadata.get("publication_date"),
                        "abstract": metadata.get("abstract"),
                        "source": metadata.get("source_database")
                    }
                )
            ]
        )
    
    def semantic_search(self, collection: str, query_vector: List[float], limit: int = 10):
        """Perform semantic similarity search"""
        return self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
            score_threshold=0.7
        )
```

### 4.3 Cache Strategy (Redis)

```python
import redis
import json
from typing import Optional, Any
from datetime import timedelta

class CacheManager:
    """
    Centralized cache management with TTL strategies
    """
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl_config = {
            "search_results": timedelta(hours=24),
            "paper_metadata": timedelta(days=7),
            "user_session": timedelta(hours=2),
            "api_response": timedelta(minutes=15),
            "synthesis_result": timedelta(hours=1),
            "hypothesis": timedelta(hours=6)
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(self, key: str, value: Any, cache_type: str = "default"):
        """Set value in cache with appropriate TTL"""
        ttl = self.ttl_config.get(cache_type, timedelta(hours=1))
        self.redis.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)
    
    def get_or_set(self, key: str, func: callable, cache_type: str = "default"):
        """Get from cache or compute and set"""
        value = self.get(key)
        if value is None:
            value = func()
            self.set(key, value, cache_type)
        return value

# Cache key patterns
CACHE_KEYS = {
    "user_projects": "projects:user:{user_id}",
    "search_results": "search:{query_hash}:{db}",
    "paper_detail": "paper:{doi}",
    "hypothesis_list": "hypotheses:project:{project_id}",
    "synthesis": "synthesis:{project_id}:{paper_ids_hash}"
}
```

---

## 5. Interface Design

### 5.1 User Interface Design System

#### 5.1.1 Design Tokens

```scss
// Color Palette
$colors: (
  primary: (
    50: #eff6ff,
    100: #dbeafe,
    500: #3b82f6,
    600: #2563eb,
    700: #1d4ed8,
    900: #1e3a8a
  ),
  gray: (
    50: #f9fafb,
    100: #f3f4f6,
    500: #6b7280,
    700: #374151,
    900: #111827
  ),
  semantic: (
    success: #10b981,
    warning: #f59e0b,
    error: #ef4444,
    info: #3b82f6
  )
);

// Typography
$typography: (
  font-family: (
    sans: 'Inter, system-ui, sans-serif',
    mono: 'JetBrains Mono, monospace'
  ),
  font-size: (
    xs: 0.75rem,
    sm: 0.875rem,
    base: 1rem,
    lg: 1.125rem,
    xl: 1.25rem,
    '2xl': 1.5rem,
    '3xl': 1.875rem
  ),
  font-weight: (
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  )
);

// Spacing
$spacing: (
  0: 0,
  1: 0.25rem,
  2: 0.5rem,
  3: 0.75rem,
  4: 1rem,
  6: 1.5rem,
  8: 2rem,
  12: 3rem,
  16: 4rem
);

// Breakpoints
$breakpoints: (
  sm: 640px,
  md: 768px,
  lg: 1024px,
  xl: 1280px,
  '2xl': 1536px
);
```

#### 5.1.2 Component Library

```typescript
// Button Component
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  children,
  onClick
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
    ghost: 'text-gray-700 hover:bg-gray-100',
    danger: 'bg-red-600 text-white hover:bg-red-700'
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };
  
  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading && <Spinner className="mr-2" />}
      {icon && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};
```

### 5.2 Page Layouts

#### 5.2.1 Dashboard Layout

```typescript
// Dashboard Layout Component
const DashboardLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Logo />
              <Navigation />
            </div>
            <div className="flex items-center space-x-4">
              <SearchBar />
              <NotificationBell />
              <UserMenu />
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-sm">
          <nav className="px-4 py-6">
            <SidebarMenu />
          </nav>
        </aside>
        
        {/* Content Area */}
        <main className="flex-1 px-8 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
```

#### 5.2.2 Search Interface Mockup

```
┌──────────────────────────────────────────────────────────────┐
│  🔍 Search Literature                                   [?]  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Search Query:                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ machine learning in cancer diagnosis              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Databases:                                                 │
│  ☑ PubMed  ☑ arXiv  ☑ Semantic Scholar  ☐ CORE           │
│                                                              │
│  Filters:                                                   │
│  Date Range: [2020-2025 ▼]  Type: [All Types ▼]           │
│                                                              │
│  Advanced Options ▼                                         │
│                                                              │
│  [Search] [Save Search] [Clear]                            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Results (2,847 papers found)                Sort: [Relevance ▼]│
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 📄 Deep Learning Applications in Early Cancer...    │    │
│  │ Authors: Smith, J., Chen, L., et al.               │    │
│  │ Journal: Nature Medicine, 2023                     │    │
│  │ Relevance: 98%  Citations: 145                     │    │
│  │ [View] [Add to Project] [Export]                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 📄 AI-Powered Diagnostic Systems: A Review         │    │
│  │ Authors: Johnson, M., Williams, K.                 │    │
│  │ Journal: Medical AI Review, 2024                   │    │
│  │ Relevance: 95%  Citations: 89                      │    │
│  │ [View] [Add to Project] [Export]                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  [Previous] Page 1 of 285 [Next]                           │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 Responsive Design

```typescript
// Responsive Grid System
const ResponsiveGrid: React.FC = ({ children }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {children}
    </div>
  );
};

// Responsive Table
const ResponsiveTable: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <>
      {/* Desktop View */}
      <div className="hidden md:block">
        <table className="min-w-full divide-y divide-gray-200">
          {/* Table content */}
        </table>
      </div>
      
      {/* Mobile View */}
      <div className="block md:hidden">
        {data.map((item, index) => (
          <div key={index} className="bg-white p-4 mb-2 rounded-lg shadow">
            {/* Card-based layout for mobile */}
          </div>
        ))}
      </div>
    </>
  );
};
```

---

## 6. API Design

### 6.1 RESTful API Specification

#### 6.1.1 API Structure

```yaml
openapi: 3.0.0
info:
  title: HypothesisAI API
  version: 1.0.0
  description: RESTful API for HypothesisAI Research Platform

servers:
  - url: https://api.hypothesisai.com/v1
    description: Production server
  - url: https://staging-api.hypothesisai.com/v1
    description: Staging server

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  
  schemas:
    Project:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        description:
          type: string
        owner_id:
          type: string
          format: uuid
        created_at:
          type: string
          format: date-time
        papers:
          type: array
          items:
            $ref: '#/components/schemas/Paper'
    
    Paper:
      type: object
      properties:
        id:
          type: string
          format: uuid
        doi:
          type: string
        title:
          type: string
        abstract:
          type: string
        authors:
          type: array
          items:
            type: object
        publication_date:
          type: string
          format: date

paths:
  /auth/register:
    post:
      summary: Register new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  minLength: 8
                full_name:
                  type: string
      responses:
        '201':
          description: User created successfully
        '400':
          description: Invalid input
  
  /projects:
    get:
      summary: List user projects
      security:
        - bearerAuth: []
      parameters:
        - in: query
          name: page
          schema:
            type: integer
            default: 1
        - in: query
          name: limit
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: List of projects
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Project'
                  pagination:
                    type: object
    
    post:
      summary: Create new project
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                description:
                  type: string
      responses:
        '201':
          description: Project created
  
  /search:
    post:
      summary: Execute literature search
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                query:
                  type: string
                databases:
                  type: array
                  items:
                    type: string
                    enum: [arxiv, pubmed, semantic_scholar]
                filters:
                  type: object
                  properties:
                    date_from:
                      type: string
                      format: date
                    date_to:
                      type: string
                      format: date
                    publication_types:
                      type: array
                      items:
                        type: string
      responses:
        '200':
          description: Search results
        '202':
          description: Search queued for processing
```

### 6.2 GraphQL API

```graphql
# GraphQL Schema Definition
type Query {
  # User queries
  me: User!
  user(id: ID!): User
  
  # Project queries
  project(id: ID!): Project
  projects(
    filter: ProjectFilter
    pagination: PaginationInput
  ): ProjectConnection!
  
  # Search queries
  search(input: SearchInput!): SearchResult!
  searchHistory(limit: Int = 10): [SearchHistory!]!
  
  # Hypothesis queries
  hypothesis(id: ID!): Hypothesis
  hypotheses(projectId: ID!): [Hypothesis!]!
}

type Mutation {
  # Authentication
  register(input: RegisterInput!): AuthPayload!
  login(input: LoginInput!): AuthPayload!
  refreshToken(token: String!): AuthPayload!
  
  # Projects
  createProject(input: CreateProjectInput!): Project!
  updateProject(id: ID!, input: UpdateProjectInput!): Project!
  deleteProject(id: ID!): Boolean!
  
  # Papers
  addPaperToProject(projectId: ID!, paperId: ID!): Project!
  removePaperFromProject(projectId: ID!, paperId: ID!): Project!
  
  # Hypothesis
  generateHypothesis(input: GenerateHypothesisInput!): Hypothesis!
  validateHypothesis(id: ID!): ValidationResult!
}

type Subscription {
  # Real-time search updates
  searchProgress(searchId: ID!): SearchProgress!
  
  # Project collaboration
  projectUpdated(projectId: ID!): Project!
  
  # Agent status
  agentStatus(projectId: ID!): AgentStatus!
}

# Types
type User {
  id: ID!
  email: String!
  fullName: String
  profile: UserProfile
  projects: [Project!]!
  createdAt: DateTime!
}

type Project {
  id: ID!
  name: String!
  description: String
  owner: User!
  papers: [Paper!]!
  hypotheses: [Hypothesis!]!
  collaborators: [User!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Paper {
  id: ID!
  doi: String
  title: String!
  abstract: String
  authors: [Author!]!
  publicationDate: Date
  citations: Int
  embedding: [Float!]
}

type Hypothesis {
  id: ID!
  content: String!
  confidenceScore: Float!
  evidence: [Evidence!]!
  reasoning: String!
  status: HypothesisStatus!
  generatedAt: DateTime!
}

# Enums
enum HypothesisStatus {
  DRAFT
  PENDING_VALIDATION
  VALIDATED
  REJECTED
}

# Input Types
input SearchInput {
  query: String!
  databases: [DatabaseType!]!
  filters: SearchFilters
  limit: Int = 20
}

input SearchFilters {
  dateFrom: Date
  dateTo: Date
  publicationTypes: [String!]
  minCitations: Int
}
```

### 6.3 WebSocket Events

```typescript
// WebSocket Event Definitions
enum WebSocketEvent {
  // Connection Events
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  ERROR = 'error',
  
  // Search Events
  SEARCH_STARTED = 'search:started',
  SEARCH_PROGRESS = 'search:progress',
  SEARCH_COMPLETED = 'search:completed',
  SEARCH_FAILED = 'search:failed',
  
  // Agent Events
  AGENT_STARTED = 'agent:started',
  AGENT_PROGRESS = 'agent:progress',
  AGENT_COMPLETED = 'agent:completed',
  AGENT_ERROR = 'agent:error',
  
  // Collaboration Events
  PROJECT_UPDATED = 'project:updated',
  PAPER_ADDED = 'paper:added',
  COMMENT_ADDED = 'comment:added',
  USER_JOINED = 'user:joined',
  USER_LEFT = 'user:left'
}

// WebSocket Client Implementation
class WebSocketClient {
  private socket: Socket;
  private handlers: Map<string, Function[]>;
  
  constructor(url: string, token: string) {
    this.socket = io(url, {
      auth: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });
    
    this.handlers = new Map();
    this.setupEventListeners();
  }
  
  private setupEventListeners() {
    this.socket.on(WebSocketEvent.CONNECT, () => {
      console.log('WebSocket connected');
    });
    
    this.socket.on(WebSocketEvent.SEARCH_PROGRESS, (data) => {
      this.emit('searchProgress', data);
    });
  }
  
  public subscribe(event: string, handler: Function) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)?.push(handler);
  }
  
  public emit(event: string, data: any) {
    this.handlers.get(event)?.forEach(handler => handler(data));
  }
  
  public joinProject(projectId: string) {
    this.socket.emit('join:project', { projectId });
  }
  
  public leaveProject(projectId: string) {
    this.socket.emit('leave:project', { projectId });
  }
}
```

---

## 7. Security Architecture

### 7.1 Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                         WAF Layer                           │
│              CloudFlare / AWS WAF / ModSecurity            │
├─────────────────────────────────────────────────────────────┤
│                      API Gateway Layer                      │
│         Rate Limiting │ DDoS Protection │ IP Filtering     │
├─────────────────────────────────────────────────────────────┤
│                   Authentication Layer                      │
│           JWT │ OAuth 2.0 │ 2FA │ Session Management      │
├─────────────────────────────────────────────────────────────┤
│                    Authorization Layer                      │
│              RBAC │ Resource Permissions │ Scopes          │
├─────────────────────────────────────────────────────────────┤
│                     Application Layer                       │
│      Input Validation │ CSRF Protection │ XSS Prevention   │
├─────────────────────────────────────────────────────────────┤
│                        Data Layer                           │
│    Encryption at Rest │ Field-level Encryption │ Masking   │
├─────────────────────────────────────────────────────────────┤
│                      Network Layer                          │
│          TLS 1.3 │ VPC │ Private Subnets │ Firewalls     │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Authentication & Authorization

```python
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your-secret-key"  # Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []

class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: str = "user"
    permissions: list[str] = []

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# RBAC Implementation
class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self):
        self.roles = {
            "admin": ["*"],  # All permissions
            "researcher": [
                "project:create", "project:read", "project:update", "project:delete",
                "search:execute", "hypothesis:generate", "synthesis:create"
            ],
            "viewer": ["project:read", "search:execute"],
            "guest": ["search:execute"]
        }
    
    def check_permission(self, user: User, resource: str, action: str) -> bool:
        permission = f"{resource}:{action}"
        user_permissions = self.roles.get(user.role, [])
        
        if "*" in user_permissions:
            return True
        
        return permission in user_permissions
    
    def require_permission(self, resource: str, action: str):
        def permission_checker(current_user: User = Depends(get_current_user)):
            if not self.check_permission(current_user, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return permission_checker

rbac = RBACManager()
```

### 7.3 Data Security

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64

class DataEncryption:
    """Field-level encryption for sensitive data"""
    
    def __init__(self, master_key: str):
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt',  # Use proper salt management
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt_field(self, data: str) -> str:
        """Encrypt sensitive field"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt sensitive field"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_pii(self, data: dict) -> dict:
        """Encrypt PII fields in dictionary"""
        pii_fields = ['ssn', 'credit_card', 'bank_account']
        encrypted_data = data.copy()
        
        for field in pii_fields:
            if field in encrypted_data:
                encrypted_data[field] = self.encrypt_field(encrypted_data[field])
        
        return encrypted_data

# Data Masking
class DataMasking:
    """Mask sensitive data for non-production environments"""
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email address"""
        parts = email.split('@')
        if len(parts) != 2:
            return email
        
        username = parts[0]
        if len(username) > 2:
            masked = username[0] + '*' * (len(username) - 2) + username[-1]
        else:
            masked = '*' * len(username)
        
        return f"{masked}@{parts[1]}"
    
    @staticmethod
    def mask_doi(doi: str) -> str:
        """Partially mask DOI"""
        if len(doi) > 10:
            return doi[:5] + '*' * (len(doi) - 10) + doi[-5:]
        return doi
```

---

## 8. Infrastructure Design

### 8.1 Kubernetes Architecture

```yaml
# Kubernetes Deployment Configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hypothesisai-api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hypothesisai-api
  template:
    metadata:
      labels:
        app: hypothesisai-api
    spec:
      containers:
      - name: api
        image: hypothesisai/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: hypothesisai-api-service
  namespace: production
spec:
  selector:
    app: hypothesisai-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hypothesisai-api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hypothesisai-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 8.2 CI/CD Pipeline

```yaml
# GitHub Actions CI/CD Pipeline
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check .
        mypy .
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml --cov-report=html
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Security scan
      run: |
        pip install safety
        safety check
        bandit -r app/
  
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to DockerHub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          hypothesisai/api:latest
          hypothesisai/api:${{ github.sha }}
        cache-from: type=registry,ref=hypothesisai/api:buildcache
        cache-to: type=registry,ref=hypothesisai/api:buildcache,mode=max
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v4
      with:
        manifests: |
          k8s/deployment.yaml
          k8s/service.yaml
        images: |
          hypothesisai/api:${{ github.sha }}
```

### 8.3 Monitoring and Observability

```python
# Prometheus Metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
import time

# Metrics definitions
request_count = Counter(
    'hypothesisai_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'hypothesisai_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

active_users = Gauge(
    'hypothesisai_active_users',
    'Number of active users'
)

search_queries = Counter(
    'hypothesisai_search_queries_total',
    'Total number of search queries',
    ['database', 'status']
)

hypothesis_generated = Counter(
    'hypothesisai_hypotheses_generated_total',
    'Total number of hypotheses generated'
)

# Metrics decorator
def track_metrics(endpoint: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = 'success'
            except Exception as e:
                status = 'error'
                raise e
            finally:
                duration = time.time() - start_time
                request_count.labels(
                    method='POST',
                    endpoint=endpoint,
                    status=status
                ).inc()
                request_duration.labels(
                    method='POST',
                    endpoint=endpoint
                ).observe(duration)
            
            return result
        return wrapper
    return decorator

# Logging Configuration
import logging
import json
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'hypothesisai'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['version'] = os.getenv('VERSION', '1.0.0')

# Configure structured logging
def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = CustomJsonFormatter()
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    return logger

logger = setup_logging()
```

### 8.4 Disaster Recovery Plan

```yaml
# Backup and Recovery Configuration
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: production
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:14
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            command:
            - /bin/bash
            - -c
            - |
              DATE=$(date +%Y%m%d_%H%M%S)
              pg_dump -h postgres-service -U postgres hypothesisai > /backup/hypothesisai_$DATE.sql
              aws s3 cp /backup/hypothesisai_$DATE.sql s3://hypothesisai-backups/postgres/
              # Keep only last 30 days of backups
              find /backup -type f -mtime +30 -delete
            volumeMounts:
            - name: backup
              mountPath: /backup
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

---

## 9. Design Decisions and Rationale

### 9.1 Architectural Decisions

| Decision | Choice | Rationale | Alternatives Considered |
|----------|--------|-----------|------------------------|
| **Architecture Pattern** | Microservices | Scalability, independent deployment, team autonomy | Monolith, Serverless |
| **Agent Framework** | LangGraph | State management, multi-agent support, production-ready | AutoGen, CrewAI, Custom |
| **Database** | PostgreSQL + Qdrant | Relational + Vector needs, open source, proven | MongoDB, Pinecone |
| **Cache** | Redis | Performance, pub/sub support, widespread adoption | Memcached, Hazelcast |
| **Message Queue** | Celery + Redis | Python ecosystem, simple setup, reliable | RabbitMQ, Kafka |
| **Frontend Framework** | React + TypeScript | Type safety, ecosystem, developer availability | Vue, Angular, Svelte |
| **API Design** | REST + GraphQL | REST for simplicity, GraphQL for complex queries | REST only, gRPC |
| **Container Orchestration** | Kubernetes | Industry standard, cloud-agnostic, scalability | Docker Swarm, ECS |
| **Monitoring** | Prometheus + Grafana | Open source, powerful, Kubernetes native | DataDog, New Relic |

### 9.2 Technology Trade-offs

#### 9.2.1 LangGraph vs Custom Agent System

**Chosen: LangGraph**

Pros:
- Built-in state management
- Production-ready features
- Active development and support
- Extensive documentation

Cons:
- Framework lock-in
- Learning curve
- Limited customization

**Rationale:** Time-to-market and reliability outweigh customization limitations.

#### 9.2.2 PostgreSQL vs NoSQL

**Chosen: PostgreSQL**

Pros:
- ACID compliance
- Complex queries support
- JSON support for flexibility
- Mature ecosystem

Cons:
- Vertical scaling limitations
- Schema migrations complexity

**Rationale:** Research data requires strong consistency and complex relationships.

### 9.3 Design Patterns Applied

| Pattern | Application | Benefits |
|---------|-------------|----------|
| **Repository Pattern** | Data access layer | Abstraction, testability, flexibility |
| **Service Layer** | Business logic | Separation of concerns, reusability |
| **Factory Pattern** | Agent creation | Flexible instantiation, configuration |
| **Observer Pattern** | Event system | Loose coupling, extensibility |
| **Circuit Breaker** | External APIs | Fault tolerance, graceful degradation |
| **Saga Pattern** | Distributed transactions | Consistency, rollback capability |
| **CQRS** | Read/write separation | Performance, scalability |
| **Adapter Pattern** | Database integrations | Flexibility, maintainability |

### 9.4 Performance Optimization Strategies

```python
# Performance Optimization Examples

# 1. Database Query Optimization
class OptimizedQueryBuilder:
    @staticmethod
    def get_papers_with_citations(project_id: str, db: Session):
        """Optimized query with eager loading"""
        return (
            db.query(Paper)
            .filter(Paper.project_id == project_id)
            .options(
                joinedload(Paper.citations),
                joinedload(Paper.authors),
                selectinload(Paper.annotations)
            )
            .order_by(Paper.citation_count.desc())
            .limit(100)
            .all()
        )

# 2. Caching Strategy
class CachingStrategy:
    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.cache_times = {
            'paper_detail': 86400,  # 24 hours
            'search_results': 3600,  # 1 hour
            'user_profile': 300,     # 5 minutes
            'hypothesis': 1800       # 30 minutes
        }
    
    def cache_with_strategy(self, key: str, data: Any, cache_type: str):
        ttl = self.cache_times.get(cache_type, 3600)
        self.cache.setex(key, ttl, json.dumps(data))

# 3. Batch Processing
class BatchProcessor:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def process_papers(self, papers: List[Paper]):
        """Process papers in batches for efficiency"""
        for i in range(0, len(papers), self.batch_size):
            batch = papers[i:i + self.batch_size]
            await self.process_batch(batch)
    
    async def process_batch(self, batch: List[Paper]):
        # Process batch with concurrent tasks
        tasks = [self.process_single(paper) for paper in batch]
        await asyncio.gather(*tasks)

# 4. Connection Pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### 9.5 Scalability Considerations

```yaml
# Horizontal Scaling Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: scaling-config
data:
  scaling_rules.yaml: |
    services:
      api:
        min_replicas: 3
        max_replicas: 20
        cpu_threshold: 70
        memory_threshold: 80
        scale_up_rate: 2
        scale_down_rate: 1
      
      agent_orchestrator:
        min_replicas: 2
        max_replicas: 10
        queue_length_threshold: 100
        processing_time_threshold: 30
      
      literature_hunter:
        min_replicas: 2
        max_replicas: 15
        concurrent_searches: 50
      
      hypothesis_generator:
        min_replicas: 1
        max_replicas: 5
        gpu_enabled: true
        gpu_utilization_threshold: 80
```

---

## 10. Appendices

### Appendix A: Database Index Strategy

```sql
-- Performance-critical indexes
CREATE INDEX CONCURRENTLY idx_papers_embedding ON papers USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX CONCURRENTLY idx_papers_fulltext ON papers USING gin(to_tsvector('english', title || ' ' || abstract));
CREATE INDEX CONCURRENTLY idx_projects_user_status ON projects(owner_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_hypotheses_confidence ON hypotheses(confidence_score DESC) WHERE status = 'validated';
CREATE INDEX CONCURRENTLY idx_search_history_user_date ON search_history(user_id, executed_at DESC);

-- Partial indexes for common queries
CREATE INDEX CONCURRENTLY idx_papers_recent ON papers(publication_date DESC) 
WHERE publication_date > CURRENT_DATE - INTERVAL '2 years';

CREATE INDEX CONCURRENTLY idx_projects_public ON projects(created_at DESC) 
WHERE is_public = true;

-- Composite indexes for complex queries
CREATE INDEX CONCURRENTLY idx_paper_project_composite ON project_papers(project_id, paper_id, added_at DESC);
```

### Appendix B: Error Handling Strategy

```python
from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException

class ErrorCode(Enum):
    # Client errors (4xx)
    INVALID_INPUT = "INVALID_INPUT"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"

class ApplicationError(Exception):
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ErrorHandler:
    @staticmethod
    def handle_error(error: Exception) -> HTTPException:
        if isinstance(error, ApplicationError):
            return HTTPException(
                status_code=error.status_code,
                detail={
                    "error_code": error.error_code.value,
                    "message": error.message,
                    "details": error.details
                }
            )
        
        # Log unexpected errors
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        
        return HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "message": "An unexpected error occurred"
            }
        )

# Usage example
def get_paper(paper_id: str) -> Paper:
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise ApplicationError(
            error_code=ErrorCode.NOT_FOUND,
            message=f"Paper with ID {paper_id} not found",
            status_code=404,
            details={"paper_id": paper_id}
        )
    return paper
```

### Appendix C: Testing Strategy

```python
# Testing Framework Configuration
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test Database Setup
@pytest.fixture(scope="session")
def test_db():
    engine = create_engine("postgresql://test_user:test_pass@localhost/test_hypothesisai")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

# Integration Test Example
class TestSearchAPI:
    def test_search_papers(self, client: TestClient, test_db):
        """Test paper search functionality"""
        # Arrange
        search_params = {
            "query": "machine learning",
            "databases": ["arxiv", "pubmed"],
            "filters": {
                "date_from": "2023-01-01",
                "date_to": "2024-12-31"
            }
        }
        
        # Act
        response = client.post("/api/v1/search", json=search_params)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        assert all(
            "machine learning" in paper["title"].lower() or 
            "machine learning" in paper["abstract"].lower()
            for paper in data["results"]
        )

# Unit Test Example
class TestHypothesisGenerator:
    def test_confidence_score_calculation(self):
        """Test confidence score calculation logic"""
        generator = HypothesisGenerator()
        
        evidence = [
            {"source": "paper1", "strength": 0.9},
            {"source": "paper2", "strength": 0.7},
            {"source": "paper3", "strength": 0.8}
        ]
        
        score = generator.calculate_confidence(evidence)
        
        assert 0 <= score <= 1
        assert score == pytest.approx(0.8, rel=0.1)

# Performance Test Example
class TestPerformance:
    @pytest.mark.performance
    def test_search_response_time(self, client: TestClient):
        """Test search API response time"""
        import time
        
        search_params = {"query": "test", "databases": ["arxiv"]}
        
        start_time = time.time()
        response = client.post("/api/v1/search", json=search_params)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Must respond within 2 seconds
```

### Appendix D: Deployment Checklist

```markdown
## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage > 80%
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks met
- [ ] Documentation updated

### Security
- [ ] Secrets management configured
- [ ] SSL certificates installed
- [ ] WAF rules configured
- [ ] Security headers implemented
- [ ] CORS properly configured
- [ ] Rate limiting enabled

### Infrastructure
- [ ] Database migrations tested
- [ ] Backup strategy verified
- [ ] Monitoring dashboards created
- [ ] Alerts configured
- [ ] Log aggregation working
- [ ] Auto-scaling tested

### Application
- [ ] Feature flags configured
- [ ] Environment variables set
- [ ] Health checks passing
- [ ] Rollback plan documented
- [ ] API documentation published

### Business
- [ ] Stakeholder approval obtained
- [ ] User communication sent
- [ ] Support team briefed
- [ ] Analytics tracking verified
- [ ] SLA requirements met
```

### Appendix E: API Rate Limiting Configuration

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
import time
from typing import Dict, Tuple

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.limits = {
            'anonymous': (10, 60),      # 10 requests per minute
            'free': (100, 60),          # 100 requests per minute
            'pro': (1000, 60),          # 1000 requests per minute
            'enterprise': (10000, 60)    # 10000 requests per minute
        }
    
    def check_rate_limit(self, key: str, tier: str = 'free') -> Tuple[bool, Dict]:
        limit, window = self.limits.get(tier, self.limits['free'])
        
        pipe = self.redis.pipeline()
        now = time.time()
        window_start = now - window
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Count requests in window
        pipe.zcard(key)
        # Set expiry
        pipe.expire(key, window)
        
        results = pipe.execute()
        request_count = results[2]
        
        if request_count > limit:
            return False, {
                'limit': limit,
                'window': window,
                'retry_after': window
            }
        
        return True, {
            'limit': limit,
            'remaining': limit - request_count,
            'reset': int(now + window)
        }
    
    async def __call__(self, request: Request):
        # Get user tier from JWT or default to 'free'
        user = getattr(request.state, 'user', None)
        tier = user.subscription_tier if user else 'anonymous'
        
        # Create rate limit key
        client_id = user.id if user else request.client.host
        key = f"rate_limit:{tier}:{client_id}"
        
        # Check rate limit
        allowed, info = self.check_rate_limit(key, tier)
        
        # Set rate limit headers
        request.state.rate_limit_info = info
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    'X-RateLimit-Limit': str(info['limit']),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(info['reset']),
                    'Retry-After': str(info['retry_after'])
                }
            )
```

---

## Document Approval

**Design Document Approval:**

| Role | Name | Signature | Date | Comments |
|------|------|-----------|------|----------|
| System Architect | | | | |
| Technical Lead | | | | |
| Frontend Lead | | | | |
| Backend Lead | | | | |
| DevOps Lead | | | | |
| Security Officer | | | | |
| Product Manager | | | | |

---

## Document Control

- **Version:** 1.0
- **Status:** Draft for Review
- **Classification:** Confidential
- **Distribution:** Development Team, Architects, Technical Stakeholders
- **Review Cycle:** Sprint-based updates
- **Next Review:** [Start of implementation phase]
- **Owner:** System Architect / Technical Lead

---

*This System Design Document represents the complete technical blueprint for the HypothesisAI platform. It should be maintained as a living document throughout the development lifecycle, with updates reflecting design decisions and architectural evolution.*