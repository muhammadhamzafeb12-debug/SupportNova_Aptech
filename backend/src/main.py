"""
SupportNova FastAPI Main Application Entrypoint
"""
import os
import sys
from pathlib import Path

# Ensure root workspace is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.db import init_db
from backend.src.api import (
    auth,
    complaints,
    knowledge_base,
    admin_kb,
    rule_matrix,
    genai_pipeline,
    validation,
    comparison,
    dashboards,
    reports
)

enable_docs = os.getenv("ENABLE_DOCS", "true").lower() == "true"

app = FastAPI(
    title="SupportNova API",
    description="AI-Powered Customer Complaint Resolution & Dual-Pipeline Intelligence System",
    version="2.0.0",
    docs_url="/docs" if enable_docs else None,
    redoc_url="/redoc" if enable_docs else None
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# Mount Routers
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(knowledge_base.router)
app.include_router(admin_kb.router)
app.include_router(rule_matrix.router)
app.include_router(rule_matrix.public_router)
app.include_router(genai_pipeline.router)
app.include_router(validation.router)
app.include_router(comparison.router)
app.include_router(dashboards.router)
app.include_router(reports.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.main:app", host="0.0.0.0", port=8000, reload=True)
