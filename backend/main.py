import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base
from backend.api.routes import router as api_router
from backend.database_seed import seed_database

app = FastAPI(
    title=settings.APP_NAME,
    description="ResponseX Intelligence - Generative AI & Independent Ground-Truth Complaint Resolution System for NovaCart Technologies",
    version="1.0.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
def on_startup():
    # Initialize DB schema
    Base.metadata.create_all(bind=engine)
    # Seed default dataset and demo records
    seed_database()

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "ONLINE",
        "organization": "NovaCart Technologies",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
