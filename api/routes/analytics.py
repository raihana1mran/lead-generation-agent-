from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Analytics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/")
def get_analytics(db: Session = Depends(get_db)):
    return db.query(Analytics).all()

@router.get("/dashboard")
def get_dashboard_summary(db: Session = Depends(get_db)):
    # Mock dashboard payload based on DB metrics
    metrics = db.query(Analytics).all()
    summary = {m.metric_name: m.metric_value for m in metrics}
    return {"dashboard": summary}
