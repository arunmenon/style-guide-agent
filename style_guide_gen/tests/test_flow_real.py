import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from crew_flow.flow import TitleStyleGuideCrew

def run_real_test():
    """
    Runs a real test of the TitleStyleFlow with actual LLM calls.
    Note: This will use actual API calls and may incur costs.
    """
    # Create the crew with test data
    crew = TitleStyleGuideCrew(
        category="Electronics", 
        product_type="Headphones",
        max_iterations=2  # Limit iterations to control API costs
    )
    
    # Run the flow and get the results
    final_guide = crew.run()
    
    # Output results
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
    print("Running real test with actual LLM - this will make API calls!")
    run_real_test()
    print("\nTest completed!")