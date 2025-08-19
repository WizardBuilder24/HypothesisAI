"""
Utility functions for HypothesisAI research workflow
Adapted from Google's utility patterns
"""

from typing import Any, Dict, List, Optional
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
import hashlib
import re
from datetime import datetime


def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    Get the research topic from the messages.
    Follows Google's pattern for extracting query from message history.
    """
    if not messages:
        return ""
    
    # Single message case - just return content
    if len(messages) == 1:
        return messages[-1].content
    
    # Multiple messages - build context
    research_topic = ""
    for message in messages:
        if isinstance(message, HumanMessage):
            research_topic += f"User: {message.content}\n"
        elif isinstance(message, AIMessage):
            research_topic += f"Assistant: {message.content}\n"
    
    return research_topic.strip()


def format_papers_for_synthesis(papers: List[Dict[str, Any]], max_papers: int = 20) -> str:
    """
    Format papers into a structured summary for synthesis.
    
    Args:
        papers: List of paper dictionaries
        max_papers: Maximum papers to include
        
    Returns:
        Formatted string of papers
    """
    if not papers:
        return "No papers available."
    
    formatted_papers = []
    for i, paper in enumerate(papers[:max_papers], 1):
        paper_text = f"""Paper {i} (ID: p{i}):
Title: {paper.get('title', 'Unknown')}
Authors: {', '.join(paper.get('authors', ['Unknown']))}
Year: {paper.get('year', 'N/A')}
Abstract: {paper.get('abstract', 'No abstract')[:300]}...
Relevance: {paper.get('relevance_score', 0):.2f}"""
        formatted_papers.append(paper_text)
    
    return "\n\n---\n\n".join(formatted_papers)


def format_synthesis_summary(synthesis: Dict[str, Any]) -> str:
    """
    Format synthesis into a summary for hypothesis generation.
    
    Args:
        synthesis: Synthesis dictionary
        
    Returns:
        Formatted synthesis summary
    """
    if not synthesis:
        return "No synthesis available."
    
    parts = []
    
    # Add patterns
    patterns = synthesis.get('patterns', [])
    if patterns:
        parts.append("PATTERNS IDENTIFIED:")
        for i, pattern in enumerate(patterns, 1):
            parts.append(f"{i}. {pattern.get('description', 'Unknown')}")
            parts.append(f"   Confidence: {pattern.get('confidence', 0):.2f}")
    
    # Add key findings
    findings = synthesis.get('key_findings', [])
    if findings:
        parts.append("\nKEY FINDINGS:")
        for finding in findings[:5]:
            parts.append(f"- {finding}")
    
    # Add research gaps
    gaps = synthesis.get('research_gaps', [])
    if gaps:
        parts.append("\nRESEARCH GAPS:")
        for gap in gaps[:5]:
            parts.append(f"- {gap}")
    
    return "\n".join(parts)


def format_hypotheses_list(hypotheses: List[Dict[str, Any]]) -> str:
    """
    Format hypotheses for validation.
    
    Args:
        hypotheses: List of hypothesis dictionaries
        
    Returns:
        Formatted hypotheses string
    """
    if not hypotheses:
        return "No hypotheses available."
    
    formatted = []
    for i, hyp in enumerate(hypotheses, 1):
        hyp_text = f"""Hypothesis {i}:
Content: {hyp.get('content', 'Unknown')}
Reasoning: {hyp.get('reasoning', 'No reasoning provided')}
Confidence: {hyp.get('confidence_score', 0):.2f}
Novelty: {hyp.get('novelty_score', 0):.2f}
Feasibility: {hyp.get('feasibility_score', 0):.2f}"""
        formatted.append(hyp_text)
    
    return "\n\n---\n\n".join(formatted)


def deduplicate_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate papers based on title similarity.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        Deduplicated list of papers
    """
    seen_titles = set()
    unique_papers = []
    
    for paper in papers:
        # Normalize title for comparison
        title = paper.get('title', '').lower().strip()
        title_normalized = re.sub(r'[^\w\s]', '', title)
        title_normalized = re.sub(r'\s+', ' ', title_normalized)
        
        if title_normalized not in seen_titles:
            seen_titles.add(title_normalized)
            unique_papers.append(paper)
    
    return unique_papers


def score_paper_relevance(title: str, abstract: str, query: str) -> float:
    """
    Calculate simple relevance score for a paper.
    
    Args:
        title: Paper title
        abstract: Paper abstract
        query: Research query
        
    Returns:
        Relevance score between 0 and 1
    """
    query_words = set(query.lower().split())
    
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been'}
    query_words = query_words - stop_words
    
    if not query_words:
        return 0.5
    
    # Score based on title (weighted more)
    title_words = set(title.lower().split())
    title_overlap = len(query_words & title_words) / len(query_words)
    
    # Score based on abstract
    abstract_words = set(abstract.lower().split())
    abstract_overlap = len(query_words & abstract_words) / len(query_words)
    
    # Weighted combination
    relevance_score = (0.6 * title_overlap) + (0.4 * abstract_overlap)
    
    return min(1.0, max(0.0, relevance_score))


def extract_paper_ids(synthesis: Dict[str, Any]) -> List[str]:
    """
    Extract all paper IDs referenced in synthesis.
    
    Args:
        synthesis: Synthesis dictionary
        
    Returns:
        List of unique paper IDs
    """
    paper_ids = set()
    
    # Extract from patterns
    patterns = synthesis.get('patterns', [])
    for pattern in patterns:
        paper_ids.update(pattern.get('paper_ids', []))
    
    return list(paper_ids)


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