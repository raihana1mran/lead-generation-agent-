from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import GeographyConfig
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/geography", tags=["Geography"])

class GeographyConfigSchema(BaseModel):
    tier1_countries: List[str]
    tier2_countries: List[str]
    tier3_countries: List[str]
    active_tiers: List[str]
    platforms: List[str]

    class Config:
        from_attributes = True

@router.get("/")
def get_geography_config(db: Session = Depends(get_db)):
    configs = db.query(GeographyConfig).filter_by(workspace_id="default").all()
    if not configs:
        # Return defaults if none configured
        return [{
            "id": None,
            "tier1_countries": ["USA", "UK", "Canada", "Australia", "Germany"],
            "tier2_countries": ["India", "UAE", "Singapore", "Brazil", "Netherlands", "France"],
            "tier3_countries": ["Philippines", "Nigeria", "Kenya", "Pakistan", "South Africa"],
            "active_tiers": ["tier1"],
            "platforms": ["linkedin", "instagram", "tiktok", "quora", "pinterest"]
        }]
    return configs

@router.post("/")
def save_geography_config(config: GeographyConfigSchema, db: Session = Depends(get_db)):
    existing = db.query(GeographyConfig).filter_by(workspace_id="default").first()
    if existing:
        existing.tier1_countries = config.tier1_countries
        existing.tier2_countries = config.tier2_countries
        existing.tier3_countries = config.tier3_countries
        existing.active_tiers = config.active_tiers
        existing.platforms = config.platforms
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_config = GeographyConfig(
            workspace_id="default",
            tier1_countries=config.tier1_countries,
            tier2_countries=config.tier2_countries,
            tier3_countries=config.tier3_countries,
            active_tiers=config.active_tiers,
            platforms=config.platforms
        )
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        return new_config
