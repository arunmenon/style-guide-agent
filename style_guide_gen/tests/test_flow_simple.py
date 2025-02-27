import sys
import os
from pathlib import Path
import json
import unittest
from unittest.mock import patch, Mock

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the flow module classes
from crew_flow.flow import TitleStyleFlow, TitleStyleGuideCrew
from crew_flow.flow import Draft_Title_Guide, Pending_Title_Guide, Final_Title_Guide

# Simple test that doesn't use mocking libraries
def test_title_style_flow_simple():
    """
    Simple test for TitleStyleFlow that fakes the dependencies without mock libraries
    """
    # Create a simple test class
    class TestTitleStyleFlow(TitleStyleFlow):
        def __init__(self, *args, **kwargs):
            # Skip the parent init to avoid external dependencies
            self.state = {
                'category': kwargs.get('category', 'Test'),
                'product_type': kwargs.get('product_type', 'Test'),
                'iteration': 0,
                'max_iterations': kwargs.get('max_iterations', 3),
                'feedback': [],
                'draft': None,
                'pending': None,
                'final_guide': None,
                'guidelines': ""
            }
            
            # We'll use simple function mocks instead of actual agents
            self.title_writer = self._mock_writer
            self.title_validator = self._mock_validator
            self.engine = None
            
        def _mock_writer(self, *args, **kwargs):
            """Mock writer agent that returns a simple draft"""
            self.state['iteration'] += 1
            return json.dumps({
                "category": self.state['category'],
                "product_type": self.state['product_type'],
                "draft_text": f"Sample draft for {self.state['category']} {self.state['product_type']}. Iteration {self.state['iteration']}"
            })
            
        def _mock_validator(self, *args, **kwargs):
            """Mock validator that approves on the second iteration"""
            if self.state['iteration'] == 1:
                return json.dumps({
                    "category": self.state['category'],
                    "product_type": self.state['product_type'],
                    "pending_text": f"Pending text for {self.state['category']} {self.state['product_type']}",
                    "feedback": ["Need more details", "Add examples"]
                })
            else:
                return json.dumps({
                    "category": self.state['category'],
                    "product_type": self.state['product_type'],
                    "pending_text": f"Final text for {self.state['category']} {self.state['product_type']}",
                    "feedback": []  # Empty feedback means approved
                })
    
    # Create flow instance
    flow = TestTitleStyleFlow(
        category="Electronics",
        product_type="Headphones",
        max_iterations=3
    )
    
    # Start the flow
    result = flow.kickoff()
    
    # Print test results
    print("\nTest Results:")
    print(f"Result: {result}")
    print(f"Iterations: {flow.state.get('iteration')}")
    print(f"Final guide: {flow.state.get('final_guide')}")
    
    # Basic assertions
    assert flow.state.get('iteration') == 2
    assert flow.state.get('final_guide') is not None
    
    return result

if __name__ == "__main__":
    print("Running simple test for TitleStyleFlow...")
    test_result = test_title_style_flow_simple()
    print("\nTest completed successfully!")