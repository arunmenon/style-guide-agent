# style_guide_gen/style_guide_gen/schemas.py

from pydantic import BaseModel
from typing import List

class StyleGuideOutput(BaseModel):
    final_style_guide: str
    notes: List[str] = []
    # If you want to store the legal or version references, you can add them here, e.g.:
    # legal_findings: List[str] = []
    # version: int = 1
