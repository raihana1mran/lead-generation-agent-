from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Proposal
from typing import List

router = APIRouter(prefix="/api/proposals", tags=["Proposals"])

@router.get("/")
def get_proposals(db: Session = Depends(get_db)):
    return db.query(Proposal).all()

@router.get("/{id}/pdf")
def get_proposal_pdf(id: int, db: Session = Depends(get_db)):
    # Mock PDF URL
    return {"pdf_url": f"http://localhost:8000/static/proposals/proposal_{id}.pdf"}
