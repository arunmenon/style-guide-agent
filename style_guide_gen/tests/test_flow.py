import sys
import os
from pathlib import Path
import json
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from crew_flow.flow import TitleStyleFlow, TitleStyleGuideCrew, Draft_Title_Guide, Pending_Title_Guide, Final_Title_Guide

class MockLLM:
    def __init__(self, *args, **kwargs):
        pass
    
    def complete(self, *args, **kwargs):
        return "Mock completion"

class MockAgent:
    def __init__(self, *args, **kwargs):
        self.role = kwargs.get("role", "Mock Agent")
        
    def execute(self, input_data):
        # Simulate agent responses based on role and input
        if "Title Guide Writer" in self.role:
            # Writer agent returns a draft
            return json.dumps({
                "category": input_data.get("category", "Unknown"),
                "product_type": input_data.get("product_type", "Unknown"),
                "draft_text": f"Sample draft for {input_data.get('category')} {input_data.get('product_type')} titles.\n\n"
                             f"1. Include brand first\n2. Add key features\n3. Include size/color if applicable"
            })
        elif "Title Guide Validator" in self.role:
            # Validator agent - first returns feedback, then approves on second pass
            draft_text = input_data.get("draft_text", "")
            if "first_validation" not in draft_text:
                # First pass - return feedback
                return json.dumps({
                    "category": input_data.get("category", "Unknown"),
                    "product_type": input_data.get("product_type", "Unknown"),
                    "pending_text": f"{draft_text}\n[first_validation]", # Add marker to recognize second pass
                    "feedback": ["Add character count limits", "Include example titles"]
                })
            else:
                # Second pass - approve
                return json.dumps({
                    "category": input_data.get("category", "Unknown"),
                    "product_type": input_data.get("product_type", "Unknown"),
                    "pending_text": draft_text,
                    "feedback": []  # Empty feedback means approval
                })
        
        return json.dumps({"error": "Unknown agent role"})

@patch('crew_flow.flow.LLM', MockLLM)
@patch('crew_flow.flow.create_title_guide_writer', return_value=MockAgent(role="Title Guide Writer"))
@patch('crew_flow.flow.create_title_guide_validator', return_value=MockAgent(role="Title Guide Validator"))
@patch('crew_flow.flow.create_engine', return_value=None)
def test_title_style_flow(mock_engine, mock_validator, mock_writer, mock_llm):
    """Test the TitleStyleFlow class with mocked agents"""
    # Initialize the flow
    flow = TitleStyleFlow(
        category="Electronics",
        product_type="Headphones",
        azure_conn_str=None,
        max_iterations=3
    )
    
    # Start the flow
    result = flow.kickoff()
    
    # Verify the flow completed successfully
    assert flow.state.get('final_guide') is not None
    assert flow.state.get('iteration') == 2  # Should complete after 2 iterations based on our mocks
    
    print("\nTest Results:")
    print(f"Iterations: {flow.state.get('iteration')}")
    print(f"Final guide: {flow.state.get('final_guide')}")
    
    return result

@patch('crew_flow.flow.TitleStyleFlow')
def test_title_style_guide_crew(mock_flow_class):
    """Test the TitleStyleGuideCrew class with a mocked flow"""
    # Set up the mock flow instance
    mock_flow_instance = MagicMock()
    mock_flow_instance.state = {
        'final_guide': {
            'category': 'Electronics',
            'product_type': 'Headphones',
            'final_text': 'Final style guide for Electronics Headphones'
        }
    }
    mock_flow_instance.kickoff.return_value = "done"
    
    # Make the mock_flow_class return our mock instance
    mock_flow_class.return_value = mock_flow_instance
    
    # Create and run the crew
    crew = TitleStyleGuideCrew(
        category="Electronics",
        product_type="Headphones"
    )
    result = crew.run()
    
    # Verify results
    assert result is not None
    assert result.category == "Electronics"
    assert result.product_type == "Headphones"
    assert "Final style guide" in result.final_text
    
    print("\nCrew Test Results:")
    print(f"Result: {result}")
    
    return result

if __name__ == "__main__":
    print("Testing TitleStyleFlow...")
    flow_result = test_title_style_flow()
    
    print("\nTesting TitleStyleGuideCrew...")
    crew_result = test_title_style_guide_crew()
    
    print("\nAll tests completed successfully!")