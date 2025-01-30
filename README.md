# **StyleGuideCrew – README**

## **Overview**

The **StyleGuideCrew** is a multi-step workflow in CrewAI that **automates the creation of style guide snippets** (for *title*, *shortDesc*, and *longDesc*) to ensure product descriptions meet **domain** and **legal** standards. Each snippet is thoroughly reviewed and refined to guarantee consistency, clarity, and compliance with brand/IP constraints.

## **High-Level Flow**

1. **Knowledge Retrieval**  
   - A specialized agent aggregates domain & product-type guidelines (baseline rules) plus brand/legal guidelines from a **knowledge base**.  
2. **Domain Breakdown**  
   - Analyzes the broader domain constraints (e.g., “Fashion”) to distill big-picture rules.  
3. **Product Type Analysis**  
   - Pinpoints how these constraints apply specifically to the given product type (like “Men’s T-Shirt”) for each field.  
4. **Schema Inference**  
   - Defines the final structure (fields, disclaimers) for the style guide.  
5. **Field-Specific Creation**  
   - For each field—**title**, **shortDesc**, **longDesc**—the crew constructs a snippet, runs a legal compliance review, and finalizes it.  
6. **Persistence**  
   - Each snippet is then stored or published as an official style guide resource (e.g., for internal grading or user-facing references).

---

## **Core Components**

### **Knowledge Base**

Two **knowledge sources** supply domain/baseline rules and legal constraints:

- **BaselineStyleKnowledgeSource**:  
  - Provides best practices for a given `{category, product_type}` from a stored knowledge base.  
  - If no exact match, can fall back to a general rule set (e.g., `'ALL'`).  

- **LegalKnowledgeSource**:  
  - Delivers brand/IP usage guidelines relevant to your domain (e.g., disclaimers, trademark usage).  
  - Falls back to universal or `'ALL'` if no domain match.

### **Agents and Their Tasks**

1. **Knowledge Agent**  
   - Gathers domain, product-type, and legal guidelines from the knowledge base.  
   - Produces a unified JSON with `baseline_rules_summary` + `legal_guidelines_summary`.

2. **Domain Breakdown Agent**  
   - Consumes that knowledge summary.  
   - Outputs high-level category/domain constraints.

3. **Product Type Agent**  
   - Merges domain breakdown with product-type specifics, enumerating each field’s requirements.  

4. **Schema Inference Agent**  
   - Finalizes the data structure for the style guide, ensuring mandatory fields (title/shortDesc/longDesc).

5. **Style Guide Construction Agent**  
   - Builds a **draft** snippet for each field.  
   - For example, “draftTitleGuide” or “draftShortDescGuide.”

6. **Legal Review Agent**  
   - Checks each snippet for brand/IP compliance.  
   - Revises or flags issues if it sees competitor references or unsubstantiated claims.

7. **Final Refiner Agent**  
   - Produces a strictly valid JSON object with `"title_guide"`, `"shortDesc_guide"`, or `"longDesc_guide"`.  
   - This is the final snippet in readable markdown.

---

## **Detailed Step-by-Step**

1. **knowledge_retrieval_task**  
   - Agent: *Knowledge Aggregator*  
   - Summarizes domain/baseline + legal guidelines.  
   - Output: `{"baseline_rules_summary":"","legal_guidelines_summary":""}`

2. **domain_breakdown_task**  
   - Agent: *Domain Breakdown*  
   - Merges knowledge retrieval, yielding `{"category_insights":[]}`.

3. **product_type_task**  
   - Agent: *Product Type Analyzer*  
   - Explains each field’s guidelines for `(category, product_type)`.

4. **schema_inference_task**  
   - Agent: *Schema Inference*  
   - Proposes `{"final_schema":"","schema_details":[]}` listing mandatory fields.

### **Subflows for Each Field**

Assuming `fields_needed` includes `"title"`, `"shortDesc"`, `"longDesc"`, we do:

1. **Title**:
   - **Construction** (`title_guide_construction_task`): yields `{"draftTitleGuide":""}`
   - **Legal Review** (`title_legal_review_task`): yields `{"legally_reviewed_title":""}`
   - **Final Refinement** (`title_final_refine_task`): yields `{"title_guide":"...","notes":[]}`

2. **ShortDesc**:
   - **Construction** → `{"draftShortDescGuide":""}`
   - **Legal Review** → `{"legally_reviewed_shortdesc":""}`
   - **Final Refinement** → `{"shortDesc_guide":"...","notes":[]}`

3. **LongDesc**:
   - **Construction** → `{"draftLongDescGuide":""}`
   - **Legal Review** → `{"legally_reviewed_longdesc":""}`
   - **Final Refinement** → `{"longDesc_guide":"...","notes":[]}`

### **Persistence**

An **`@after_kickoff`** method scans the final JSON result for each snippet key (`"title_guide"`, `"shortDesc_guide"`, `"longDesc_guide"`) and stores them, each with a `field_name`, enabling you to track or version the final style guides.

---

## **Why This Agentic Flow**

- **Granularity**: Each field (title, shortDesc, longDesc) is generated, legally reviewed, and refined independently.  
- **Robust**: The multi-step design ensures domain breakdown, product-type constraints, and legal compliance are carefully integrated.  
- **Extensible**: If you later need more fields or a new domain, just add tasks or knowledge source rows.  
- **Compliant**: The legal review step flags disclaimers, competitor references, trademark usage, etc.

---

## **Key Files**

1. **`crew.py`**: Defines the tasks and agents (this file).  
2. **`db_knowledge.py`** (or a knowledge module): Custom knowledge sources for retrieving domain + legal data.  
3. **`schemas.py`**: Pydantic classes for typed final outputs (like `StyleGuideOutput`).  
4. **`main.py`** / **API Router**: Exposes a route, e.g. `/style-guide/generate`, that calls `StyleGuideCrew().crew().kickoff(inputs=...)`.

---

## **Conclusion**

The **StyleGuideCrew** orchestrates a comprehensive pipeline to produce field-specific style guides for product listings in your domain. By referencing a dedicated knowledge base and running each snippet through a multi-step creation + legal compliance check, the final style guides are thorough, brand-aligned, and easily persisted for future usage.