# style_guide_gen/main.py
from fastapi import FastAPI
from crew_flow.api.routers.style_guide import router as style_guide_router

app = FastAPI()

app.include_router(style_guide_router, prefix="/style-guide", tags=["StyleGuide"])
