"""
Utility functions for HypothesisAI research workflow.
Provides text processing, data formatting, and analysis utilities.
"""

from typing import Any, Dict, List, Optional, Set
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
import hashlib
import re
from datetime import datetime


# Constants for better maintainability
COMMON_STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'that', 
    'this', 'will', 'would', 'could', 'should'
}

DEFAULT_PAPER_RELEVANCE_SCORE = 0.5
TITLE_WEIGHT_IN_RELEVANCE = 0.6
ABSTRACT_WEIGHT_IN_RELEVANCE = 0.4
MAX_ABSTRACT_LENGTH_FOR_DISPLAY = 300


def extract_research_topic_from_messages(messages: List[AnyMessage]) -> str:
    """
    Extract research topic from conversation messages.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        Research topic string extracted from messages
    """
    if not messages:
        return ""
    
    if len(messages) == 1:
        return messages[-1].content
    
    # Build context from multiple messages
    topic_parts = []
    for message in messages:
        if isinstance(message, HumanMessage):
            topic_parts.append(f"User: {message.content}")
        elif isinstance(message, AIMessage):
            topic_parts.append(f"Assistant: {message.content}")
    
    return "\n".join(topic_parts)


def format_papers_for_synthesis(papers: List[Dict[str, Any]], max_papers: int = 20) -> str:
    """
    Format paper collection into structured text for synthesis processing.
    
    Args:
        papers: List of paper dictionaries
        max_papers: Maximum number of papers to include
        
    Returns:
        Formatted string representation of papers
    """
    if not papers:
        return "No papers available for synthesis."
    
    formatted_papers = []
    for index, paper in enumerate(papers[:max_papers], 1):
        paper_summary = _create_paper_summary(paper, index)
        formatted_papers.append(paper_summary)
    
    return "\n\n---\n\n".join(formatted_papers)


def _create_paper_summary(paper: Dict[str, Any], paper_number: int) -> str:
    """Create a formatted summary for a single paper."""
    title = paper.get('title', 'Unknown Title')
    authors = ', '.join(paper.get('authors', ['Unknown Author']))
    year = paper.get('year', 'N/A')
    abstract = paper.get('abstract', 'No abstract available')
    relevance_score = paper.get('relevance_score', 0)
    
    # Truncate abstract if too long
    if len(abstract) > MAX_ABSTRACT_LENGTH_FOR_DISPLAY:
        abstract = abstract[:MAX_ABSTRACT_LENGTH_FOR_DISPLAY] + "..."
    
    return f"""Paper {paper_number} (ID: p{paper_number}):
Title: {title}
Authors: {authors}
Year: {year}
Abstract: {abstract}
Relevance: {relevance_score:.2f}"""


def create_synthesis_summary_for_prompt(synthesis: Dict[str, Any]) -> str:
    """
    Format synthesis results into readable text for prompting.
    
    Args:
        synthesis: Synthesis result dictionary
        
    Returns:
        Formatted synthesis summary
    """
    if not synthesis:
        return "No synthesis data available."
    
    summary_sections = []
    
    # Add patterns section
    patterns_section = _format_patterns_section(synthesis.get('patterns', []))
    if patterns_section:
        summary_sections.append(patterns_section)
    
    # Add key findings section
    findings_section = _format_findings_section(synthesis.get('key_findings', []))
    if findings_section:
        summary_sections.append(findings_section)
    
    # Add research gaps section
    gaps_section = _format_gaps_section(synthesis.get('research_gaps', []))
    if gaps_section:
        summary_sections.append(gaps_section)
    
    return "\n\n".join(summary_sections) if summary_sections else "No synthesis content available."


def _format_patterns_section(patterns: List[Dict[str, Any]]) -> str:
    """Format patterns section of synthesis."""
    if not patterns:
        return ""
    
    lines = ["IDENTIFIED PATTERNS:"]
    for i, pattern in enumerate(patterns, 1):
        description = pattern.get('description', 'No description')
        confidence = pattern.get('confidence', 0)
        lines.append(f"{i}. {description}")
        lines.append(f"   Confidence: {confidence:.2f}")
    
    return "\n".join(lines)


def _format_findings_section(findings: List[str], max_findings: int = 5) -> str:
    """Format key findings section."""
    if not findings:
        return ""
    
    lines = ["KEY FINDINGS:"]
    for finding in findings[:max_findings]:
        lines.append(f"- {finding}")
    
    return "\n".join(lines)


def _format_gaps_section(gaps: List[str], max_gaps: int = 5) -> str:
    """Format research gaps section."""
    if not gaps:
        return ""
    
    lines = ["RESEARCH GAPS:"]
    for gap in gaps[:max_gaps]:
        lines.append(f"- {gap}")
    
    return "\n".join(lines)


def create_hypotheses_summary_for_validation(hypotheses: List[Dict[str, Any]]) -> str:
    """
    Format hypotheses list for validation processing.
    
    Args:
        hypotheses: List of hypothesis dictionaries
        
    Returns:
        Formatted hypotheses string
    """
    if not hypotheses:
        return "No hypotheses available for validation."
    
    formatted_hypotheses = []
    for i, hypothesis in enumerate(hypotheses, 1):
        hypothesis_summary = _create_hypothesis_summary(hypothesis, i)
        formatted_hypotheses.append(hypothesis_summary)
    
    return "\n\n---\n\n".join(formatted_hypotheses)


def _create_hypothesis_summary(hypothesis: Dict[str, Any], hypothesis_number: int) -> str:
    """Create formatted summary for a single hypothesis."""
    content = hypothesis.get('content', 'No content provided')
    reasoning = hypothesis.get('reasoning', 'No reasoning provided')
    confidence = hypothesis.get('confidence_score', 0)
    novelty = hypothesis.get('novelty_score', 0)
    feasibility = hypothesis.get('feasibility_score', 0)
    
    return f"""Hypothesis {hypothesis_number}:
Content: {content}
Reasoning: {reasoning}
Confidence: {confidence:.2f}
Novelty: {novelty:.2f}
Feasibility: {feasibility:.2f}"""


def remove_duplicate_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate papers based on normalized title similarity.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        Deduplicated list of papers
    """
    seen_titles: Set[str] = set()
    unique_papers = []
    
    for paper in papers:
        normalized_title = _normalize_paper_title(paper.get('title', ''))
        
        if normalized_title and normalized_title not in seen_titles:
            seen_titles.add(normalized_title)
            unique_papers.append(paper)
    
    return unique_papers


def _normalize_paper_title(title: str) -> str:
    """Normalize paper title for duplicate detection."""
    if not title:
        return ""
    
    # Convert to lowercase and remove punctuation
    normalized = re.sub(r'[^\w\s]', '', title.lower().strip())
    # Collapse multiple spaces into single spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def calculate_paper_relevance_score(title: str, abstract: str, query: str) -> float:
    """
    Calculate relevance score for a paper against a research query.
    
    Args:
        title: Paper title
        abstract: Paper abstract
        query: Research query
        
    Returns:
        Relevance score between 0 and 1
    """
    query_keywords = _extract_meaningful_keywords(query)
    
    if not query_keywords:
        return DEFAULT_PAPER_RELEVANCE_SCORE
    
    title_relevance = _calculate_text_overlap(title, query_keywords)
    abstract_relevance = _calculate_text_overlap(abstract, query_keywords)
    
    # Weighted combination favoring title matches
    relevance_score = (
        TITLE_WEIGHT_IN_RELEVANCE * title_relevance + 
        ABSTRACT_WEIGHT_IN_RELEVANCE * abstract_relevance
    )
    
    return min(1.0, max(0.0, relevance_score))


def _extract_meaningful_keywords(text: str) -> Set[str]:
    """Extract meaningful keywords by removing stop words."""
    if not text:
        return set()
    
    words = set(text.lower().split())
    return words - COMMON_STOP_WORDS


def _calculate_text_overlap(text: str, keywords: Set[str]) -> float:
    """Calculate overlap between text and keyword set."""
    if not text or not keywords:
        return 0.0
    
    text_words = set(text.lower().split())
    overlap_count = len(keywords & text_words)
    
    return overlap_count / len(keywords)


def extract_relevant_paper_ids(
    synthesis: Dict[str, Any], 
    hypothesis_content: Optional[str] = None
) -> List[str]:
    """
    Extract paper IDs relevant to a specific hypothesis or all papers from synthesis.
    
    Args:
        synthesis: Synthesis dictionary containing patterns and findings
        hypothesis_content: Optional hypothesis text for relevance filtering
        
    Returns:
        List of paper IDs relevant to the hypothesis
    """
    if hypothesis_content:
        return _find_hypothesis_relevant_papers(synthesis, hypothesis_content)
    else:
        return _extract_all_synthesis_paper_ids(synthesis)


def _find_hypothesis_relevant_papers(synthesis: Dict[str, Any], hypothesis_content: str) -> List[str]:
    """Find paper IDs relevant to a specific hypothesis."""
    hypothesis_keywords = _extract_meaningful_keywords(hypothesis_content)
    relevant_paper_ids: Set[str] = set()
    
    # Find relevant patterns
    patterns = synthesis.get('patterns', [])
    for pattern in patterns:
        if _is_pattern_relevant_to_hypothesis(pattern, hypothesis_keywords):
            relevant_paper_ids.update(pattern.get('paper_ids', []))
    
    # Find relevant key findings (using index-based paper IDs as heuristic)
    key_findings = synthesis.get('key_findings', [])
    for index, finding in enumerate(key_findings):
        if _is_finding_relevant_to_hypothesis(finding, hypothesis_keywords):
            relevant_paper_ids.add(f"p{index + 1}")
    
    return list(relevant_paper_ids)


def _is_pattern_relevant_to_hypothesis(pattern: Dict[str, Any], hypothesis_keywords: Set[str]) -> bool:
    """Check if a pattern is relevant to hypothesis keywords."""
    pattern_description = pattern.get('description', '').lower()
    pattern_keywords = set(pattern_description.split())
    return bool(hypothesis_keywords & pattern_keywords)


def _is_finding_relevant_to_hypothesis(finding: str, hypothesis_keywords: Set[str]) -> bool:
    """Check if a finding is relevant to hypothesis keywords."""
    finding_keywords = set(finding.lower().split())
    return bool(hypothesis_keywords & finding_keywords)


def _extract_all_synthesis_paper_ids(synthesis: Dict[str, Any]) -> List[str]:
    """Extract all paper IDs from synthesis patterns."""
    paper_ids: Set[str] = set()
    
    patterns = synthesis.get('patterns', [])
    for pattern in patterns:
        paper_ids.update(pattern.get('paper_ids', []))
    
    return list(paper_ids)


def generate_unique_workflow_id(query: str) -> str:
    """
    Generate unique workflow identifier based on query and timestamp.
    
    Args:
        query: Research query string
        
    Returns:
        Unique workflow ID string
    """
    timestamp = datetime.utcnow().isoformat()
    content = f"{query}_{timestamp}"
    hash_object = hashlib.md5(content.encode())
    return f"wf_{hash_object.hexdigest()[:12]}"


def get_current_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def create_validation_results_summary(validation_results: List[Dict[str, Any]]) -> str:
    """
    Create human-readable summary of validation results.
    
    Args:
        validation_results: List of validation result dictionaries
        
    Returns:
        Formatted validation summary string
    """
    if not validation_results:
        return "No validation results available."
    
    valid_count = sum(1 for result in validation_results if result.get('is_valid'))
    total_count = len(validation_results)
    
    summary_lines = [
        "VALIDATION SUMMARY:",
        f"Valid Hypotheses: {valid_count}/{total_count}",
        ""
    ]
    
    for i, result in enumerate(validation_results, 1):
        is_valid = result.get('is_valid', False)
        confidence = result.get('confidence', 0)
        status_icon = "✓" if is_valid else "✗"
        status_text = "Valid" if is_valid else "Invalid"
        
        summary_lines.append(f"Hypothesis {i}: {status_icon} {status_text}")
        summary_lines.append(f"  Confidence: {confidence:.2f}")
        
        # Add issues if present
        issues = result.get('issues', [])
        if issues:
            issue_preview = ', '.join(issues[:2])
            summary_lines.append(f"  Issues: {issue_preview}")
        
        # Add top recommendation if present
        recommendations = result.get('recommendations', [])
        if recommendations:
            summary_lines.append(f"  Recommendation: {recommendations[0]}")
    
    return "\n".join(summary_lines)


def merge_search_query_lists(existing_queries: List[str], new_queries: List[str]) -> List[str]:
    """
    Merge two query lists while avoiding duplicates.
    
    Args:
        existing_queries: Current list of queries
        new_queries: New queries to add
        
    Returns:
        Merged list without duplicates
    """
    # Use case-insensitive comparison for deduplication
    seen_queries = {query.lower().strip() for query in existing_queries}
    merged_queries = list(existing_queries)
    
    for query in new_queries:
        normalized_query = query.lower().strip()
        if normalized_query and normalized_query not in seen_queries:
            seen_queries.add(normalized_query)
            merged_queries.append(query)
    
    return merged_queries


def analyze_state(state: Dict[str, Any]) -> str:
    """
    Analyze the current state and return a summary for the supervisor.
    Moved from graph.py to centralize formatting logic.
    
    Args:
        state: ResearchState dictionary
        
    Returns:
        Formatted status summary string
    """
    status_parts = []
    
    # Check papers
    papers = state.get("papers", [])
    if papers:
        status_parts.append(f"Papers: {len(papers)} found")
    else:
        status_parts.append("Papers: None")
    
    # Check synthesis
    if state.get("synthesis"):
        synthesis = state["synthesis"]
        status_parts.append(f"Synthesis: Complete ({len(synthesis.get('patterns', []))} patterns)")
    else:
        status_parts.append("Synthesis: Not done")
    
    # Check hypotheses
    hypotheses = state.get("hypotheses", [])
    if hypotheses:
        status_parts.append(f"Hypotheses: {len(hypotheses)} generated")
    else:
        status_parts.append("Hypotheses: None")
    
    # Check validation
    if state.get("validation_results"):
        valid_count = state.get("valid_hypotheses_count", 0)
        status_parts.append(f"Validation: Complete ({valid_count} valid)")
    else:
        status_parts.append("Validation: Not done")
    
    # Check errors
    errors = state.get("errors", [])
    if errors:
        status_parts.append(f"Errors: {len(errors)}")
    
    return " | ".join(status_parts)


def format_synthesis_for_prompt(synthesis: Dict[str, Any]) -> str:
    """
    Format synthesis dictionary for prompt.
    Moved from graph.py to enable reuse across modules.
    
    Args:
        synthesis: Synthesis result dictionary
        
    Returns:
        Formatted synthesis text for prompting
    """
    parts = []
    
    # Add patterns
    patterns = synthesis.get("patterns", [])
    if patterns:
        parts.append("PATTERNS IDENTIFIED:")
        for i, pattern in enumerate(patterns, 1):
            parts.append(f"{i}. {pattern.get('description', '')}")
    
    # Add key findings
    findings = synthesis.get("key_findings", [])
    if findings:
        parts.append("\nKEY FINDINGS:")
        for finding in findings:
            parts.append(f"- {finding}")
    
    # Add research gaps
    gaps = synthesis.get("research_gaps", [])
    if gaps:
        parts.append("\nRESEARCH GAPS:")
        for gap in gaps:
            parts.append(f"- {gap}")
    
    return "\n".join(parts)


# Legacy function name aliases for backward compatibility
get_research_topic = extract_research_topic_from_messages
format_synthesis_summary = create_synthesis_summary_for_prompt
format_hypotheses_list = create_hypotheses_summary_for_validation
deduplicate_papers = remove_duplicate_papers
score_paper_relevance = calculate_paper_relevance_score
extract_paper_ids = extract_relevant_paper_ids
generate_workflow_id = generate_unique_workflow_id
get_current_timestamp = get_current_utc_timestamp
format_validation_summary = create_validation_results_summary
merge_search_queries = merge_search_query_lists


def generate_workflow_id(query: str) -> str:
    """
    Generate unique workflow ID.
    
    Args:
        query: Research query
        
    Returns:
        Unique workflow ID
    """
    timestamp = datetime.utcnow().isoformat()
    content = f"{query}_{timestamp}"
    hash_obj = hashlib.md5(content.encode())
    return f"wf_{hash_obj.hexdigest()[:12]}"


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()


def format_validation_summary(validation_results: List[Dict[str, Any]]) -> str:
    """
    Format validation results into a summary.
    
    Args:
        validation_results: List of validation result dictionaries
        
    Returns:
        Formatted validation summary
    """
    if not validation_results:
        return "No validation results."
    
    valid_count = sum(1 for v in validation_results if v.get('is_valid'))
    total_count = len(validation_results)
    
    summary_parts = [
        f"VALIDATION SUMMARY:",
        f"Valid Hypotheses: {valid_count}/{total_count}",
        ""
    ]
    
    for i, result in enumerate(validation_results, 1):
        summary_parts.append(f"Hypothesis {i}: {'✓ Valid' if result.get('is_valid') else '✗ Invalid'}")
        summary_parts.append(f"  Confidence: {result.get('confidence', 0):.2f}")
        
        issues = result.get('issues', [])
        if issues:
            summary_parts.append(f"  Issues: {', '.join(issues[:2])}")
        
        recommendations = result.get('recommendations', [])
        if recommendations:
            summary_parts.append(f"  Recommendation: {recommendations[0]}")
    
    return "\n".join(summary_parts)


def merge_search_queries(existing: List[str], new: List[str]) -> List[str]:
    """
    Merge search query lists, avoiding duplicates.
    
    Args:
        existing: Existing queries
        new: New queries to add
        
    Returns:
        Merged list of unique queries
    """
    # Normalize queries for comparison
    seen = {q.lower().strip() for q in existing}
    merged = list(existing)
    
    for query in new:
        normalized = query.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            merged.append(query)
    
    return merged


def analyze_state(state: Dict[str, Any]) -> str:
    """
    Analyze the current state and return a summary for the supervisor.
    Moved from graph.py to centralize formatting logic.
    
    Args:
        state: ResearchState dictionary
        
    Returns:
        Formatted status summary string
    """
    status_parts = []
    
    # Check papers
    papers = state.get("papers", [])
    if papers:
        status_parts.append(f"Papers: {len(papers)} found")
    else:
        status_parts.append("Papers: None")
    
    # Check synthesis
    if state.get("synthesis"):
        synthesis = state["synthesis"]
        status_parts.append(f"Synthesis: Complete ({len(synthesis.get('patterns', []))} patterns)")
    else:
        status_parts.append("Synthesis: Not done")
    
    # Check hypotheses
    hypotheses = state.get("hypotheses", [])
    if hypotheses:
        status_parts.append(f"Hypotheses: {len(hypotheses)} generated")
    else:
        status_parts.append("Hypotheses: None")
    
    # Check validation
    if state.get("validation_results"):
        valid_count = state.get("valid_hypotheses_count", 0)
        status_parts.append(f"Validation: Complete ({valid_count} valid)")
    else:
        status_parts.append("Validation: Not done")
    
    # Check errors
    errors = state.get("errors", [])
    if errors:
        status_parts.append(f"Errors: {len(errors)}")
    
    return " | ".join(status_parts)


def format_synthesis_for_prompt(synthesis: Dict[str, Any]) -> str:
    """
    Format synthesis dictionary for prompt.
    Moved from graph.py to enable reuse across modules.
    
    Args:
        synthesis: Synthesis result dictionary
        
    Returns:
        Formatted synthesis text for prompting
    """
    parts = []
    
    # Add patterns
    patterns = synthesis.get("patterns", [])
    if patterns:
        parts.append("PATTERNS IDENTIFIED:")
        for i, pattern in enumerate(patterns, 1):
            parts.append(f"{i}. {pattern.get('description', '')}")
    
    # Add key findings
    findings = synthesis.get("key_findings", [])
    if findings:
        parts.append("\nKEY FINDINGS:")
        for finding in findings:
            parts.append(f"- {finding}")
    
    # Add research gaps
    gaps = synthesis.get("research_gaps", [])
    if gaps:
        parts.append("\nRESEARCH GAPS:")
        for gap in gaps:
            parts.append(f"- {gap}")
    
    return "\n".join(parts)