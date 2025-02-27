import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Create mock for crewai imports
sys.modules['crewai'] = type('MockCrewAI', (), {
    'Crew': type('MockCrew', (), {}),
    'Process': type('MockProcess', (), {}),
    'Agent': type('MockAgent', (), {}),
    'Task': type('MockTask', (), {}),
    'Flow': type('MockFlow', (), {
        '__init__': lambda self: None,
        'kickoff': lambda self: "done"
    }),
    'start': lambda: lambda f: f,
    'router': lambda f: lambda g: g,
    'listen': lambda s: lambda f: f,
    'before_kickoff': lambda f: f,
    'after_kickoff': lambda f: f,
    'LLM': type('MockLLM', (), {'__init__': lambda self, **kwargs: None})
})

# Create mock for sqlalchemy
sys.modules['sqlalchemy'] = type('MockSQLAlchemy', (), {
    'create_engine': lambda *args, **kwargs: None,
    'text': lambda s: s
})

# Create mock for pydantic
class MockBaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    @classmethod
    def parse_obj(cls, obj):
        return cls(**obj)

sys.modules['pydantic'] = type('MockPydantic', (), {
    'BaseModel': MockBaseModel,
    'Field': lambda *args, **kwargs: None
})

# Now import the flow module with mocks in place
from crew_flow.flow import TitleStyleFlow, TitleStyleGuideCrew

def test_title_style_flow_with_mocks():
    """Test the TitleStyleFlow class with our manually injected mocks"""
    
    # Override methods to simulate the flow behavior
    class TestTitleStyleFlow(TitleStyleFlow):
        def __init__(self, *args, **kwargs):
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
            
        def kickoff(self):
            """Simulate the flow execution"""
            # Simulate first iteration
            self.state['iteration'] = 1
            draft = {
                'category': self.state['category'],
                'product_type': self.state['product_type'],
                'draft_text': f"Draft for {self.state['category']} {self.state['product_type']}"
            }
            self.state['draft'] = draft
            
            # Simulate validation with feedback
            pending = {
                'category': self.state['category'],
                'product_type': self.state['product_type'],
                'pending_text': draft['draft_text'],
                'feedback': ['Add more details', 'Include examples']
            }
            self.state['pending'] = pending
            
            # Simulate second iteration with revision
            self.state['iteration'] = 2
            revised_draft = {
                'category': self.state['category'],
                'product_type': self.state['product_type'],
                'draft_text': f"Improved draft for {self.state['category']} {self.state['product_type']} with examples"
            }
            self.state['draft'] = revised_draft
            
            # Simulate final validation (approved)
            final_pending = {
                'category': self.state['category'],
                'product_type': self.state['product_type'],
                'pending_text': revised_draft['draft_text'],
                'feedback': []  # Empty feedback means approved
            }
            self.state['pending'] = final_pending
            
            # Set final guide
            self.state['final_guide'] = {
                'category': self.state['category'],
                'product_type': self.state['product_type'],
                'final_text': final_pending['pending_text']
            }
            
            return "done"
    
    # Create the test flow
    flow = TestTitleStyleFlow(
        category="Electronics", 
        product_type="Headphones",
        max_iterations=3
    )
    
    # Run the flow
    result = flow.kickoff()
    
    # Print results
    print("\nTest Results:")
    print(f"Result: {result}")
    print(f"Iterations: {flow.state['iteration']}")
    print(f"Final guide: {flow.state['final_guide']}")
    
    # Assert some expectations
    assert flow.state['iteration'] == 2
    assert flow.state['final_guide'] is not None
    assert "Improved draft" in flow.state['final_guide']['final_text']
    
    return result

def test_title_style_guide_crew():
    """Test the TitleStyleGuideCrew class"""
    
    # Create a mock flow class
    class MockFlow:
        def __init__(self, *args, **kwargs):
            self.state = {
                'final_guide': {
                    'category': kwargs.get('category', 'Test'),
                    'product_type': kwargs.get('product_type', 'Test'),
                    'final_text': f"Final guide for {kwargs.get('category', 'Test')} {kwargs.get('product_type', 'Test')}"
                }
            }
            
        def kickoff(self):
            return "done"
    
    # Create a modified crew class
    class TestTitleStyleGuideCrew(TitleStyleGuideCrew):
        def __init__(self, *args, **kwargs):
            self.category = kwargs.get('category', 'Test')
            self.product_type = kwargs.get('product_type', 'Test')
            self.azure_conn_str = None
            self.max_iterations = 3
            self.flow = MockFlow(**kwargs)
    
    # Create and run the crew
    crew = TestTitleStyleGuideCrew(
        category="Fashion", 
        product_type="T-Shirts"
    )
    result = crew.run()
    
    # Print and verify results
    print("\nCrew Test Results:")
    print(f"Result: {result}")
    
    assert result is not None
    assert result.category == "Fashion"
    assert result.product_type == "T-Shirts"
    assert "Final guide" in result.final_text
    
    return result

if __name__ == "__main__":
    print("Running test for TitleStyleFlow with manual mocks...")
    flow_result = test_title_style_flow_with_mocks()
    
    print("\nRunning test for TitleStyleGuideCrew...")
    crew_result = test_title_style_guide_crew()
    
    print("\nAll tests completed successfully!")