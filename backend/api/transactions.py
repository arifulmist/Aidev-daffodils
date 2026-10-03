from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db, Transaction, TransactionEvent
from backend.services.transaction_matcher import transaction_matcher
from backend.services.investigator import investigator

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

class MatchRequest(BaseModel):
    customer_id: Optional[str] = None
    amount: Optional[float] = None
    merchant_id: Optional[str] = None
    complaint_text: Optional[str] = None

@router.get("")
def list_transactions(
    status: Optional[str] = None,
    failure_code: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)
    if status:
        query = query.filter(Transaction.transaction_status == status)
    if failure_code:
        query = query.filter(Transaction.failure_code == failure_code)
    
    txs = query.order_by(Transaction.created_at.desc()).limit(limit).all()

    return [
        {
            "transaction_id": t.transaction_id,
            "customer_id": t.customer_id,
            "merchant_id": t.merchant_id,
            "amount": float(t.amount),
            "transaction_type": t.transaction_type,
            "transaction_status": t.transaction_status,
            "failure_code": t.failure_code,
            "ground_truth_root_cause": t.ground_truth_root_cause,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in txs
    ]

@router.get("/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    res = investigator.investigate(transaction_id, db)
    if not res.get("found"):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return res

@router.post("/match")
def match_candidates(req: MatchRequest, db: Session = Depends(get_db)):
    candidates = transaction_matcher.find_candidates(
        db=db,
        customer_id=req.customer_id,
        amount=req.amount,
        merchant_id=req.merchant_id,
        complaint_text=req.complaint_text,
        limit=5
    )
    return {
        "query": req.dict(),
        "candidate_count": len(candidates),
        "candidates": candidates
    }
