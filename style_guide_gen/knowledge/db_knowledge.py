# style_guide_gen/knowledge/db_knowledge.py

import sqlite3
from typing import Dict, Any
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

# style_guide_gen/crew_flow/knowledge/db_knowledge.py
import sqlite3
from typing import Dict, Any
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

class BaselineStyleKnowledgeSource(BaseKnowledgeSource):
    """
    Fetch baseline style guidelines from an SQLite DB for the given category/product_type.
    Also implements 'add()' so we can finalize the knowledge chunks in CrewAI.
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

    def add(self) -> None:
        """
        Required method to chunk + store the loaded text in self.chunks, then persist in self._save_documents().
        """
        content_dict = self.load_content()
        for _, text in content_dict.items():
            # Use the built-in chunking method from BaseKnowledgeSource
            chunks = self._chunk_text(text)
            self.chunks.extend(chunks)

        # Now store them so that the knowledge is available
        self._save_documents()
    
class LegalKnowledgeSource(BaseKnowledgeSource):
    """
    Fetch domain-specific or fallback 'ALL' legal guidelines from SQLite.
    """
    domain: str
    db_path: str

    def load_content(self) -> Dict[Any, str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query_domain = """
            SELECT legal_text
            FROM legal_guidelines
            WHERE domain = ?
            LIMIT 1
        """
        cursor.execute(query_domain, (self.domain,))
        row = cursor.fetchone()

        if row:
            guidelines = row[0]
        else:
            # fallback to domain='ALL'
            query_all = """
                SELECT legal_text
                FROM legal_guidelines
                WHERE domain = 'ALL'
                LIMIT 1
            """
            cursor.execute(query_all)
            row_all = cursor.fetchone()
            guidelines = row_all[0] if row_all else ""

        cursor.close()
        conn.close()

        key = f"legal_{self.domain}"
        return {key: guidelines or ""}

    def add(self) -> None:
        """
        Implement the add method for the legal knowledge:
        chunk and store the text so the agent can query it.
        """
        content_dict = self.load_content()
        for _, text in content_dict.items():
            chunks = self._chunk_text(text)
            self.chunks.extend(chunks)

        self._save_documents()
