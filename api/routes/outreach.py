from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Message, FollowUp
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/outreach", tags=["Outreach"])

class OutreachRequest(BaseModel):
    lead_id: int
    channel: str # email, linkedin
    template_id: int = None

class SmtpSettings(BaseModel):
    email_user: str
    email_password: str

@router.get("/smtp")
def get_smtp_settings():
    email_user = os.getenv("EMAIL_USER", "")
    email_password = os.getenv("EMAIL_PASSWORD", "")
    masked_password = "********" if email_password else ""
    return {
        "email_user": email_user,
        "email_password": masked_password
    }

@router.post("/smtp")
def save_smtp_settings(settings: SmtpSettings):
    try:
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        user_found = False
        pass_found = False
        new_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("EMAIL_USER="):
                new_lines.append(f"EMAIL_USER={settings.email_user}\n")
                user_found = True
            elif stripped.startswith("EMAIL_PASSWORD="):
                if settings.email_password != "********":
                    new_lines.append(f"EMAIL_PASSWORD={settings.email_password}\n")
                else:
                    new_lines.append(line)
                pass_found = True
            else:
                new_lines.append(line)

        if not user_found:
            new_lines.append(f"EMAIL_USER={settings.email_user}\n")
        if not pass_found and settings.email_password != "********":
            new_lines.append(f"EMAIL_PASSWORD={settings.email_password}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        from dotenv import load_dotenv
        load_dotenv(override=True)

        return {"message": "SMTP settings saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{channel}")
def trigger_outreach(channel: str, req: OutreachRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Event Trigger: Proposal Sent -> Send outreach
    
    msg = Message(lead_id=req.lead_id, channel=channel.upper(), status="PENDING", content="Mocked message content")
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    # background_tasks.add_task(trigger_outreach_agent, msg.id)
    return {"message": "Outreach queued", "message_id": msg.id}

@router.post("/followups")
def schedule_followup(message_id: int, db: Session = Depends(get_db)):
    fup = FollowUp(message_id=message_id, step=1, status="PENDING", content="Mock follow-up")
    db.add(fup)
    db.commit()
    db.refresh(fup)
    return fup
