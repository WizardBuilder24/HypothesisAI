# HypothesisAI

A multi-agent scientific research automation platform that accelerates hypothesis generation and validation through AI-powered literature analysis.

## Overview

HypothesisAI uses a coordinated system of 5 specialized AI agents to automate the research process:

- **� Literature Hunter**: Searches and retrieves relevant papers from arXiv
- **🧠 Knowledge Synthesizer**: Analyzes papers to identify patterns and gaps
- **💡 Hypothesis Generator**: Creates novel, testable research hypotheses
- **🔬 Validator**: Assesses hypothesis validity and feasibility
- **🎯 Supervisor**: Orchestrates the entire workflow

## Agent Architecture

HypothesisAI implements a **hub-and-spoke architecture** with a central supervisor agent coordinating four specialized research agents. This design ensures intelligent workflow orchestration while maintaining clear separation of concerns.

### Supervisor Agent (Central Orchestrator)

The supervisor agent acts as the **intelligent router** that:

- **Analyzes current workflow state** to determine the next optimal step
- **Routes control flow** between specialized agents based on research progress
- **Manages error recovery** when agents encounter failures or incomplete results
- **Tracks research quality** and determines when sufficient information has been gathered
- **Orchestrates iterative refinement** by cycling agents when deeper analysis is needed

**Decision Logic:**
```python
# Supervisor routing decisions based on workflow state
if no_papers_found:
    route_to → Literature Hunter
elif papers_need_synthesis:
    route_to → Synthesizer  
elif synthesis_complete_no_hypotheses:
    route_to → Hypothesis Generator
elif hypotheses_need_validation:
    route_to → Validator
elif research_incomplete:
    route_to → Literature Hunter (follow-up search)
else:
    route_to → END (generate final report)
```

### Specialized Agents

#### 🔍 Literature Hunter Agent
- **Purpose**: Multi-strategy paper discovery and retrieval
- **Capabilities**:
  - Generates 2-4 complementary arXiv search strategies
  - Executes parallel searches to maximize paper coverage
  - Ranks papers by relevance and recency scores
  - Handles API rate limiting and error recovery
- **Output**: Curated list of high-quality research papers with metadata

#### 🧠 Knowledge Synthesizer Agent  
- **Purpose**: Pattern recognition and gap analysis across papers
- **Capabilities**:
  - Identifies recurring themes and methodological patterns
  - Extracts key findings and contradictory results
  - Maps research landscape and identifies understudied areas
  - Synthesizes complex relationships between studies
- **Output**: Structured synthesis with patterns, findings, and research gaps

#### 💡 Hypothesis Generator Agent
- **Purpose**: Novel hypothesis creation based on synthesis
- **Capabilities**:
  - Generates testable, novel research hypotheses
  - Ensures hypotheses are grounded in identified patterns/gaps
  - Specifies required data and experimental approaches
  - Prioritizes hypotheses by potential impact and feasibility
- **Output**: Ranked list of novel, testable hypotheses with supporting rationale

#### 🔬 Validator Agent
- **Purpose**: Hypothesis assessment and feasibility analysis
- **Capabilities**:
  - Evaluates logical consistency and methodological soundness
  - Assesses experimental feasibility and resource requirements
  - Identifies supporting evidence from literature corpus
  - Assigns confidence scores and risk assessments
- **Output**: Validation scores with detailed reasoning and evidence links

### Workflow Orchestration

The system uses **LangGraph's state machine** to manage the research workflow:

#### 1. State Management
```python
class ResearchState:
    query: str                    # Original research question
    papers: List[Paper]          # Retrieved papers
    synthesis: Optional[dict]     # Synthesis results
    hypotheses: List[dict]       # Generated hypotheses
    validation_results: List[dict] # Validation outcomes
    current_stage: str           # Workflow position
    follow_up_queries: List[str] # Additional searches needed
```

#### 2. Conditional Routing
The supervisor uses **conditional edges** to make intelligent routing decisions:

```python
# Workflow transitions based on state analysis
START → Literature Hunter → Synthesizer → Hypothesis Generator → Validator → END
     ↘                    ↗              ↘                    ↗
       Literature Hunter (follow-up)      Validator (re-check)
```

#### 3. Iterative Refinement
- **Quality Gates**: Each agent validates output quality before proceeding
- **Follow-up Searches**: Supervisor triggers additional literature searches for gaps
- **Hypothesis Refinement**: Low-confidence hypotheses trigger deeper analysis
- **Error Recovery**: Failed API calls or poor results trigger alternative strategies

### Key Benefits of This Architecture

1. **Modularity**: Each agent has a single, well-defined responsibility
2. **Scalability**: New agents can be added without modifying existing ones
3. **Reliability**: Supervisor handles failures and ensures workflow completion
4. **Transparency**: Every routing decision is logged with clear reasoning
5. **Flexibility**: Workflow adapts based on research complexity and quality requirements

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/WizardBuilder24/HypothesisAI.git
   cd HypothesisAI
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```
   # Required: At least one LLM provider
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   GEMINI_API_KEY=your_gemini_key_here
   
   # Optional: Database (defaults to SQLite)
   DATABASE_URL=postgresql://user:password@localhost/hypothesisai
   REDIS_URL=redis://localhost:6379
   ```

### Usage

Run the research CLI with a research question:

```bash
cd backend
python examples/cli_research.py "How can quantum computing improve drug discovery?"
```

**Options:**
```bash
# Specify maximum papers to analyze
python examples/cli_research.py "machine learning for healthcare" --max-papers 15

# Use verbose output for detailed logging
python examples/cli_research.py "CRISPR gene editing" --verbose

# Specify LLM provider
python examples/cli_research.py "climate change mitigation" --llm-provider openai

# Save results to file
python examples/cli_research.py "renewable energy storage" --output results.json
```

### Example Output

The system will:
1. Generate optimized search strategies for your research question
2. Search arXiv for relevant papers using multiple approaches
3. Synthesize findings to identify patterns and research gaps
4. Generate novel, testable hypotheses
5. Validate each hypothesis for feasibility and significance

## Features

- **Multi-Strategy Search**: Uses multiple complementary search strategies to maximize paper discovery
- **Real-time Processing**: Live progress updates during research workflow
- **Flexible LLM Support**: Works with OpenAI GPT, Anthropic Claude, or Google Gemini
- **Comprehensive Analysis**: Analyzes papers for patterns, gaps, and research opportunities
- **Quality Ranking**: Ranks papers and hypotheses by relevance and quality scores
- **Export Options**: Save results in JSON, Markdown, or plain text formats

## Architecture

Built on LangGraph for robust multi-agent orchestration:

- **Supervisor Agent**: Makes intelligent routing decisions
- **Stateful Workflow**: Maintains research context across all agents
- **Error Recovery**: Graceful handling of API failures and edge cases
- **Rate Limiting**: Respects API quotas and rate limits
- **Audit Trail**: Complete logging of all agent interactions

## Configuration

The system supports extensive configuration through environment variables and CLI options:

- **LLM Providers**: OpenAI, Anthropic, Google (configurable per agent)
- **Search Parameters**: Paper limits, search strategies, quality thresholds
- **Temperature Settings**: Creativity levels for different research phases
- **Output Formats**: JSON, Markdown, plain text
- **Logging Levels**: Debug, info, warning, error

## Development Status

🚧 **Active Development** 🚧

HypothesisAI is an actively evolving project with exciting enhancements planned for the coming weeks. We're continuously improving the platform to make it more robust and capable.

### Upcoming Releases

**🔗 Knowledge Graph Integration**
- Advanced relationship mapping between papers, concepts, and hypotheses
- Visual knowledge representation for better insight discovery
- Graph-based reasoning for more sophisticated hypothesis generation

**🎯 Prompt Optimization Strategies**
- Dynamic prompt adaptation based on research domain
- Advanced prompt engineering techniques for higher quality outputs
- Context-aware prompt selection for improved agent performance

**📈 Enhanced Analytics**
- Deeper research impact scoring and metrics
- Advanced pattern recognition algorithms
- Improved validation criteria and confidence scoring

Stay tuned for regular updates as we continue to push the boundaries of AI-powered research automation!

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

**Built with LangGraph, LangChain, and FastAPI**