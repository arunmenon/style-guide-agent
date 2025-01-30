# style_guide_gen/knowledge/db_knowledge.py

import sqlite3
from typing import Dict, Any
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

class BaselineStyleKnowledgeSource(BaseKnowledgeSource):
    """
    Fetch baseline style guidelines from an SQLite DB for the given category and product_type.
    We'll do a multi-tier fallback:
      1) (category, product_type) exactly
      2) (category, 'ALL') if no exact match
      3) (category, product_type IS NULL) if still not found
    """
    category: str
    product_type: str
    db_path: str

    def load_content(self) -> Dict[Any, str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1) Try exact category+product_type
        query_exact = """
        SELECT guidelines_text
        FROM baseline_style_guidelines
        WHERE category = ?
          AND product_type = ?
        LIMIT 1
        """
        cursor.execute(query_exact, (self.category, self.product_type))
        row_exact = cursor.fetchone()

        guidelines = ""
        if row_exact:
            guidelines = row_exact[0]
        else:
            # 2) fallback to 'ALL'
            query_all = """
            SELECT guidelines_text
            FROM baseline_style_guidelines
            WHERE category = ?
              AND product_type = 'ALL'
            LIMIT 1
            """
            cursor.execute(query_all, (self.category,))
            row_all = cursor.fetchone()

            if row_all:
                guidelines = row_all[0]
            else:
                # 3) fallback to product_type IS NULL
                query_null = """
                SELECT guidelines_text
                FROM baseline_style_guidelines
                WHERE category = ?
                  AND product_type IS NULL
                LIMIT 1
                """
                cursor.execute(query_null, (self.category,))
                row_null = cursor.fetchone()
                if row_null:
                    guidelines = row_null[0]

        cursor.close()
        conn.close()

        key = f"baseline_{self.category}_{self.product_type}"
        return {key: guidelines or ""}
