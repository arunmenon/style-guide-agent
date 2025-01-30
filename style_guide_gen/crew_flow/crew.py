# style_guide_gen/style_guide_gen/crew.py

import json
from typing import Any, Dict
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from .schemas import StyleGuideOutput
from knowledge.db_knowledge import BaselineStyleKnowledgeSource, LegalKnowledgeSource
import sqlite3


@CrewBase
class StyleGuideCrew:
    """
    Multi-step crew that:
      1) Retrieves baseline & legal guidelines from SQLite (with fallback including 'ALL')
      2) Analyzes domain & product type
      3) Infers a final schema
      4) Builds a style guide
      5) Performs an exhaustive legal review
      6) Final refinement
      7) (Optional) Store final style guide in 'published_style_guides'
    """

    def __init__(self, llm_model="openai/gpt-4o", db_path="style_guide.db"):
        self.llm = LLM(model=llm_model, temperature=0.2, verbose=False)
        self.db_path = db_path
        self.inputs: Dict[str, Any] = {}

    @before_kickoff
    def capture_inputs(self, inputs: Dict[str, Any]):
        """
        Example input:
          {
            "category": "Fashion",
            "product_type": "Women's Dress",
            "fields_needed": ["title","shortDesc","longDesc"]
          }
        """
        self.inputs = inputs
        return inputs

    # Agents
    # -----------------------------------------------------------------------

    @agent
    def knowledge_agent(self) -> Agent:
        return Agent(
            role="Knowledge Aggregator",
            goal=(
                "Gather baseline style guidelines from the DB for {category}, {product_type}, plus brand/IP legal constraints. "
                "Merge them into a summarizable form for subsequent tasks."
            ),
            backstory=(
                "This agent queries the knowledge sources. "
                "No direct mention of DB tables is made here—it's all abstracted away by knowledge sources."
            ),
            llm=self.llm,
            memory=True,
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            use_system_prompt=True,
            cache=False
        )

    @agent
    def domain_breakdown_agent(self) -> Agent:
        return Agent(
            role="Domain Breakdown",
            goal=(
                "Examine the domain-level constraints from the knowledge retrieval. "
                "Focus on how {category} guidelines shape the style approach before focusing on product_type specifics."
            ),
            backstory=(
                "Ensures the broad domain guidelines are recognized (e.g., overall fashion rules, brand order, disclaimers)."
            ),
            llm=self.llm,
            memory=True,
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            use_system_prompt=True,
            cache=False
        )

    @agent
    def product_type_agent(self) -> Agent:
        return Agent(
            role="Product Type Analyzer",
            goal=(
                "Combine the domain breakdown with product-type knowledge. "
                "Refine the guidelines for each field needed (title, shortDesc, longDesc), factoring in brand or legal constraints."
            ),
            backstory="This agent pinpoints how {product_type} might differ within {category}, referencing baseline + legal guidelines.",
            llm=self.llm,
            memory=True,
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            use_system_prompt=True,
            cache=False
        )

    @agent
    def schema_inference_agent(self) -> Agent:
        return Agent(
            role="Schema Inference",
            goal="Propose a final style guide schema, ensuring no optional placeholders—everything is mandatory.",
            backstory=(
                "This agent ensures there's a well-defined JSON or markdown structure for the final style guide output. "
                "No partial or ambiguous instructions are allowed."
            ),
            llm=self.llm,
            memory=True,
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            use_system_prompt=True,
            cache=False
        )

    @agent
    def style_guide_construction_agent(self) -> Agent:
        return Agent(
            role="Style Guide Constructor",
            goal=(
                "Using the domain breakdown, product-type analysis, and schema inference, create a robust style guide. "
                "Include best practices, do's & don'ts, examples, disclaimers, etc. in a cohesive text form."
            ),
            backstory="The agent merges all constraints into an initial draft text. Typically partial markdown but not final.",
            llm=self.llm,
            memory=True,
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            use_system_prompt=True,
            cache=False
        )

    @agent
    def legal_review_agent(self) -> Agent:
        return Agent(
            role="Exhaustive Legal Reviewer",
            goal=(
                "Check the draft style guide for brand/IP compliance. If it references competitors or violates disclaimers, "
                "revise or highlight them. Return a legally reviewed version."
            ),
            backstory="This agent thoroughly applies Walmart brand usage constraints, disclaimers, avoiding 'guarantees', etc.",
            llm=self.llm,
            memory=True,
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            use_system_prompt=True,
            cache=False
        )

    @agent
    def final_refinement_agent(self) -> Agent:
        return Agent(
            role="Final Refiner",
            goal=(
                "Take the legally reviewed guide and finalize it. Output full markdown, ensure no optional disclaimers if mandatory. "
                "Return final with {{ 'final_style_guide':..., 'notes':[] }}."
            ),
            backstory="Ensures the final markdown is consistent, instructions are mandatory, no leftover placeholders, etc.",
            llm=self.llm,
            memory=True,
            verbose=False,
            allow_delegation=False,
            respect_context_window=True,
            use_system_prompt=True,
            cache=False
        )

    # Tasks
    # -----------------------------------------------------------------------
    @task
    def knowledge_retrieval_task(self) -> Task:
        description = r"""
**INSTRUCTIONS**:
1. Summarize or unify content from the knowledge sources (baseline + legal).
2. Output strictly JSON:
   {{
     "baseline_rules_summary":"...",
     "legal_guidelines_summary":"..."
   }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"baseline_rules_summary":"","legal_guidelines_summary":""}}',
            agent=self.knowledge_agent()
        )

    @task
    def domain_breakdown_task(self) -> Task:
        description = r"""
We have knowledge retrieval:
{{output from knowledge_retrieval_task}}

**INSTRUCTIONS**:
1. Outline domain-level constraints for {category}, referencing baseline_rules_summary + legal_guidelines_summary.
2. Return JSON:
   {{"category_insights":[ "...some bullet points..." ]}}
No commentary outside JSON.
"""
        return Task(
            description=description,
            expected_output='{{"category_insights":[]}}',
            agent=self.domain_breakdown_agent(),
            context=[self.knowledge_retrieval_task()]
        )

    @task
    def product_type_task(self) -> Task:
        description = r"""
We have domain breakdown:
{{output from domain_breakdown_task}}

We also have productType: {product_type}
Fields: {fields_needed}

**INSTRUCTIONS**:
1. Provide guidelines for each field, referencing domain breakdown + baseline + legal. 
2. Return strictly JSON:
   {{
     "product_type_analysis": "...some text about {product_type} specifics...",
     "field_guidelines": [
       {{"field":"title","notes":[]}},
       {{"field":"shortDesc","notes":[]}},
       {{"field":"longDesc","notes":[]}}
     ]
   }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"product_type_analysis":"","field_guidelines":[]}}',
            agent=self.product_type_agent(),
            context=[self.domain_breakdown_task()]
        )

    @task
    def schema_inference_task(self) -> Task:
        description = r"""
We have product_type_task output:
{{output}}

**INSTRUCTIONS**:
1. Propose final style guide schema with mandatory fields. 
2. Return JSON:
   {{
     "final_schema": "...",
     "schema_details": [...]
   }}
No commentary.
"""
        return Task(
            description=description,
            expected_output='{{"final_schema":"","schema_details":[]}}',
            agent=self.schema_inference_agent(),
            context=[self.product_type_task()]
        )

    @task
    def style_guide_construction_task(self) -> Task:
        description = r"""
Domain breakdown + product type analysis + schema inference in context:
{{output from schema_inference_task}}

**INSTRUCTIONS**:
1. Build a cohesive style guide draft. Possibly partial markdown. 
2. Return strictly JSON:
   {{ "draftStyleGuide":"..." }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"draftStyleGuide":"..."}}',
            agent=self.style_guide_construction_agent(),
            context=[self.schema_inference_task()]
        )

    @task
    def legal_review_task(self) -> Task:
        description = r"""
Draft style guide:
{{output}}

**INSTRUCTIONS**:
1. Check brand/IP compliance thoroughly, referencing legal guidelines. 
2. If issues, revise them. 
3. Return strictly JSON:
   {{ "legally_reviewed_guide":"...", "legal_issues_found":[ ... ] }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"legally_reviewed_guide":"","legal_issues_found":[]}}',
            agent=self.legal_review_agent(),
            context=[self.style_guide_construction_task()]
        )

    @task
    def final_refinement_task(self) -> Task:
        description = r"""
We have a legally reviewed style guide:
{{output}}

**INSTRUCTIONS**:
1. Finalize it. Return full markdown in "final_style_guide". 
2. Return strictly JSON:
   {{
     "final_style_guide":"...",
     "notes":[]
   }}
No extra commentary or extra fields.
"""
        return Task(
            description=description,
            expected_output='{{"final_style_guide":"","notes":[]}}',
            agent=self.final_refinement_agent(),
            context=[self.legal_review_task()],
            output_pydantic=StyleGuideOutput
        )

    # Optionally, store the final style guide in published_style_guides
    @after_kickoff
    def store_final_guide(self, output):
        """
        Safely extract 'final_style_guide' from the final result,
        then insert into 'published_style_guides' in SQLite.
        """
        # 1) Check .json_dict first
        final_data = output.json_dict
        
        # 2) If no json_dict, try to parse output.raw
        if not final_data:
            try:
                final_data = json.loads(output.raw)
            except (json.JSONDecodeError, TypeError):
                final_data = {}

        # 3) Ensure final_data is a dict and check if 'final_style_guide' is present
        if isinstance(final_data, dict) and "final_style_guide" in final_data:
            style_guide_md = final_data["final_style_guide"]
            category = self.inputs.get("category", "Unspecified")
            product_type = self.inputs.get("product_type", "Unspecified")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            insert_query = """
                INSERT INTO published_style_guides
                (category, product_type, style_guide_md, created_at, updated_at)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """
            cursor.execute(insert_query, (category, product_type, style_guide_md))
            conn.commit()
            cursor.close()
            conn.close()

        return output

    @crew
    def crew(self) -> Crew:
        cat = self.inputs.get("category","Fashion")
        pt = self.inputs.get("product_type","ALL")
        domain = cat  # or separate domain param

        baseline_source = BaselineStyleKnowledgeSource(category=cat, product_type=pt, db_path=self.db_path)
        legal_source = LegalKnowledgeSource(domain=domain, db_path=self.db_path)

        return Crew(
            agents=[
                self.knowledge_agent(),
                self.domain_breakdown_agent(),
                self.product_type_agent(),
                self.schema_inference_agent(),
                self.style_guide_construction_agent(),
                self.legal_review_agent(),
                self.final_refinement_agent()
            ],
            tasks=[
                self.knowledge_retrieval_task(),
                self.domain_breakdown_task(),
                self.product_type_task(),
                self.schema_inference_task(),
                self.style_guide_construction_task(),
                self.legal_review_task(),
                self.final_refinement_task()
            ],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=[baseline_source, legal_source]
        )
