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
     4) Thoroughly builds style guides for each 'field' in fields_needed:
        - title
        - shortDesc
        - longDesc
     5) Performs an exhaustive legal review for each field snippet
     6) Final refinement for each field snippet
     7) (Optional) Store each snippet in 'published_style_guides' with field_name= 'title','shortDesc','longDesc'
    """

    def __init__(self, llm_model="openai/gpt-4o-mini", db_path="style_guide.db"):
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
            backstory=(
                "This agent pinpoints how {product_type} might differ within {category}, referencing baseline + legal guidelines, "
                "and addresses each field specifically."
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
    def schema_inference_agent(self) -> Agent:
        return Agent(
            role="Schema Inference",
            goal="Propose a final style guide schema, ensuring no optional placeholders—everything is mandatory.",
            backstory=(
                "This agent ensures there's a well-defined JSON or markdown structure for the final style guide. "
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
                "Using the domain breakdown, product-type analysis, and schema inference, create a robust style guide for each field. "
                "We handle 'title', 'shortDesc', and 'longDesc' separately."
            ),
            backstory="This agent merges all constraints into an initial draft text for each field.",
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
                "Check the draft style guide snippet for brand/IP compliance. If it references competitors or violates disclaimers, "
                "revise or highlight them. Return a legally reviewed version."
            ),
            backstory="Thoroughly applies brand usage constraints, disclaimers, avoiding 'guarantees', etc. for each snippet.",
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
                "Take the legally reviewed snippet and finalize it for the specified field. Output full markdown, no optional disclaimers. "
                "Return final with {{ 'style_guide_snippet':..., 'notes':[] }}."
            ),
            backstory="Ensures final snippet is consistent, instructions are mandatory, no leftover placeholders.",
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
   {{
     "category_insights":[ "...some bullet points..." ]
   }}
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
       {{
         "field":"title",
         "notes":[]
       }},
       {{
         "field":"shortDesc",
         "notes":[]
       }},
       {{
         "field":"longDesc",
         "notes":[]
       }}
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

    #
    # PHASE: Generate style guides for each field
    #

    #
    # 1) Title generation
    #
    @task
    def title_guide_construction_task(self) -> Task:
        description = r"""
We have domain breakdown + product type analysis + schema inference in context:
{{output from schema_inference_task}}

**INSTRUCTIONS**:
1. Build a style guide snippet specifically for the 'title' field. Possibly partial markdown.
2. Return strictly JSON:
   {{
     "draftTitleGuide":"..."
   }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"draftTitleGuide":""}}',
            agent=self.style_guide_construction_agent(),
            context=[self.schema_inference_task()]
        )

    @task
    def title_legal_review_task(self) -> Task:
        description = r"""
We have a draft Title snippet:
{{output}}

**INSTRUCTIONS**:
1. Check brand/IP compliance thoroughly for the Title snippet. 
2. If issues, revise them. 
3. Return strictly JSON:
   {{
     "legally_reviewed_title":"...",
     "title_legal_issues":[ ... ]
   }}
No commentary.
"""
        return Task(
            description=description,
            expected_output='{{"legally_reviewed_title":"","title_legal_issues":[]}}',
            agent=self.legal_review_agent(),
            context=[self.title_guide_construction_task()]
        )

    @task
    def title_final_refine_task(self) -> Task:
        description = r"""
We have a legally reviewed Title snippet:
{{output}}

**INSTRUCTIONS**:
1. Finalize the Title snippet in full markdown.
2. Return strictly JSON:
   {{
     "title_guide":"...",
     "notes":[]
   }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"title_guide":"","notes":[]}}',
            agent=self.final_refinement_agent(),
            context=[self.title_legal_review_task()]
        )

    #
    # 2) ShortDesc generation
    #
    @task
    def shortdesc_guide_construction_task(self) -> Task:
        description = r"""
We have domain/product-type context + schema inference:
{{output from schema_inference_task}}

**INSTRUCTIONS**:
1. Build a style guide snippet for the 'shortDesc' field. Possibly partial markdown.
2. Return strictly JSON:
   {{
     "draftShortDescGuide":"..."
   }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"draftShortDescGuide":""}}',
            agent=self.style_guide_construction_agent(),
            context=[self.schema_inference_task()]
        )

    @task
    def shortdesc_legal_review_task(self) -> Task:
        description = r"""
We have a draft ShortDesc snippet:
{{output}}

**INSTRUCTIONS**:
1. Check brand/IP compliance thoroughly for the shortDesc snippet. 
2. If issues, revise them. 
3. Return strictly JSON:
   {{
     "legally_reviewed_shortdesc":"...",
     "shortdesc_legal_issues":[ ... ]
   }}
No commentary.
"""
        return Task(
            description=description,
            expected_output='{{"legally_reviewed_shortdesc":"","shortdesc_legal_issues":[]}}',
            agent=self.legal_review_agent(),
            context=[self.shortdesc_guide_construction_task()]
        )

    @task
    def shortdesc_final_refine_task(self) -> Task:
        description = r"""
We have a legally reviewed shortDesc snippet:
{{output}}

**INSTRUCTIONS**:
1. Finalize the shortDesc snippet in full markdown.
2. Return strictly JSON:
   {{
     "shortDesc_guide":"...",
     "notes":[]
   }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"shortDesc_guide":"","notes":[]}}',
            agent=self.final_refinement_agent(),
            context=[self.shortdesc_legal_review_task()]
        )

    #
    # 3) LongDesc generation
    #
    @task
    def longdesc_guide_construction_task(self) -> Task:
        description = r"""
We have domain/product-type context + schema inference:
{{output from schema_inference_task}}

**INSTRUCTIONS**:
1. Build a style guide snippet for the 'longDesc' field. Possibly partial markdown.
2. Return strictly JSON:
   {{
     "draftLongDescGuide":"..."
   }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"draftLongDescGuide":""}}',
            agent=self.style_guide_construction_agent(),
            context=[self.schema_inference_task()]
        )

    @task
    def longdesc_legal_review_task(self) -> Task:
        description = r"""
We have a draft longDesc snippet:
{{output}}

**INSTRUCTIONS**:
1. Check brand/IP compliance thoroughly for the longDesc snippet. 
2. If issues, revise them. 
3. Return strictly JSON:
   {{
     "legally_reviewed_longdesc":"...",
     "longdesc_legal_issues":[ ... ]
   }}
No commentary.
"""
        return Task(
            description=description,
            expected_output='{{"legally_reviewed_longdesc":"","longdesc_legal_issues":[]}}',
            agent=self.legal_review_agent(),
            context=[self.longdesc_guide_construction_task()]
        )

    @task
    def longdesc_final_refine_task(self) -> Task:
        description = r"""
We have a legally reviewed longDesc snippet:
{{output}}

**INSTRUCTIONS**:
1. Finalize the longDesc snippet in full markdown.
2. Return strictly JSON:
   {{
     "longDesc_guide":"...",
     "notes":[]
   }}
No extra commentary.
"""
        return Task(
            description=description,
            expected_output='{{"longDesc_guide":"","notes":[]}}',
            agent=self.final_refinement_agent(),
            context=[self.longdesc_legal_review_task()]
        )

    # after_kickoff to store final snippet
    @after_kickoff
    def store_final_guide(self, output):
        """
        Safely parse final result for 'title_guide', 'shortDesc_guide', 'longDesc_guide'.
        Insert each snippet into published_style_guides table with field_name='title','shortDesc','longDesc'.
        """
        import json

        final_data = output.json_dict
        if not final_data:
            try:
                final_data = json.loads(output.raw)
            except (json.JSONDecodeError, TypeError):
                final_data = {}

        category = self.inputs.get("category","Unspecified")
        product_type = self.inputs.get("product_type","Unspecified")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        def store_snippet(field_key):
            if field_key in final_data:
                snippet_md = final_data[field_key]
                insert_query = """
                  INSERT INTO published_style_guides
                  (category, product_type, field_name, style_guide_md, created_at, updated_at)
                  VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                """
                cursor.execute(insert_query, (category, product_type, field_key, snippet_md))

        # Attempt to store each snippet if present
        store_snippet("title_guide")
        store_snippet("shortDesc_guide")
        store_snippet("longDesc_guide")

        conn.commit()
        cursor.close()
        conn.close()

        return output

    @crew
    def crew(self) -> Crew:
        """
        Steps:
          1) knowledge_retrieval_task
          2) domain_breakdown_task
          3) product_type_task
          4) schema_inference_task
          5) title_guide_construction_task -> title_legal_review_task -> title_final_refine_task
          6) shortdesc_guide_construction_task -> shortdesc_legal_review_task -> shortdesc_final_refine_task
          7) longdesc_guide_construction_task -> longdesc_legal_review_task -> longdesc_final_refine_task
        Then store final guides after kickoff.
        """
        cat = self.inputs.get("category","Fashion")
        pt = self.inputs.get("product_type","ALL")
        domain = cat  # or separate

        baseline_source = BaselineStyleKnowledgeSource(category=cat, product_type=pt, db_path=self.db_path)
        legal_source = LegalKnowledgeSource(domain=domain, db_path=self.db_path)

        return Crew(
            agents=[
                self.knowledge_agent(),
                self.domain_breakdown_agent(),
                self.product_type_agent(),
                self.schema_inference_agent(),

                self.style_guide_construction_agent(), # used for all field tasks
                self.legal_review_agent(),
                self.final_refinement_agent(),
            ],
            tasks=[
                # Common plan tasks
                self.knowledge_retrieval_task(),
                self.domain_breakdown_task(),
                self.product_type_task(),
                self.schema_inference_task(),

                # Title field sub-flow
                self.title_guide_construction_task(),
                self.title_legal_review_task(),
                self.title_final_refine_task(),

                # shortDesc field sub-flow
                self.shortdesc_guide_construction_task(),
                self.shortdesc_legal_review_task(),
                self.shortdesc_final_refine_task(),

                # longDesc field sub-flow
                self.longdesc_guide_construction_task(),
                self.longdesc_legal_review_task(),
                self.longdesc_final_refine_task(),
            ],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=[baseline_source, legal_source]
        )
