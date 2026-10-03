from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from backend.database import get_db, Complaint, Transaction
from backend.models.complaint_classifier import complaint_classifier
from backend.services.transaction_matcher import transaction_matcher

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

class ComplaintCreateRequest(BaseModel):
    customer_id: str
    complaint_text: str
    transaction_id: Optional[str] = None

@router.get("")
def list_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    
    complaints = query.order_by(Complaint.created_at.desc()).limit(limit).all()

    return [
        {
            "complaint_id": c.complaint_id,
            "customer_id": c.customer_id,
            "transaction_id": c.transaction_id,
            "complaint_text": c.complaint_text,
            "category": c.category,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in complaints
    ]

@router.post("")
def create_complaint(req: ComplaintCreateRequest, db: Session = Depends(get_db)):
    # 1. Predict category using NLP Classifier
    clf_result = complaint_classifier.predict(req.complaint_text)

    # 2. Check for candidate transactions if not provided
    candidates = []
    if not req.transaction_id:
        candidates = transaction_matcher.find_candidates(
            db=db,
            customer_id=req.customer_id,
            complaint_text=req.complaint_text
        )

    # 3. Save complaint
    new_id = f"CMP-{int(datetime.utcnow().timestamp())}"
    db_complaint = Complaint(
        complaint_id=new_id,
        customer_id=req.customer_id,
        transaction_id=req.transaction_id or (candidates[0]["transaction_id"] if len(candidates) == 1 else None),
        complaint_text=req.complaint_text,
        category=clf_result["predicted_category"],
        status="NEW",
        created_at=datetime.utcnow()
    )
    db.add(db_complaint)
    db.commit()

    return {
        "complaint_id": new_id,
        "customer_id": req.customer_id,
        "complaint_text": req.complaint_text,
        "predicted_category": clf_result["predicted_category"],
        "confidence": clf_result["confidence"],
        "top_keywords": clf_result["top_keywords"],
        "candidates": candidates
    }
