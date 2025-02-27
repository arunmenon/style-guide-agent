import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from crew_flow.flow import TitleStyleFlow, TitleStyleGuideCrew
from crew_flow.flow import Draft_Title_Guide, Pending_Title_Guide, Final_Title_Guide

class MockWriter:
    """Simulates the Title Guide Writer agent"""
    def execute(self, input_data):
        category = input_data.get("category", "Unknown")
        product_type = input_data.get("product_type", "Unknown")
        feedback = input_data.get("feedback", [])
        
        # If there's feedback, create an improved version
        if feedback:
            return json.dumps({
                "category": category,
                "product_type": product_type,
                "draft_text": f"""# Walmart Style Guide for {category} {product_type} Titles

## Purpose
This guide provides standardized instructions for creating effective product titles for {product_type} in the {category} category on Walmart's platform.

## Title Structure Requirements
1. Begin with the brand name
2. Include key product features (now with character counts)
3. Specify model number when applicable
4. Mention color options clearly
5. Include size specifications when relevant
6. Avoid ALL CAPS except for brand names that are stylized that way
7. Maximum 200 characters

## Examples
- "Sony WH-1000XM4 Wireless Noise-Canceling Headphones, Black, 30-Hour Battery"
- "Bose QuietComfort 45 Bluetooth Wireless Headphones, White, Noise Cancelling"
- "Apple AirPods Pro (2nd Generation) with MagSafe Case, Active Noise Cancellation"

## Prohibited Elements
- Promotional phrases like "Best" or "Top-rated"
- Special characters except hyphens and parentheses
- Competitor brand names
- Price information
"""
            })
        else:
            # Initial draft (with intentional issues for validator to catch)
            return json.dumps({
                "category": category,
                "product_type": product_type,
                "draft_text": f"""# Style Guide for {category} {product_type}

## Title Structure
1. Start with brand name
2. Include key product features
3. Add model number
4. Mention color
5. Add size if applicable

## Formatting
- Use title case
- Separate elements with commas
- No all-caps
"""
            })

class MockValidator:
    """Simulates the Title Guide Validator agent"""
    def execute(self, input_data):
        category = input_data.get("category", "Unknown")
        product_type = input_data.get("product_type", "Unknown")
        draft_text = input_data.get("draft_text", "")
        
        # First review - provide feedback
        if "Examples" not in draft_text:
            return json.dumps({
                "category": category,
                "product_type": product_type,
                "pending_text": draft_text,
                "feedback": [
                    "Add character count limits for the title",
                    "Include specific examples of good titles for this product type",
                    "Add more details about prohibited terms/elements",
                    "Specifically mention this is for Walmart platform"
                ]
            })
        else:
            # Second review - approve
            return json.dumps({
                "category": category,
                "product_type": product_type,
                "pending_text": draft_text,
                "feedback": []  # Empty feedback means approved
            })

def run_demo_test():
    """Run a demo of the flow with mock agents that return realistic content"""
    
    # Create a test flow with mock agents
    class DemoTitleStyleFlow(TitleStyleFlow):
        def __init__(self, *args, **kwargs):
            # Skip parent init to avoid external dependencies
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
            
            # Use our mock agents
            self.title_writer = MockWriter()
            self.title_validator = MockValidator()
            self.engine = None
    
    # Create a crew that uses our demo flow
    class DemoTitleStyleGuideCrew(TitleStyleGuideCrew):
        def __init__(self, *args, **kwargs):
            self.category = kwargs.get('category', 'Test')
            self.product_type = kwargs.get('product_type', 'Test')
            self.azure_conn_str = None
            self.max_iterations = kwargs.get('max_iterations', 3)
            self.flow = DemoTitleStyleFlow(
                category=self.category,
                product_type=self.product_type,
                max_iterations=self.max_iterations
            )
    
    # Run the demo
    crew = DemoTitleStyleGuideCrew(
        category="Electronics", 
        product_type="Headphones",
        max_iterations=3
    )
    
    # Execute the flow
    final_guide = crew.run()
    
    # Output the results
    if final_guide:
        print("\nFinal Guide Output:")
        print(f"Category: {final_guide.category}")
        print(f"Product Type: {final_guide.product_type}")
        print("\nStyle Guide Content:")
        print("=" * 80)
        print(final_guide.final_text)
        print("=" * 80)
    else:
        print("No final guide was produced.")

if __name__ == "__main__":
    print("Running demonstration of title style guide flow with realistic mock content")
    run_demo_test()
    print("\nDemo completed!")