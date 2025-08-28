#!/usr/bin/env python3
"""
Test script for ArxivAPI integration in literature_hunter
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent.tools_and_schemas import SearchKeywords, Paper
from agent.tools.preprint_apis import ArxivAPI, Paper as PreprintPaper
import asyncio

async def test_arxiv_api():
    """Test ArxivAPI functionality"""
    print("Testing ArxivAPI integration...")
    
    try:
        async with ArxivAPI() as arxiv_api:
            papers = await arxiv_api.search("machine learning healthcare", max_results=3)
            print(f"Found {len(papers)} papers:")
            for i, paper in enumerate(papers, 1):
                print(f"{i}. {paper.title}")
                print(f"   Authors: {', '.join(paper.authors)}")
                print(f"   Date: {paper.date_published}")
                print(f"   Abstract: {paper.abstract[:100]}...")
                print()
    except Exception as e:
        print(f"Error: {e}")

def test_schemas():
    """Test schema imports"""
    print("Testing schema imports...")
    
    try:
        # Test SearchKeywords
        keywords = SearchKeywords(keywords=["machine learning", "healthcare", "AI"])
        print(f"SearchKeywords: {keywords.keywords}")
        
        # Test Paper compatibility
        paper_data = {
            "id": "test-123",
            "title": "Test Paper",
            "abstract": "Test abstract",
            "authors": ["Author 1", "Author 2"],
            "date_published": "2024-01-01T00:00:00",
            "source": "arXiv",
            "url": "https://example.com",
            "categories": ["cs.AI"],
            "doi": None,
            "citations": 0,
            "version": "v1",
            "pdf_url": "https://example.com/pdf",
            "relevance_score": 0.85,
            "quality_score": 0.90,
            "metadata": {}
        }
        
        paper = Paper(**paper_data)
        print(f"Paper created: {paper.title}")
        print("Schema imports successful!")
        
    except Exception as e:
        print(f"Schema error: {e}")

if __name__ == "__main__":
    print("=== HypothesisAI ArxivAPI Integration Test ===\n")
    
    # Test schemas first
    test_schemas()
    print()
    
    # Test ArxivAPI
    asyncio.run(test_arxiv_api())
    
    print("=== Test completed ===")
