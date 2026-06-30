from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, default="default", index=True)
    company_name = Column(String, index=True)
    industry = Column(String)
    services = Column(JSON)
    target_customers = Column(String)
    pricing = Column(String)
    geography = Column(String)
    icp = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GeographyConfig(Base):
    __tablename__ = "geography_config"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, default="default", index=True)
    tier1_countries = Column(JSON, default=lambda: ["USA", "UK", "Canada", "Australia", "Germany"])
    tier2_countries = Column(JSON, default=lambda: ["India", "UAE", "Singapore", "Brazil", "Netherlands", "France"])
    tier3_countries = Column(JSON, default=lambda: ["Philippines", "Pakistan", "Bangladesh", "Nigeria", "Kenya"])
    active_tiers = Column(JSON, default=lambda: ["tier1"])   # which tiers are currently enabled
    platforms = Column(JSON, default=lambda: ["linkedin", "instagram", "tiktok", "quora", "pinterest", "googlemaps"])
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, default="default", index=True)
    company_name = Column(String, index=True)
    website = Column(String)
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    location = Column(String, nullable=True)
    source = Column(String)
    workflow_state = Column(String, default="INGESTED") # INGESTED, ENRICHMENT, SCORING, DECISION, PROPOSAL, OUTREACH, FOLLOW_UP, RESPONSE, CRM_UPDATE, CLOSED_LOOP
    requires_hitl = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    intelligence = relationship("LeadIntelligence", back_populates="lead", uselist=False)
    proposal = relationship("Proposal", back_populates="lead", uselist=False)
    messages = relationship("Message", back_populates="lead")

class LeadIntelligence(Base):
    __tablename__ = "lead_intelligence"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    size = Column(String)
    revenue_estimate = Column(String)
    tech_stack = Column(JSON)
    hiring_status = Column(Boolean)
    digital_presence_score = Column(Integer)
    lead_score = Column(Integer, nullable=True)
    classification = Column(String, nullable=True)    # Phase 5 & 6 Additional Data
    website_audit = Column(JSON)
    ai_opportunities = Column(JSON)
    personalized_message = Column(JSON)
    
    # Phase 7 & 8 Additional Data
    outreach_status = Column(JSON)
    followups = Column(JSON)
    meeting_booking = Column(JSON)
    crm_update = Column(JSON)
    
    lead = relationship("Lead", back_populates="intelligence")

class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    title = Column(String)
    content = Column(JSON) # Store structured proposal
    proposal_url = Column(String, nullable=True) # PDF storage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    lead = relationship("Lead", back_populates="proposal")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    channel = Column(String) # EMAIL, LINKEDIN
    status = Column(String) # SENT, FAILED, REPLIED
    content = Column(String)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    lead = relationship("Lead", back_populates="messages")
    followups = relationship("FollowUp", back_populates="message")

class FollowUp(Base):
    __tablename__ = "followups"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    step = Column(Integer)
    content = Column(String)
    scheduled_time = Column(DateTime(timezone=True))
    status = Column(String) # PENDING, SENT, CANCELLED
    
    message = relationship("Message", back_populates="followups")

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, index=True)
    action = Column(String)
    lead_id = Column(String, nullable=True)
    status = Column(String)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
