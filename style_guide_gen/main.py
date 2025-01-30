# style_guide_gen/main.py
from fastapi import FastAPI
from style_guide_gen.style_guide_gen.api.routers.style_guide import router as style_guide_router

app = FastAPI()

app.include_router(style_guide_router, prefix="/style-guide", tags=["StyleGuide"])
