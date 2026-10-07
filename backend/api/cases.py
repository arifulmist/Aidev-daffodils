from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from backend.database import get_db, Case, Complaint, ResolutionHistory, Transaction
from backend.models.root_cause_model import root_cause_ml

router = APIRouter(prefix="/api/cases", tags=["Cases"])

class CaseCreateRequest(BaseModel):
    complaint_id: Optional[str] = None
    transaction_id: str
    root_cause: str
    confidence: float
    priority: str = "MEDIUM"
    assigned_team: str
    recommendation: str

class FeedbackRequest(BaseModel):
    operator_action: str  # "ACCEPTED", "CORRECTED", "OVERRIDDEN"
    actual_root_cause: str
    actual_team: str
    resolved_by: str = "Ops_Officer_Rahman"
    resolution_notes: Optional[str] = None

@router.get("")
def list_cases(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    cases = query.order_by(Case.created_at.desc()).all()

    return [
        {
            "case_id": c.case_id,
            "complaint_id": c.complaint_id,
            "transaction_id": c.transaction_id,
            "root_cause": c.root_cause,
            "confidence": c.confidence,
            "priority": c.priority,
            "assigned_team": c.assigned_team,
            "recommendation": c.recommendation,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in cases
    ]

@router.post("")
def create_case(req: CaseCreateRequest, db: Session = Depends(get_db)):
    case_id = f"CASE-{datetime.utcnow().strftime('%m%d%H%M%S')}"
    
    db_case = Case(
        case_id=case_id,
        complaint_id=req.complaint_id,
        transaction_id=req.transaction_id,
        root_cause=req.root_cause,
        confidence=req.confidence,
        priority=req.priority,
        assigned_team=req.assigned_team,
        recommendation=req.recommendation,
        status="OPEN",
        created_at=datetime.utcnow()
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    # Sync to Supabase PostgreSQL in Cloud
    supabase_synced = False
    try:
        from backend.services.supabase_service import supabase_service
        sync_res = supabase_service.sync_case({
            "case_id": db_case.case_id,
            "complaint_id": db_case.complaint_id,
            "transaction_id": db_case.transaction_id,
            "root_cause": db_case.root_cause,
            "confidence": db_case.confidence,
            "priority": db_case.priority,
            "assigned_team": db_case.assigned_team,
            "recommendation": db_case.recommendation,
            "status": db_case.status
        })
        supabase_synced = sync_res.get("synced", False)
    except Exception as e:
        print(f"[Supabase Sync] Warning: {e}")

    return {
        "status": "success",
        "case_id": db_case.case_id,
        "assigned_team": db_case.assigned_team,
        "supabase_synced": supabase_synced,
        "message": f"Case {case_id} logged and routed to {db_case.assigned_team}."
    }

@router.post("/{case_id}/feedback")
def submit_feedback(case_id: str, req: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Phase 15 Human-in-the-Loop Feedback:
    Captures officer judgment, updates case, and logs to resolution_history table.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    pred_rc = case.root_cause
    pred_team = case.assigned_team

    # Update case status
    case.status = "RESOLVED"
    case.root_cause = req.actual_root_cause
    case.assigned_team = req.actual_team
    case.updated_at = datetime.utcnow()

    # Log to resolution history
    history = ResolutionHistory(
        case_id=case_id,
        predicted_root_cause=pred_rc,
        actual_root_cause=req.actual_root_cause,
        predicted_team=pred_team,
        actual_team=req.actual_team,
        operator_action=req.operator_action,
        resolved_by=req.resolved_by,
        resolution_notes=req.resolution_notes,
        is_feedback_approved=True,
        timestamp=datetime.utcnow()
    )
    db.add(history)
    db.commit()

    return {
        "status": "success",
        "case_id": case_id,
        "operator_action": req.operator_action,
        "feedback_logged": True,
        "message": "Operator feedback captured! Dataset updated for continuous model training loop."
    }

@router.get("/feedback/history")
def get_feedback_history(db: Session = Depends(get_db)):
    history = db.query(ResolutionHistory).order_by(ResolutionHistory.timestamp.desc()).limit(20).all()
    return [
        {
            "id": h.id,
            "case_id": h.case_id,
            "predicted_root_cause": h.predicted_root_cause,
            "actual_root_cause": h.actual_root_cause,
            "operator_action": h.operator_action,
            "resolved_by": h.resolved_by,
            "resolution_notes": h.resolution_notes,
            "timestamp": h.timestamp.isoformat() if h.timestamp else None
        }
        for h in history
    ]
