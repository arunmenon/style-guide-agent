import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from crewai import Crew, Process, Agent, Task, Flow, start, router, listen, before_kickoff, after_kickoff, LLM
from sqlalchemy import create_engine, text

# =============================================================================
# Pydantic Models for Structured Communication
# =============================================================================

class Draft_Title_Guide(BaseModel):
    category: str
    product_type: str
    draft_text: str

class Pending_Title_Guide(BaseModel):
    category: str
    product_type: str
    pending_text: str
    feedback: List[str] = Field(default_factory=list)

class Final_Title_Guide(BaseModel):
    category: str
    product_type: str
    final_text: str

# =============================================================================
# SQLAlchemy Helper: Fetch Generic Title Guidelines from Azure SQL
# =============================================================================

def fetch_generic_title_guidelines(engine, category: str, product_type: str) -> Optional[str]:
    if not engine:
        return None
    with engine.connect() as conn:
        query = text("""
            SELECT guidelines 
            FROM GenericTitleGuides 
            WHERE category = :cat AND product_type = :pt
        """)
        result = conn.execute(query, {"cat": category, "pt": product_type}).fetchone()
        if result:
            return result[0]
    return None

# =============================================================================
# Agent Creators: Writer & Validator
# =============================================================================

def create_title_guide_writer(llm: LLM) -> Agent:
    return Agent(
        role="Title Guide Writer",
        goal=(
            "Draft a Walmart-style title guide for {category} / {product_type} "
            "using any provided generic guidelines and incorporating feedback if given."
        ),
        backstory=(
            "This agent is well-versed in Walmart's content guidelines for product titles "
            "and uses best practices to produce a clear, structured guide."
        ),
        llm=llm,
        memory=True,
        verbose=True,
        allow_delegation=False,
        respect_context_window=True,
        use_system_prompt=True,
        cache=False
    )

def create_title_guide_validator(llm: LLM) -> Agent:
    return Agent(
        role="Title Guide Validator",
        goal=(
            "Review the drafted title guide for clarity, completeness, and compliance "
            "with Walmart's style. Return structured feedback (a list of issues) if needed."
        ),
        backstory=(
            "This agent inspects the draft to ensure all requirements are met. It only provides "
            "feedback and does not modify the guide directly."
        ),
        llm=llm,
        memory=True,
        verbose=True,
        allow_delegation=False,
        respect_context_window=True,
        use_system_prompt=True,
        cache=False
    )

# =============================================================================
# CrewAI Flow: TitleStyleFlow - Event-Driven Feedback Loop
# =============================================================================

class TitleStyleFlow(Flow):
    def __init__(self, category: str, product_type: str, llm_model: str = "openai/gpt-4o-mini",
                 azure_conn_str: Optional[str] = None, max_iterations: int = 3):
        super().__init__()
        # Initialize flow state
        self.state['category'] = category
        self.state['product_type'] = product_type
        self.state['iteration'] = 0
        self.state['max_iterations'] = max_iterations
        self.state['feedback'] = []  # latest feedback (if any)
        self.state['draft'] = None   # current draft
        self.state['pending'] = None # current pending guide (with feedback)
        self.state['final_guide'] = None

        # Set up LLM and (optionally) the SQL engine
        self.llm = LLM(model=llm_model, temperature=0.2, verbose=True)
        self.engine = create_engine(azure_conn_str) if azure_conn_str else None

        # Create agents
        self.title_writer = create_title_guide_writer(self.llm)
        self.title_validator = create_title_guide_validator(self.llm)

        # Retrieve generic guidelines, if available, and store in state.
        guidelines = fetch_generic_title_guidelines(self.engine, category, product_type)
        self.state['guidelines'] = guidelines or ""

    @start()
    def start_flow(self) -> Dict[str, Any]:
        """
        Start the flow by producing an initial draft using the Title Guide Writer Agent.
        """
        self.state['iteration'] = 1
        print(f"[FLOW] Starting iteration {self.state['iteration']} for {self.state['category']} / {self.state['product_type']}")
        writer_input = {
            "category": self.state['category'],
            "product_type": self.state['product_type'],
            "generic_guidelines": self.state['guidelines'],
            "feedback": []  # No feedback on the first iteration
        }
        # Call the writer agent via a simulated task invocation.
        # (Assume the agent returns a JSON string matching Draft_Title_Guide.)
        draft_json_str = self.title_writer.execute(writer_input)  # Use execute() instead of run()
        draft = json.loads(draft_json_str)
        self.state['draft'] = draft
        return draft

    @router(start_flow)
    def route_draft_to_validation(self, draft: Dict[str, Any]) -> str:
        """
        Route the produced draft to the Validator Agent.
        """
        print(f"[FLOW] Routing draft (Iteration {self.state['iteration']}) for validation.")
        validator_input = {
            "category": draft.get("category", self.state['category']),
            "product_type": draft.get("product_type", self.state['product_type']),
            "draft_text": draft.get("draft_text", ""),
            "feedback": []  # Validator does not need prior feedback in its input.
        }
        validation_json_str = self.title_validator.execute(validator_input)  # Simulated agent call
        pending = json.loads(validation_json_str)
        self.state['pending'] = pending

        # If no feedback is returned, consider the draft validated.
        if not pending.get("feedback"):
            return "validated"
        else:
            return "needs_revision"

    @listen("needs_revision")
    def revise_draft(self) -> Dict[str, Any]:
        """
        When validation indicates revisions are needed, invoke the writer agent again with the feedback.
        """
        if self.state['iteration'] >= self.state['max_iterations']:
            print("[FLOW] Maximum iterations reached; cannot refine further.")
            return self.state['pending']  # Return the latest pending result.
        self.state['iteration'] += 1
        print(f"[FLOW] Revision iteration {self.state['iteration']}. Feedback: {self.state['pending'].get('feedback')}")
        writer_input = {
            "category": self.state['category'],
            "product_type": self.state['product_type'],
            "generic_guidelines": self.state['guidelines'],
            "feedback": self.state['pending'].get("feedback", [])
        }
        revised_json_str = self.title_writer.execute(writer_input)
        revised_draft = json.loads(revised_json_str)
        self.state['draft'] = revised_draft
        return revised_draft

    @router(revise_draft)
    def route_revised_to_validation(self, revised_draft: Dict[str, Any]) -> str:
        """
        Validate the revised draft.
        """
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
        if not pending.get("feedback"):
            return "validated"
        else:
            return "needs_revision"

    @listen("validated")
    def on_validated(self) -> str:
        """
        Once validated, request human approval.
        """
        print("[FLOW] Draft validated. Requesting human approval...")
        pending = self.state['pending']
        # Simulate human approval (in practice, this could be a task with human input)
        human_approval = True  # For demonstration, we assume approval.
        if human_approval:
            final = Final_Title_Guide(
                category=pending.get("category", self.state['category']),
                product_type=pending.get("product_type", self.state['product_type']),
                final_text=pending.get("pending_text", "")
            )
            self.state['final_guide'] = final.dict()
            return "approved"
        else:
            return "rejected"

    @listen("max_reached")
    def on_max_reached(self) -> str:
        """
        Handle the case where maximum iterations were reached.
        """
        print("[FLOW] Maximum iterations reached; outputting the best available draft.")
        pending = self.state['pending']
        final = Final_Title_Guide(
            category=pending.get("category", self.state['category']),
            product_type=pending.get("product_type", self.state['product_type']),
            final_text="(Partial Draft) " + pending.get("pending_text", "")
        )
        self.state['final_guide'] = final.dict()
        return "done"

    @listen("approved")
    def on_approved(self) -> str:
        """
        Final step: the human-approved guide.
        """
        print("[FLOW] Human approval received. Finalizing the title guide.")
        return "done"

# =============================================================================
# Top-Level Crew: Composing the Flow into a CrewAI Process
# =============================================================================

class TitleStyleGuideCrew:
    def __init__(self, category: str, product_type: str, azure_conn_str: Optional[str] = None, max_iterations: int = 3):
        self.category = category
        self.product_type = product_type
        self.azure_conn_str = azure_conn_str
        self.max_iterations = max_iterations
        self.flow = TitleStyleFlow(category, product_type, azure_conn_str=azure_conn_str, max_iterations=max_iterations)

    def run(self) -> Optional[Final_Title_Guide]:
        print(f"=== Starting Title Style Guide Crew for {self.category} / {self.product_type} ===")
        result = self.flow.kickoff()  # Kick off the event-driven flow.
        print(f"=== Flow ended with state: {self.flow.state} ===")
        final_data = self.flow.state.get("final_guide", {})
        if final_data:
            return Final_Title_Guide.parse_obj(final_data)
        return None

# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Replace with your actual Azure SQL connection string if available.
    azure_conn_str = "mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"
    
    # Instantiate the crew with sample inputs.
    crew = TitleStyleGuideCrew(category="Fashion", product_type="T-Shirts", azure_conn_str=azure_conn_str, max_iterations=3)
    final_guide = crew.run()
    
    if final_guide:
        print("\nFinal Title Style Guide (approved or partial):")
        print(final_guide.json(indent=2))
    else:
        print("No final guide produced.")
