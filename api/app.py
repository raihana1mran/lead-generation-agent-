from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database.database import engine
from database.models import Base
import os

# We already run alembic, but this is a fallback
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LeadForge AI API",
    description="Enterprise Lead Generation & Proposal AI System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static storage
app.mount("/static", StaticFiles(directory="storage"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to LeadForge AI API"}

from api.routes import auth, business, leads, proposals, outreach, analytics, workflow, geography

app.include_router(auth.router)
app.include_router(business.router)
app.include_router(leads.router)
app.include_router(proposals.router)
app.include_router(outreach.router)
app.include_router(analytics.router)
app.include_router(workflow.router)
app.include_router(geography.router)
