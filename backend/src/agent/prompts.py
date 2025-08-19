"""
Prompt templates for HypothesisAI agents
Adapted from Google's prompt structure
"""

from datetime import datetime


def get_current_date():
    """Get current date in readable format"""
    return datetime.now().strftime("%B %d, %Y")


# ============================================================================
# SUPERVISOR PROMPTS
# ============================================================================

supervisor_instructions = """You are the research workflow supervisor. Analyze the current state and route to the appropriate agent.

Current Date: {current_date}
Research Query: {query}

CURRENT STATE:
- Papers Found: {papers_count}
- Synthesis Complete: {has_synthesis}
- Patterns Identified: {patterns_count}
- Hypotheses Generated: {hypotheses_count}
- Validation Complete: {has_validation}
- Current Iteration: {iteration}

ROUTING LOGIC:
1. If no papers or papers < 5 → route to "literature_hunter"
2. If papers ≥ 5 but no synthesis → route to "synthesizer"
3. If synthesis done but no hypotheses → route to "hypothesis_generator"
4. If hypotheses exist but no validation → route to "validator"
5. If validation complete or iteration > 10 → route to "end"

Format your response as a JSON object with these exact keys:
- "next_agent": one of ["literature_hunter", "synthesizer", "hypothesis_generator", "validator", "end"]
- "should_continue": true or false
- "reasoning": brief explanation

Example:
```json
{{
    "next_agent": "synthesizer",
    "should_continue": true,
    "reasoning": "Found 15 papers, ready for synthesis"
}}
```

Make your routing decision:"""


# ============================================================================
# LITERATURE SEARCH PROMPTS
# ============================================================================

literature_search_instructions = """Generate search queries and find relevant academic papers for the research topic.

Current Date: {current_date}
Research Query: {query}
Maximum Papers: {max_papers}

Instructions:
- Generate 1-3 focused search queries
- Find papers from the last 5 years preferably
- Include diverse perspectives
- Each paper needs title, authors, year, and abstract

Format your response as a JSON object with these keys:
- "queries": list of search query strings
- "rationale": explanation of search strategy

Then provide a second JSON object with:
- "papers": list of paper objects containing:
  - "title": paper title
  - "authors": list of author names
  - "year": publication year
  - "abstract": paper abstract (200-300 words)
  - "doi": DOI if available
- "total_found": total number found
- "search_strategy": strategy used

Focus on finding high-quality, relevant papers."""


# ============================================================================
# SYNTHESIS PROMPTS
# ============================================================================

synthesis_instructions = """Analyze the research papers and synthesize patterns, findings, and gaps.

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

Provide comprehensive synthesis of the research landscape."""


# ============================================================================
# HYPOTHESIS GENERATION PROMPTS
# ============================================================================

hypothesis_generation_instructions = """Generate novel research hypotheses based on the synthesis.

Current Date: {current_date}
Target: Generate {num_hypotheses} hypotheses

SYNTHESIS SUMMARY:
{synthesis_summary}

Requirements for each hypothesis:
- Novel: not directly stated in existing research
- Testable: can be validated experimentally
- Specific: clearly defined relationships
- Grounded: based on identified patterns and gaps

Format your response as a JSON object with these keys:
- "hypotheses": list of hypothesis objects containing:
  - "content": the hypothesis statement
  - "reasoning": why this hypothesis is proposed
  - "confidence_score": confidence (0.0 to 1.0)
  - "novelty_score": novelty (0.0 to 1.0)
  - "feasibility_score": feasibility (0.0 to 1.0)
- "generation_strategy": your approach

Generate creative but scientifically grounded hypotheses."""


# ============================================================================
# VALIDATION PROMPTS
# ============================================================================

validation_instructions = """Validate the research hypotheses for soundness and feasibility.

Current Date: {current_date}

HYPOTHESES TO VALIDATE:
{hypotheses_list}

Validation Criteria:
1. Logical consistency
2. Methodological soundness
3. Feasibility of testing
4. Potential impact
5. Ethical considerations

For each hypothesis, assess:
- Is it internally consistent?
- Can it be tested with current methods?
- Are there major obstacles?
- What are the main risks?

Format your response as a JSON object with these keys:
- "validation_results": list of validation objects containing:
  - "is_valid": true or false
  - "confidence": validation confidence (0.0 to 1.0)
  - "issues": list of issues found
  - "recommendations": list of recommendations
- "overall_quality": overall quality score (0.0 to 1.0)
- "summary": brief validation summary

Provide rigorous but constructive validation."""


# ============================================================================
# REFLECTION PROMPTS (similar to Google's)
# ============================================================================

reflection_instructions = """Analyze the current research state and identify knowledge gaps.

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

Carefully assess the research completeness:"""


# ============================================================================
# FINAL ANSWER PROMPTS
# ============================================================================

answer_instructions = """Generate a comprehensive research report based on the workflow results.

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

Generate a high-quality research report that addresses the query with actionable insights."""