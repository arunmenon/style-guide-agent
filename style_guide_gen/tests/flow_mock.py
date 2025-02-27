"""
This module provides a standalone mock implementation of the TitleStyleFlow
that can be run without any dependencies like crewai, pydantic, etc.
"""

import json
from typing import Dict, List, Any, Optional

# Mock models
class MockFinal_Title_Guide:
    def __init__(self, category: str, product_type: str, final_text: str):
        self.category = category
        self.product_type = product_type
        self.final_text = final_text
    
    def __str__(self):
        return f"Category: {self.category}\nProduct Type: {self.product_type}\nFinal Text: {self.final_text}"

# Mock agents
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

# Mock flow implementation
class MockTitleStyleFlow:
    def __init__(self, category: str, product_type: str, max_iterations: int = 3):
        self.state = {
            'category': category,
            'product_type': product_type,
            'iteration': 0,
            'max_iterations': max_iterations,
            'feedback': [],
            'draft': None,
            'pending': None,
            'final_guide': None,
            'guidelines': ""
        }
        
        # Create mock agents
        self.title_writer = MockWriter()
        self.title_validator = MockValidator()
    
    def kickoff(self):
        """Runs the flow logic and returns the final state"""
        # First draft
        self.state['iteration'] = 1
        print(f"[FLOW] Starting iteration {self.state['iteration']} for {self.state['category']} / {self.state['product_type']}")
        
        writer_input = {
            "category": self.state['category'],
            "product_type": self.state['product_type'],
            "generic_guidelines": self.state['guidelines'],
            "feedback": []
        }
        
        draft_json_str = self.title_writer.execute(writer_input)
        draft = json.loads(draft_json_str)
        self.state['draft'] = draft
        
        # First validation
        print(f"[FLOW] Routing draft (Iteration {self.state['iteration']}) for validation.")
        validator_input = {
            "category": draft.get("category", self.state['category']),
            "product_type": draft.get("product_type", self.state['product_type']),
            "draft_text": draft.get("draft_text", ""),
            "feedback": []
        }
        
        validation_json_str = self.title_validator.execute(validator_input)
        pending = json.loads(validation_json_str)
        self.state['pending'] = pending
        
        # Check if revision needed
        if pending.get("feedback"):
            # Needs revision
            self.state['iteration'] += 1
            print(f"[FLOW] Revision iteration {self.state['iteration']}. Feedback: {pending.get('feedback')}")
            
            writer_input = {
                "category": self.state['category'],
                "product_type": self.state['product_type'],
                "generic_guidelines": self.state['guidelines'],
                "feedback": pending.get("feedback", [])
            }
            
            revised_json_str = self.title_writer.execute(writer_input)
            revised_draft = json.loads(revised_json_str)
            self.state['draft'] = revised_draft
            
            # Second validation
            print(f"[FLOW] Validating revised draft (Iteration {self.state['iteration']})")
            validator_input = {
                "category": revised_draft.get("category", self.state['category']),
                "product_type": revised_draft.get("product_type", self.state['product_type']),
                "draft_text": revised_draft.get("draft_text", ""),
                "feedback": []
            }
            
            validation_json_str = self.title_validator.execute(validator_input)
            pending = json.loads(validation_json_str)
            self.state['pending'] = pending
        
        # Finalize
        print("[FLOW] Draft validated. Requesting human approval...")
        pending = self.state['pending']
        
        # Always approve in this mock
        final = {
            "category": pending.get("category", self.state['category']),
            "product_type": pending.get("product_type", self.state['product_type']),
            "final_text": pending.get("pending_text", "")
        }
        
        self.state['final_guide'] = final
        print("[FLOW] Human approval received. Finalizing the title guide.")
        
        return "done"

# Crew implementation
class MockTitleStyleGuideCrew:
    def __init__(self, category: str, product_type: str, max_iterations: int = 3):
        self.category = category
        self.product_type = product_type
        self.max_iterations = max_iterations
        self.flow = MockTitleStyleFlow(category, product_type, max_iterations)
    
    def run(self) -> Optional[MockFinal_Title_Guide]:
        print(f"=== Starting Title Style Guide Crew for {self.category} / {self.product_type} ===")
        result = self.flow.kickoff()
        print(f"=== Flow ended with state: {self.flow.state} ===")
        
        final_data = self.flow.state.get("final_guide", {})
        if final_data:
            return MockFinal_Title_Guide(
                category=final_data.get("category", self.category),
                product_type=final_data.get("product_type", self.product_type),
                final_text=final_data.get("final_text", "")
            )
        return None

def run_standalone_demo():
    """Run a standalone demo that doesn't require any external dependencies"""
    crew = MockTitleStyleGuideCrew(
        category="Electronics", 
        product_type="Headphones",
        max_iterations=3
    )
    
    final_guide = crew.run()
    
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
    print("Running standalone mock implementation (no dependencies required)")
    run_standalone_demo()
    print("\nDemo completed!")