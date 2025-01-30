# style_guide_gen/style_guide_gen/api/routers/style_guide.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from crew_flow.crew import StyleGuideCrew

router = APIRouter()

class StyleGuideRequest(BaseModel):
    category: str
    product_type: str
    fields_needed: List[str] = ["title","shortDesc","longDesc"]

@router.post("/generate")
def generate_style_guide(req: StyleGuideRequest):
    # We assume "style_guide.db" is in your project root
    crew_instance = StyleGuideCrew(db_path="style_guide.db")
    result = crew_instance.crew().kickoff(inputs=req.dict())

    final_data = result.json_dict or result.raw
    if not final_data:
        raise HTTPException(status_code=500, detail="No style guide generated.")
    return final_data
