from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import BusinessProfile, AgentLog
from pydantic import BaseModel
from typing import List, Optional
from engine.events import trigger_business_agent

router = APIRouter(prefix="/api/business", tags=["Business Profile"])

class BusinessProfileCreate(BaseModel):
    company_name: str
    industry: str
    services: List[str]
    target_customers: str
    pricing: str
    geography: str

class BusinessProfileResponse(BusinessProfileCreate):
    id: int
    icp: Optional[dict] = None

    class Config:
        from_attributes = True

@router.post("/", response_model=BusinessProfileResponse)
def create_business(profile: BusinessProfileCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_profile = BusinessProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    # Event Trigger: Business Profile Created -> Generate ICP
    background_tasks.add_task(trigger_business_agent, db_profile.id)
    
    return db_profile

@router.get("/", response_model=List[BusinessProfileResponse])
def get_businesses(db: Session = Depends(get_db)):
    return db.query(BusinessProfile).all()
