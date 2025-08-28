"""Prompt templates for HypothesisAI agents.

This module exposes prompt templates as PromptTemplate objects. The
PromptTemplate implements a `format(...)` method that mirrors the
behaviour of Python `str.format` but auto-injects `current_date` and
`current_data` into the formatting context if they are not provided.

This keeps call sites like `supervisor_routing_prompt.format(...)`
working as before while ensuring `current_data` is embedded.
"""

from datetime import datetime
import json
from typing import Any, Dict


def get_current_date() -> str:
  """Get current date in readable format."""
  return datetime.now().strftime("%B %d, %Y")


class PromptTemplate:
  """Lightweight prompt wrapper that auto-injects common fields.

  Usage:
    prompt = PromptTemplate("Hello {name}, date {current_date}")
    prompt.format(name="Vivek")  # current_date will be injected
  """

  def __init__(self, template: str):
    self.template = template

  def _serialize_current_data(self, context: Dict[str, Any]) -> str:
    """Serialize the provided formatting context as a readable string.

    We default to a pretty-printed JSON representation. Fall back to
    str() if JSON serialization fails.
    """
    try:
      return json.dumps(context, default=str, indent=2)
    except Exception:
      return str(context)

  def format(self, *args, **kwargs) -> str:
    # Start from a copy so we don't mutate caller's dict
    merged: Dict[str, Any] = dict(kwargs)

    # Inject dynamic current_date if not provided
    if "current_date" not in merged:
      merged["current_date"] = get_current_date()

    # Inject current_data as a serialization of the provided context
    # if not explicitly supplied by the caller.
    if "current_data" not in merged:
      merged["current_data"] = self._serialize_current_data(merged)

    return self.template.format(*args, **merged)


# Backwards-compatible helper so other modules can import the raw string
# if needed: prompt.template contains the original string.


# ============================================================================
# SUPERVISOR PROMPTS
# ============================================================================

supervisor_routing_prompt = PromptTemplate("""You are the research workflow supervisor. Analyze the provided state summary and choose the next agent.

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

Return a JSON object with keys: next_agent (one of ["literature_hunter","synthesizer","hypothesis_generator","validator","end"]), should_continue (true/false), and reasoning (short explanation).
""")


# ============================================================================
# LITERATURE SEARCH PROMPTS
# ============================================================================

literature_search_prompt = PromptTemplate("""Generate optimized arXiv search strategies for finding the most relevant, recent, and high-quality papers.

Current Date: {current_date}
Research Query: {query}
Maximum Papers per Search: {max_papers}

TASK: Analyze the research query and create 2-4 complementary search strategies that will comprehensively cover the research topic.

ARXIV SEARCH STRATEGY:
- arXiv supports boolean operators (AND, OR, NOT)
- Field-specific searches: ti: (title), abs: (abstract), au: (author), cat: (category)
- Use quotes for exact phrases
- Recent papers are often more valuable (consider recency bias)
- Popular/cited papers indicate importance
- Combine broad and specific terms for comprehensive coverage

SEARCH STRATEGY EXAMPLES:
For "machine learning healthcare": 
- Strategy 1: ti:"machine learning" AND abs:healthcare AND abs:medical
- Strategy 2: abs:"deep learning" AND (abs:diagnosis OR abs:treatment OR abs:clinical)
- Strategy 3: cat:cs.LG AND (abs:biomedical OR abs:radiology OR abs:pathology)

For "quantum computing cryptography":
- Strategy 1: ti:quantum AND abs:cryptography AND abs:security
- Strategy 2: abs:"quantum algorithm" AND (abs:encryption OR abs:decryption)
- Strategy 3: cat:quant-ph AND abs:cryptographic

Format your response as a JSON object with:
- "search_strategies": list of strategy objects, each containing:
  - "query": the arXiv search query string (optimized for arXiv API)
  - "focus": brief description of what this strategy targets
  - "expected_paper_types": types of papers this query should find
  - "priority": integer 1-3 (1=highest priority, 3=exploratory)
- "rationale": overall explanation of the multi-strategy approach
- "coverage_analysis": how these strategies complement each other

Generate 2-4 diverse strategies that together will find the most relevant, recent, and comprehensive set of papers.""")


# ============================================================================
# SYNTHESIS PROMPTS
# ============================================================================

synthesis_prompt = PromptTemplate("""Analyze the research papers and synthesize patterns, findings, and gaps.

Current Date: {current_date}
Number of Papers: {num_papers}

PAPERS TO ANALYZE:
{papers_summary}

Instructions:
- Identify 3-5 major patterns across papers
- Extract 5-7 key findings
- Identify 3-5 research gaps
- Note any contradictions

Format your response as a JSON object with these keys:
- "patterns": list of pattern objects containing:
  - "description": clear pattern description
  - "paper_ids": list of supporting paper IDs
  - "confidence": confidence score (0.0 to 1.0)
- "key_findings": list of key finding strings
- "research_gaps": list of research gap strings
- "total_papers_analyzed": number analyzed

Provide comprehensive synthesis of the research landscape.""")


# ============================================================================
# HYPOTHESIS GENERATION PROMPTS
# ============================================================================

hypothesis_generation_prompt = PromptTemplate("""Generate novel research hypotheses based on the synthesis.

Current Date: {current_date}
Target: Generate {num_hypotheses} hypotheses

SYNTHESIS:
{synthesis}

Requirements for each hypothesis:
- Novel: not directly stated in existing research
- Testable: can be validated experimentally
- Specific: clearly defined relationships
- Grounded: based on identified patterns and gaps

Format your response as a JSON object with these keys:
- "hypotheses": list of hypothesis objects containing:
  - "id": unique id
  - "text": the hypothesis statement
  - "rationale": why this hypothesis is proposed
  - "required_data": data needed to test
  - "potential_experiments": suggested experiments
  - "expected_outcomes": expected results
""")


# ============================================================================
# VALIDATION PROMPTS
# ============================================================================

validation_prompt = PromptTemplate("""Validate the hypothesis: {hypothesis}

Current Date: {current_date}

Instructions:
- Assess logical consistency
- Assess methodological soundness
- Assess feasibility of testing
- Identify supporting evidence from provided papers

Return a JSON object with keys:
- "confidence_score" (0.0 to 1.0)
- "reasoning" (text)
- "supporting_papers" (list of paper ids)

Example expected output (fill these fields):
{{
  "confidence_score": {confidence_score},
  "reasoning": "{reasoning}",
  "supporting_papers": {supporting_papers}
}}
""")


# ============================================================================
# REFLECTION PROMPTS (similar to Google's)
# ============================================================================

reflection_instructions = PromptTemplate("""Analyze the current research state and identify knowledge gaps.

Current Date: {current_date}
Research Topic: {research_topic}

CURRENT FINDINGS:
{current_summary}

Instructions:
- Assess if current information is sufficient
- Identify critical knowledge gaps
- Generate follow-up queries if needed

Format your response as a JSON object with these exact keys:
- "is_sufficient": true or false
- "knowledge_gap": description of what's missing (empty string if sufficient)
- "follow_up_queries": list of follow-up queries (empty list if sufficient)

Example:
```json
{{
  "is_sufficient": false,
  "knowledge_gap": "Missing information about implementation challenges",
  "follow_up_queries": ["What are the main implementation challenges for this approach?"]
}}
```

Carefully assess the research completeness:""")


# ============================================================================
# FINAL ANSWER PROMPTS
# ============================================================================

answer_instructions = PromptTemplate("""Generate a comprehensive research report based on the workflow results.

Current Date: {current_date}
Research Query: {research_topic}

RESEARCH RESULTS:
Papers Analyzed: {papers_count}
Key Findings: {key_findings}
Hypotheses Generated: {hypotheses}
Validation Results: {validation_summary}

Instructions:
- Provide a comprehensive answer to the original query
- Include key findings and validated hypotheses
- Note important limitations
- Suggest future research directions
- Use markdown formatting

Generate a high-quality research report that addresses the query with actionable insights.""")