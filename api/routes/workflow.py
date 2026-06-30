from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Lead
from engine.state_machine import workflow_engine, WorkflowState
from engine.events import trigger_proposal_generation

router = APIRouter(prefix="/api/workflow", tags=["Workflow Engine"])

@router.post("/hitl/approve/{lead_id}")
def approve_lead_hitl(lead_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Unpauses a lead that was stuck in a HITL condition.
    - If in DECISION: Approves drafting proposal (moves to PROPOSAL).
    - If in PERSONALIZATION: Approves sending outreach message (moves to OUTREACH).
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    if not lead.requires_hitl:
        raise HTTPException(status_code=400, detail="Lead does not require human approval")
        
    from engine.events import trigger_outreach
    
    current_state = lead.workflow_state
    
    if current_state == WorkflowState.DECISION.value:
        # Trigger proposal generation bypassing the HITL gate
        background_tasks.add_task(trigger_proposal_generation, lead.id, False)
        return {"message": f"Lead {lead_id} approved. Proposal drafting started."}
        
    elif current_state == WorkflowState.PERSONALIZATION.value:
        # Trigger outreach sending bypassing the HITL gate
        background_tasks.add_task(trigger_outreach, lead.id, False)
        return {"message": f"Lead {lead_id} approved. Outreach sending started."}
        
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Lead is in state {current_state}, which is not an active approval gate."
        )

@router.get("/status/{lead_id}")
def get_workflow_status(lead_id: int, db: Session = Depends(get_db)):
    """
    Returns the exact state of a lead in the 10-state machine.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    return {
        "lead_id": lead.id,
        "company_name": lead.company_name,
        "workflow_state": lead.workflow_state,
        "requires_hitl": lead.requires_hitl
    }
