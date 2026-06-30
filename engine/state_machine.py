from enum import Enum
from database.database import SessionLocal
from database.models import Lead
from typing import Dict, List

class WorkflowState(str, Enum):
    # ── Discovery ──────────────────────────────────────────────────
    INGESTED        = "INGESTED"         # State 1:  Lead discovered and saved
    WEBSITE_AUDIT   = "WEBSITE_AUDIT"    # State 2:  Website Audit Agent running
    AI_OPPORTUNITY  = "AI_OPPORTUNITY"   # State 3:  AI Opportunity Detector running
    ENRICHMENT      = "ENRICHMENT"       # State 4:  Lead Enrichment Agent running
    SCORING         = "SCORING"          # State 5:  Lead Scoring Agent running
    # ── Routing ────────────────────────────────────────────────────
    DECISION        = "DECISION"         # State 6:  Master Orchestrator routing
    NURTURE         = "NURTURE"          # State 6b: Warm leads → nurture sequence
    # ── Conversion ─────────────────────────────────────────────────
    PROPOSAL        = "PROPOSAL"         # State 7:  Proposal Generation Agent
    PERSONALIZATION = "PERSONALIZATION"  # State 8:  Hyper-Personalization Agent
    OUTREACH        = "OUTREACH"         # State 9:  Outreach Automation Agent
    FOLLOW_UP       = "FOLLOW_UP"        # State 10: Follow-Up Agent (Day 3,7,14,21)
    RESPONSE        = "RESPONSE"         # State 11: Response detected / interested
    MEETING_BOOKED  = "MEETING_BOOKED"   # State 12: Meeting Booking Agent
    # ── CRM & Close ───────────────────────────────────────────────
    CRM_UPDATE      = "CRM_UPDATE"       # State 13: CRM Agent — pipeline update
    ANALYTICS       = "ANALYTICS"        # State 14: Analytics Agent — report
    CLOSED_LOOP     = "CLOSED_LOOP"      # State 15: Fully processed ✓

class WorkflowEngine:
    """
    Central Automation Brain — 15-State Machine

    Rules enforced:
        Rule 1 — No state skipping:  transitions are strictly ordered.
        Rule 2 — State immutability: completed states cannot be reversed.
        Rule 3 — HITL gate:          human-in-loop check before critical states.
    """

    def __init__(self):
        self.transitions: Dict[WorkflowState, List[WorkflowState]] = {
            # Discovery chain
            WorkflowState.INGESTED:        [WorkflowState.WEBSITE_AUDIT],
            WorkflowState.WEBSITE_AUDIT:   [WorkflowState.AI_OPPORTUNITY],
            WorkflowState.AI_OPPORTUNITY:  [WorkflowState.ENRICHMENT],
            WorkflowState.ENRICHMENT:      [WorkflowState.SCORING],
            WorkflowState.SCORING:         [WorkflowState.DECISION],

            # Decision routing
            WorkflowState.DECISION:        [WorkflowState.PROPOSAL, WorkflowState.NURTURE, WorkflowState.CLOSED_LOOP],
            WorkflowState.NURTURE:         [WorkflowState.OUTREACH, WorkflowState.CLOSED_LOOP],

            # Conversion chain
            WorkflowState.PROPOSAL:        [WorkflowState.PERSONALIZATION],
            WorkflowState.PERSONALIZATION: [WorkflowState.OUTREACH],
            WorkflowState.OUTREACH:        [WorkflowState.FOLLOW_UP, WorkflowState.RESPONSE],
            WorkflowState.FOLLOW_UP:       [WorkflowState.RESPONSE, WorkflowState.CLOSED_LOOP],
            WorkflowState.RESPONSE:        [WorkflowState.MEETING_BOOKED, WorkflowState.CRM_UPDATE],
            WorkflowState.MEETING_BOOKED:  [WorkflowState.CRM_UPDATE],

            # CRM & close
            WorkflowState.CRM_UPDATE:      [WorkflowState.ANALYTICS],
            WorkflowState.ANALYTICS:       [WorkflowState.CLOSED_LOOP],
            WorkflowState.CLOSED_LOOP:     [],
        }

        # Human-in-the-loop gates — pause here if lead.requires_hitl = True
        self.hitl_gates = {
            WorkflowState.PROPOSAL,
            WorkflowState.OUTREACH,
            WorkflowState.MEETING_BOOKED,
        }

    def transition_state(self, lead_id: int, next_state: WorkflowState, check_hitl: bool = True) -> bool:
        db = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")

            current_state = WorkflowState(lead.workflow_state)

            # Rule 1 & 2: Enforce valid, forward-only transitions
            allowed = self.transitions.get(current_state, [])
            if next_state not in allowed:
                print(f"[StateMachine] ⛔ Invalid transition {current_state} → {next_state} for lead {lead_id}")
                return False

            # Rule 3: HITL gate check
            if check_hitl and lead.requires_hitl and next_state in self.hitl_gates:
                print(f"[StateMachine] HITL PAUSE -- Lead {lead_id} needs approval before {next_state}")
                return False

            lead.workflow_state = next_state.value
            db.commit()
            print(f"[StateMachine] Lead {lead_id}: {current_state} -> {next_state}")
            return True

        except Exception as e:
            print(f"[StateMachine] Error transitioning lead {lead_id}: {e}")
            return False
        finally:
            db.close()

    def get_state_index(self, state: WorkflowState) -> int:
        ordered = [
            WorkflowState.INGESTED, WorkflowState.WEBSITE_AUDIT, WorkflowState.AI_OPPORTUNITY,
            WorkflowState.ENRICHMENT, WorkflowState.SCORING, WorkflowState.DECISION,
            WorkflowState.PROPOSAL, WorkflowState.PERSONALIZATION, WorkflowState.OUTREACH,
            WorkflowState.FOLLOW_UP, WorkflowState.RESPONSE, WorkflowState.MEETING_BOOKED,
            WorkflowState.CRM_UPDATE, WorkflowState.ANALYTICS, WorkflowState.CLOSED_LOOP
        ]
        return ordered.index(state) if state in ordered else -1


workflow_engine = WorkflowEngine()
