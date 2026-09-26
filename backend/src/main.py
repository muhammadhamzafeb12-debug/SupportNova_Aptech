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
    reports,
    reviewer,
    sla,
    admin_analytics,
)

env_name = os.getenv("ENVIRONMENT", "development").lower()
default_docs = "true" if env_name not in ("production", "prod") else "false"
enable_docs = os.getenv("ENABLE_DOCS", default_docs).lower() == "true"

app = FastAPI(
    title="SupportNova API",
    description="AI-Powered Customer Complaint Resolution & Dual-Pipeline Intelligence System",
    version="2.0.0",
    docs_url="/docs" if enable_docs else None,
    redoc_url="/redoc" if enable_docs else None
)

# CORS Configuration
cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
raw_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

if raw_origins:
    origins = list(set(raw_origins + default_origins))
else:
    origins = ["*"]

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
app.include_router(reviewer.router)
app.include_router(sla.admin_router)
app.include_router(sla.sla_router)
app.include_router(admin_analytics.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.main:app", host="0.0.0.0", port=8000, reload=True)
