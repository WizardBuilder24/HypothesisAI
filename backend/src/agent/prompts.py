"""Prompt templates for HypothesisAI agents.

Provides PromptTemplate wrapper that auto-injects current_date and current_data
into format calls for consistent prompt context across all agents.
"""

from datetime import datetime
import json
from typing import Any, Dict


def get_current_date() -> str:
  """Get current date in readable format."""
  return datetime.now().strftime("%B %d, %Y")


class PromptTemplate:
  """Prompt wrapper that auto-injects common fields like current_date."""

  def __init__(self, template: str):
    self.template = template

  def _serialize_current_data(self, context: Dict[str, Any]) -> str:
    """Serialize formatting context as JSON string."""
    try:
      return json.dumps(context, default=str, indent=2)
    except Exception:
      return str(context)

  def format(self, *args, **kwargs) -> str:
    merged: Dict[str, Any] = dict(kwargs)

    # Auto-inject current_date and current_data if not provided
    if "current_date" not in merged:
      merged["current_date"] = get_current_date()
    if "current_data" not in merged:
      merged["current_data"] = self._serialize_current_data(merged)

    return self.template.format(*args, **merged)


# Supervisor Prompts

supervisor_routing_prompt = PromptTemplate("""Analyze current state and choose the next agent.

Research Query: {query}

STATE SUMMARY:
- Papers Found: {papers_count}
- Synthesis Present: {has_synthesis}
- Hypotheses Present: {has_hypotheses}
- Validation Present: {has_validation}
- Error Count: {error_count}
- Iteration: {iteration}
- Status Summary: {status_summary}

ROUTING RULES:
- If no papers or papers < 5 → route to "literature_hunter"
- If papers ≥ 5 but no synthesis → route to "synthesizer"
- If synthesis done but no hypotheses → route to "hypothesis_generator"
- If hypotheses exist but no validation → route to "validator"
- If validation complete or iteration > 10 → route to "end"

Return JSON: {next_agent, should_continue, reasoning}
""")


# Literature Search Prompts

literature_search_prompt = PromptTemplate("""Create arXiv search strategies for finding relevant papers.

Current Date: {current_date}
Research Query: {query}
Maximum Papers per Search: {max_papers}

Generate 2-4 search strategies that cover the research topic comprehensively.

arXiv Search Tips:
- Use boolean operators (AND, OR, NOT)
- Field searches: ti: (title), abs: (abstract), au: (author), cat: (category)
- Use quotes for exact phrases

Return JSON with:
- "search_strategies": list of {query, focus, expected_paper_types, priority}
- "rationale": explanation of multi-strategy approach
- "coverage_analysis": how strategies complement each other""")


# Synthesis Prompts

synthesis_prompt = PromptTemplate("""Analyze research papers and synthesize patterns, findings, and gaps.

Current Date: {current_date}
Number of Papers: {num_papers}

PAPERS TO ANALYZE:
{papers_summary}

Identify:
- 3-5 major patterns across papers
- 5-7 key findings
- 3-5 research gaps
- Any contradictions

Return JSON with:
- "patterns": list of {description, paper_ids, confidence}
- "key_findings": list of strings
- "research_gaps": list of strings  
- "total_papers_analyzed": number

Provide comprehensive synthesis of the research landscape.""")


# Hypothesis Generation Prompts

hypothesis_generation_prompt = PromptTemplate("""Generate novel research hypotheses based on the synthesis.

Current Date: {current_date}
Target: Generate {num_hypotheses} hypotheses

SYNTHESIS:
{synthesis}

Each hypothesis should be:
- Novel: not directly stated in existing research
- Testable: can be validated experimentally
- Specific: clearly defined relationships
- Grounded: based on identified patterns and gaps

Return JSON with:
- "hypotheses": list of {id, text, rationale, required_data, potential_experiments, expected_outcomes}
""")


# Validation Prompts

validation_prompt = PromptTemplate("""Validate the hypothesis: {hypothesis}

Current Date: {current_date}

Assess:
- Logical consistency
- Methodological soundness
- Feasibility of testing
- Supporting evidence

Return JSON with:
- "confidence_score" (0.0 to 1.0)
- "reasoning" (text)
- "supporting_papers" (list of paper ids)
""")


# Reflection Prompts

reflection_instructions = PromptTemplate("""Analyze current research state and identify knowledge gaps.

Current Date: {current_date}
Research Topic: {research_topic}

CURRENT FINDINGS:
{current_summary}

Assess:
- If current information is sufficient
- Critical knowledge gaps
- Follow-up queries needed

Return JSON with:
- "is_sufficient": true/false
- "knowledge_gap": description (empty if sufficient)
- "follow_up_queries": list (empty if sufficient)
""")


# Final Answer Prompts

answer_instructions = PromptTemplate("""Generate a comprehensive research report.

Current Date: {current_date}
Research Query: {research_topic}

RESEARCH RESULTS:
Papers Analyzed: {papers_count}
Key Findings: {key_findings}
Hypotheses Generated: {hypotheses}
Validation Results: {validation_summary}

Include:
- Comprehensive answer to the original query
- Key findings and validated hypotheses
- Important limitations
- Future research directions
- Use markdown formatting
""")