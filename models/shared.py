from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum

# ─── COLLECTION WRAPPERS (used by agents that return lists) ─────────────────
class LeadsOutput(BaseModel):
    leads: List[Any] = []

class EnrichedLeadsOutput(BaseModel):
    enriched_leads: List[Any] = []

class ScoredLeadsOutput(BaseModel):
    scored_leads: List[Any] = []


class PriorityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ClassificationEnum(str, Enum):
    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"
    UNCLASSIFIED = "UNCLASSIFIED"

class StandardAgentMessage(BaseModel):
    agent: str
    task_id: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    next_agent: str
    priority: PriorityEnum = PriorityEnum.MEDIUM

class ICP(BaseModel):
    industry: str
    company_size: str
    decision_makers: List[str]
    pain_points: List[str]
    buying_triggers: List[str]

class BusinessContext(BaseModel):
    icp: ICP
    target_keywords: List[str]
    recommended_lead_sources: List[str]
    sales_strategy: str

class MarketIntelligence(BaseModel):
    competitors: List[str]
    market_trends: List[str]
    high_value_segments: List[str]
    recommended_countries: List[str]
    lead_density_score: int

class Lead(BaseModel):
    company_name: str
    website: str
    contact_person: str
    email: Optional[str] = None
    linkedin: str
    location: str
    source: str

class EnrichedLead(BaseModel):
    company: str
    size: str
    revenue_estimate: str
    tech_stack: List[str]
    hiring_status: bool
    digital_presence_score: int

class ScoredLead(BaseModel):
    company: str
    lead_score: int
    classification: ClassificationEnum
    reasoning: str

class Proposal(BaseModel):
    title: str
    executive_summary: str
    problem_statement: str
    solution: str
    features: List[str]
    timeline: str
    pricing: str
    roi_analysis: str
    call_to_action: str

class OutreachStatus(BaseModel):
    lead_id: int
    channel: str
    status: str
    message: str

class Followup(BaseModel):
    lead_id: int
    day_number: int
    content: str
    status: str

class Analytics(BaseModel):
    total_leads: int
    hot_leads: int
    proposals_sent: int
    meetings_booked: int
    conversion_rate: float

# New Agent Output Schemas

class WebsiteAudit(BaseModel):
    design_score: int
    mobile_responsive: bool
    speed_score: int
    ux_issues: List[str]
    seo_opportunities: List[str]
    conversion_bottlenecks: List[str]
    recommendation_summary: str

class AIOpportunity(BaseModel):
    support_bottleneck: bool
    sales_bottleneck: bool
    hr_bottleneck: bool
    recommended_agents: List[str]
    roi_estimation: str
    implementation_complexity: str

class PersonalizedMessage(BaseModel):
    subject_line: str
    email_body: str
    linkedin_dm: str
    key_pain_points_addressed: List[str]

class MeetingBooking(BaseModel):
    lead_id: int
    qualified: bool
    budget_estimate: str
    timeline: str
    meeting_scheduled: bool
    calendar_link_sent: bool

class CRMUpdate(BaseModel):
    lead_id: int
    pipeline_stage: str
    next_action_date: str
    probability_to_close: int
