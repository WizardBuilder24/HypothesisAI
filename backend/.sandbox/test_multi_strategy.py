#!/usr/bin/env python3
"""
Test script for multi-strategy arXiv search
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent.tools_and_schemas import SearchStrategies, SearchStrategy
from agent.prompts import literature_search_prompt

def test_search_strategies_schema():
    """Test the SearchStrategies schema"""
    print("Testing SearchStrategies schema...")
    
    try:
        # Test creating a SearchStrategy
        strategy1 = SearchStrategy(
            query='ti:"machine learning" AND abs:medical',
            focus="Core ML medical applications",
            expected_paper_types="ML methods for medical diagnosis",
            priority=1
        )
        
        strategy2 = SearchStrategy(
            query='abs:"deep learning" AND abs:imaging',
            focus="Deep learning in medical imaging",
            expected_paper_types="CNN applications in radiology",
            priority=2
        )
        
        # Test creating SearchStrategies
        strategies = SearchStrategies(
            search_strategies=[strategy1, strategy2],
            rationale="Combined broad and specific approaches",
            coverage_analysis="Strategy 1 covers general ML medical, Strategy 2 focuses on imaging"
        )
        
        print(f"✅ Created {len(strategies.search_strategies)} search strategies:")
        for i, s in enumerate(strategies.search_strategies, 1):
            print(f"  {i}. {s.focus} (priority {s.priority})")
            print(f"     Query: {s.query}")
        
        print(f"Rationale: {strategies.rationale}")
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def test_prompt_formatting():
    """Test the updated literature search prompt"""
    print("\nTesting prompt formatting...")
    
    try:
        formatted = literature_search_prompt.format(
            query="machine learning for drug discovery",
            max_papers=10
        )
        
        if "search_strategies" in formatted and "arXiv search query string" in formatted:
            print("✅ Prompt formatting successful")
            print("Key sections found:")
            print("  - search_strategies field")
            print("  - arXiv query optimization instructions")
            return True
        else:
            print("❌ Prompt missing expected sections")
            return False
            
    except Exception as e:
        print(f"❌ Prompt formatting failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Multi-Strategy Search Test ===\n")
    
    success1 = test_search_strategies_schema()
    success2 = test_prompt_formatting()
    
    if success1 and success2:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
