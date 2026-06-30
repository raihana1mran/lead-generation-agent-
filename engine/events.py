from database.database import SessionLocal
from database.models import BusinessProfile, Lead, LeadIntelligence, Proposal
from agents.all_agents import (
    BusinessUnderstandingAgent, LeadEnrichmentAgent, 
    LeadScoringAgent, ProposalGenerationAgent, OutreachAutomationAgent,
    WebsiteAuditAgent, AIOpportunityDetectorAgent, PersonalizationAgent,
    FollowupOptimizationAgent, MeetingBookingAgent, CRMAgent
)
from database.audit import log_agent_action
from engine.state_machine import workflow_engine, WorkflowState

# Initialize agents
agent_bus = BusinessUnderstandingAgent()
agent_enrich = LeadEnrichmentAgent()
agent_score = LeadScoringAgent()
agent_prop = ProposalGenerationAgent()
agent_out = OutreachAutomationAgent()
agent_audit = WebsiteAuditAgent()
agent_ai_opp = AIOpportunityDetectorAgent()
agent_personalize = PersonalizationAgent()
agent_followup = FollowupOptimizationAgent()
agent_meeting = MeetingBookingAgent()
agent_crm = CRMAgent()

@log_agent_action("BusinessUnderstandingAgent", "GenerateICP")
def trigger_business_agent(profile_id: int):
    db = SessionLocal()
    try:
        profile = db.query(BusinessProfile).filter(BusinessProfile.id == profile_id).first()
        if not profile:
            return
            
        input_data = {
            "company_name": profile.company_name,
            "industry": profile.industry,
            "services": profile.services,
            "target_customers": profile.target_customers,
            "pricing": profile.pricing,
            "geography": profile.geography
        }
        
        result = agent_bus.run(input_data)
        profile.icp = result.icp.model_dump()
        db.commit()
    finally:
        db.close()

@log_agent_action("LeadEnrichmentAgent", "EnrichLead")
def trigger_lead_enrichment(lead_id: int):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead or lead.workflow_state != WorkflowState.INGESTED.value:
            return

        # STATE 2: Website Audit
        if not workflow_engine.transition_state(lead.id, WorkflowState.WEBSITE_AUDIT):
            return
        audit_result = agent_audit.run({"description": f"{lead.company_name} - {lead.website} - {lead.source}"})

        # STATE 3: AI Opportunity
        if not workflow_engine.transition_state(lead.id, WorkflowState.AI_OPPORTUNITY):
            return
        ai_opp_result = agent_ai_opp.run({
            "company_name": lead.company_name,
            "website": lead.website or "",
            "source": lead.source or "",
            "location": lead.location or "",
            "industry": lead.source or "Business",
            "size": "Unknown"
        })

        # STATE 4: Enrichment
        if not workflow_engine.transition_state(lead.id, WorkflowState.ENRICHMENT):
            return

        input_data = {"leads": [{
            "company_name": lead.company_name,
            "website": lead.website,
            "contact_person": lead.contact_person,
            "email": lead.email,
            "linkedin": lead.linkedin,
            "location": lead.location,
            "source": lead.source
        }]}
        
        result = agent_enrich.run(input_data)
        
        if result.enriched_leads:
            enriched = result.enriched_leads[0]
            
            intel = LeadIntelligence(
                lead_id=lead.id,
                size=enriched.size,
                revenue_estimate=enriched.revenue_estimate,
                tech_stack=enriched.tech_stack,
                hiring_status=enriched.hiring_status,
                digital_presence_score=enriched.digital_presence_score,
                website_audit=audit_result.model_dump(),
                ai_opportunities=ai_opp_result.model_dump()
            )
            db.add(intel)
            db.commit()

            # STATE 5: Scoring
            trigger_lead_scoring(lead.id)
            
    finally:
        db.close()

@log_agent_action("LeadScoringAgent", "CalculateScore")
def trigger_lead_scoring(lead_id: int):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead or not lead.intelligence:
            return

        # STATE 5: Scoring
        if not workflow_engine.transition_state(lead.id, WorkflowState.SCORING):
            return

        intel = lead.intelligence
        input_data = {"enriched_leads": [{
            "company": lead.company_name,
            "size": intel.size,
            "revenue_estimate": intel.revenue_estimate,
            "tech_stack": intel.tech_stack,
            "hiring_status": intel.hiring_status,
            "digital_presence_score": intel.digital_presence_score
        }]}
        
        result = agent_score.run(input_data)
        if result.scored_leads:
            scored = result.scored_leads[0]
            intel.lead_score = scored.lead_score
            intel.classification = scored.classification.value
            db.commit()
            
            # Chain to decision state
            trigger_lead_decision(lead.id)
                
    finally:
        db.close()

@log_agent_action("SystemEngine", "DecisionEngine")
def trigger_lead_decision(lead_id: int):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead or not lead.intelligence:
            return

        # STATE 6: Decision
        if not workflow_engine.transition_state(lead.id, WorkflowState.DECISION):
            return

        score = lead.intelligence.lead_score or 0
        if score >= 70:
            trigger_proposal_generation(lead.id)
        elif score >= 40:
            workflow_engine.transition_state(lead.id, WorkflowState.NURTURE)
        else:
            workflow_engine.transition_state(lead.id, WorkflowState.CLOSED_LOOP)
            
    finally:
        db.close()


@log_agent_action("ProposalGenerationAgent", "GenerateProposal")
def trigger_proposal_generation(lead_id: int, check_hitl: bool = True):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        profile = db.query(BusinessProfile).first()
        if not lead or not profile:
            return

        # STATE 7: Proposal
        if not workflow_engine.transition_state(lead.id, WorkflowState.PROPOSAL, check_hitl=check_hitl):
            return

        input_data = {
            "lead_profile": {
                "company": lead.company_name,
                "score": lead.intelligence.lead_score if lead.intelligence else 0,
                "website_audit": lead.intelligence.website_audit if lead.intelligence else {},
                "ai_opportunities": lead.intelligence.ai_opportunities if lead.intelligence else {}
            },
            "business_context": profile.icp
        }
        
        result = agent_prop.run(input_data)
        
        proposal = Proposal(
            lead_id=lead.id,
            title=result.title,
            content=result.model_dump()
        )
        db.add(proposal)
        db.commit()

        # STATE 8: Personalization
        if not workflow_engine.transition_state(lead.id, WorkflowState.PERSONALIZATION):
            return
        
        portfolio_url = profile.website if (profile and profile.website) else "https://raihana.dev"
        personalization_data = {
            "company_name": lead.company_name,
            "website_audit": lead.intelligence.website_audit if lead.intelligence else {},
            "ai_opportunities": lead.intelligence.ai_opportunities if lead.intelligence else {},
            "freelancer_name": "Raihana",
            "portfolio_url": portfolio_url
        }
        personalized_message = agent_personalize.run(personalization_data)
        if lead.intelligence:
            lead.intelligence.personalized_message = personalized_message.model_dump()
            db.commit()

        # STATE 9: Outreach
        trigger_outreach(lead.id)
        
    finally:
        db.close()

def send_email_via_smtp(to_email: str, subject: str, body: str) -> bool:
    import smtplib
    import os
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_user or not email_password:
        print("[SMTP] Warning: EMAIL_USER and EMAIL_PASSWORD are not configured in environment. Skipping real email send.")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach body
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Connect to Google SMTP (port 465 SSL)
        print(f"[SMTP] Connecting to smtp.gmail.com:465 for sending to {to_email}...")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(email_user, email_password)
        
        # Send
        server.sendmail(email_user, to_email, msg.as_string())
        server.close()
        print(f"[SMTP] Email sent successfully to {to_email}!")
        return True
    except Exception as e:
        print(f"[SMTP] Error sending email via Google SMTP: {e}")
        return False

@log_agent_action("OutreachAutomationAgent", "SendOutreach")
def trigger_outreach(lead_id: int, check_hitl: bool = True):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        # STATE 9: Outreach
        if not lead or not workflow_engine.transition_state(lead.id, WorkflowState.OUTREACH, check_hitl=check_hitl):
            return
        outreach = agent_out.run({"lead": lead.company_name, "message": str(lead.intelligence.personalized_message) if lead.intelligence else ""})
        if lead.intelligence:
            lead.intelligence.outreach_status = outreach.model_dump()
            db.commit()

        # Send actual email using Google SMTP if lead has email
        if lead and lead.email and lead.intelligence and lead.intelligence.personalized_message:
            msg_data = lead.intelligence.personalized_message
            subject = msg_data.get("subject_line", f"Partnership opportunity - {lead.company_name}")
            body = msg_data.get("email_body", "")
            if body:
                sent = send_email_via_smtp(lead.email, subject, body)
                if sent and lead.intelligence:
                    # Update outreach status in DB to reflect successful delivery
                    status = lead.intelligence.outreach_status or {}
                    status["delivery_status"] = "DELIVERED"
                    status["sent_via"] = "GOOGLE_SMTP"
                    lead.intelligence.outreach_status = status
                    db.commit()

        # STATE 10: Follow-Up
        trigger_followup(lead.id)
    finally:
        db.close()

@log_agent_action("FollowupOptimizationAgent", "ScheduleFollowups")
def trigger_followup(lead_id: int):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        # STATE 10: Follow-Up
        if not lead or not workflow_engine.transition_state(lead.id, WorkflowState.FOLLOW_UP):
            return
        followup = agent_followup.run({"lead": lead.company_name})
        if lead.intelligence:
            lead.intelligence.followups = followup.model_dump()
            db.commit()
        # STATE 11: Response (simulated positive)
        if not workflow_engine.transition_state(lead.id, WorkflowState.RESPONSE):
            return
        # STATE 12: Meeting Booked
        trigger_crm_update(lead.id)
    finally:
        db.close()

@log_agent_action("CRMAgent", "UpdateCRM")
def trigger_crm_update(lead_id: int):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        # STATE 12 → 13: Meeting Booked → CRM Update
        if not lead:
            return
        workflow_engine.transition_state(lead.id, WorkflowState.MEETING_BOOKED)
        if not workflow_engine.transition_state(lead.id, WorkflowState.CRM_UPDATE):
            return
        crm = agent_crm.run({"lead": lead.company_name})
        if lead.intelligence:
            lead.intelligence.crm_update = crm.model_dump()
            db.commit()
        # STATE 14: Analytics
        if not workflow_engine.transition_state(lead.id, WorkflowState.ANALYTICS):
            return
        # STATE 15: Closed Loop ✓
        workflow_engine.transition_state(lead.id, WorkflowState.CLOSED_LOOP)
    finally:
        db.close()

