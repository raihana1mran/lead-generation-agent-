from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Lead, LeadIntelligence, AgentLog, BusinessProfile, Proposal, Message, FollowUp
from pydantic import BaseModel
from typing import List, Optional
from engine.events import trigger_lead_enrichment, trigger_lead_scoring
from engine.state_machine import WorkflowState
from agents.all_agents import LeadDiscoveryAgent

router = APIRouter(prefix="/api/leads", tags=["Leads"])

class LeadCreate(BaseModel):
    company_name: str
    website: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = "Manual"
    workspace_id: Optional[str] = "default"

class AutoGenerateRequest(BaseModel):
    query: str

class LeadIntelligenceResponse(BaseModel):
    id: int
    lead_id: int
    size: Optional[str] = None
    revenue_estimate: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    hiring_status: Optional[bool] = None
    digital_presence_score: Optional[int] = None
    lead_score: Optional[int] = None
    classification: Optional[str] = None
    website_audit: Optional[dict] = None
    ai_opportunities: Optional[dict] = None
    personalized_message: Optional[dict] = None
    outreach_status: Optional[dict] = None
    followups: Optional[dict] = None
    meeting_booking: Optional[dict] = None
    crm_update: Optional[dict] = None

    class Config:
        from_attributes = True

class LeadResponse(LeadCreate):
    id: int
    workflow_state: str
    requires_hitl: bool
    intelligence: Optional[LeadIntelligenceResponse] = None

    class Config:
        from_attributes = True

@router.post("/", response_model=LeadResponse)
def create_lead(lead: LeadCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_lead = Lead(**lead.model_dump())
    db_lead.requires_hitl = True  # Enable approval gate by default
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    # Event Trigger: Lead Imported -> Start enrichment
    background_tasks.add_task(trigger_lead_enrichment, db_lead.id)
    
    return db_lead

def run_auto_discovery(query: str, workspace_id: str):
    db = next(get_db())
    saved = 0
    try:
        agent = LeadDiscoveryAgent()
        result = agent.run({"query": query})

        # Use the raw dict list — no LLM parsing needed
        raw_leads = getattr(result, "_raw", [])
        print(f"[AutoDiscovery] Processing {len(raw_leads)} raw leads from scraper")

        for lead_data in raw_leads:
            try:
                # Skip if company already exists
                exists = db.query(Lead).filter(Lead.company_name == lead_data["company_name"]).first()
                if exists:
                    continue

                db_lead = Lead(
                    company_name=lead_data.get("company_name", "Unknown"),
                    website=lead_data.get("website"),
                    contact_person=lead_data.get("contact_person"),
                    email=lead_data.get("email"),
                    linkedin=lead_data.get("linkedin"),
                    location=lead_data.get("location"),
                    source=lead_data.get("source", "AI Discovery"),
                    workspace_id=workspace_id,
                    workflow_state=WorkflowState.INGESTED.value,
                    requires_hitl=True  # Enable approval gate by default
                )
                db.add(db_lead)
                db.commit()
                db.refresh(db_lead)
                saved += 1
                print(f"[AutoDiscovery] + Saved lead #{db_lead.id}: {db_lead.company_name}")

                # Kick off the 15-state enrichment pipeline
                trigger_lead_enrichment(db_lead.id)

            except Exception as e:
                print(f"[AutoDiscovery] ! Failed to save lead: {e}")
                db.rollback()

        print(f"[AutoDiscovery] DONE. Saved {saved} new leads to database.")

    except Exception as e:
        print(f"[AutoDiscovery] ERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()

@router.post("/auto-generate")
def auto_generate_leads(request: AutoGenerateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Triggers the Lead Discovery Agent to scrape Google/Quora/Instagram 
    and automatically ingest leads into the workflow engine.
    """
    background_tasks.add_task(run_auto_discovery, request.query, "default")
    return {"message": "Auto Lead Generation started in the background. Check the dashboard for updates."}

@router.get("/", response_model=List[LeadResponse])
def get_leads(db: Session = Depends(get_db)):
    return db.query(Lead).all()

@router.get("/{id}", response_model=LeadResponse)
def get_lead(id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.post("/search", response_model=List[LeadResponse])
def search_leads(filters: dict, db: Session = Depends(get_db)):
    # Basic mock search implementation
    query = db.query(Lead)
    if "workflow_state" in filters:
        query = query.filter(Lead.workflow_state == filters["workflow_state"])
    return query.all()

@router.post("/{id}/score")
def score_lead(id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Event Trigger: Lead Scored
    lead = db.query(Lead).filter(Lead.id == id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    background_tasks.add_task(trigger_lead_scoring, lead.id)
    return {"message": "Scoring task queued"}

@router.delete("/{id}")
def delete_lead(id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # 1. Delete followups of messages
    for msg in lead.messages:
        db.query(FollowUp).filter(FollowUp.message_id == msg.id).delete()
    
    # 2. Delete messages
    db.query(Message).filter(Message.lead_id == lead.id).delete()
    
    # 3. Delete proposals
    db.query(Proposal).filter(Proposal.lead_id == lead.id).delete()
    
    # 4. Delete intelligence
    db.query(LeadIntelligence).filter(LeadIntelligence.lead_id == lead.id).delete()
    
    # 5. Delete lead
    db.delete(lead)
    db.commit()
    return {"message": f"Lead {id} and all related data deleted successfully"}

@router.delete("/")
def delete_all_leads(db: Session = Depends(get_db)):
    # 1. Delete all followups
    db.query(FollowUp).delete()
    # 2. Delete all messages
    db.query(Message).delete()
    # 3. Delete all proposals
    db.query(Proposal).delete()
    # 4. Delete all intelligence
    db.query(LeadIntelligence).delete()
    # 5. Delete all leads
    db.query(Lead).delete()
    db.commit()
    return {"message": "All leads and associated data cleared successfully"}

