from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db, Transaction, Complaint, Case
from backend.services.investigator import investigator
from backend.rules.investigation_rules import rule_engine
from backend.models.root_cause_model import root_cause_ml
from backend.models.complaint_classifier import complaint_classifier
from backend.models.anomaly_model import anomaly_model
from backend.services.rag import rag_service
from backend.services.llm_service import llm_service

router = APIRouter(prefix="/api/investigations", tags=["Investigations"])

class InvestigationRequest(BaseModel):
    transaction_id: str
    complaint_text: Optional[str] = None
    complaint_id: Optional[str] = None

@router.post("/run")
def run_investigation(req: InvestigationRequest, db: Session = Depends(get_db)):
    tx_id = req.transaction_id.strip()

    # Step 1: Reconstruct Timeline & Structured Facts (Phase 4)
    inv_data = investigator.investigate(tx_id, db)
    if not inv_data.get("found"):
        raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found in upay core database.")

    evidence = inv_data["evidence"]
    timeline = inv_data["timeline"]
    tx_obj = inv_data["transaction"]

    # Step 2: Customer Complaint Analysis (Phase 7)
    complaint_analysis = None
    text_to_analyze = req.complaint_text

    if not text_to_analyze and req.complaint_id:
        c_record = db.query(Complaint).filter(Complaint.complaint_id == req.complaint_id).first()
        if c_record:
            text_to_analyze = c_record.complaint_text

    if not text_to_analyze:
        # Default synthesized customer query if none supplied
        text_to_analyze = f"Customer disputing transaction {tx_id} of ৳{tx_obj['amount']} with status {tx_obj['status']}."

    complaint_analysis = complaint_classifier.predict(text_to_analyze)

    # Step 3: Rule-Based Evaluation Baseline (Phase 5)
    rule_res = rule_engine.evaluate(evidence)

    # Step 4: Machine Learning Prediction (Phase 6)
    ml_res = root_cause_ml.predict(evidence)

    # Step 5: Operational Anomaly Detection (Phase 9)
    anomaly_res = anomaly_model.predict(evidence)

    # Step 6: Similar Case Retrieval RAG (Phase 10)
    rag_query = f"{evidence.get('ground_truth_root_cause', '')} {evidence.get('failure_code', '')} {text_to_analyze}"
    similar_cases = rag_service.retrieve_similar_cases(rag_query, db, top_k=3)

    # Step 7: LLM Investigation Briefing (Phase 11)
    llm_report = llm_service.generate_investigation_report(
        complaint_text=text_to_analyze,
        transaction_data=tx_obj,
        timeline=timeline,
        ml_prediction=ml_res,
        rule_evaluation=rule_res,
        anomaly_data=anomaly_res,
        similar_cases=similar_cases
    )

    # Step 8: Multi-Model Alignment & Explainability (Phase 14)
    model_agreement = (rule_res["predicted_root_cause"] == ml_res["predicted_root_cause"])

    # Calculate explainability metrics
    explainability = {
        "agreement": model_agreement,
        "agreement_label": "FULL CONSENSUS" if model_agreement else "DISCREPANCY (REVIEW REQUIRED)",
        "rule_engine_verdict": rule_res["predicted_root_cause"],
        "ml_model_verdict": ml_res["predicted_root_cause"],
        "confidence_score": ml_res["confidence"],
        "driving_features": ml_res.get("driving_features", []),
        "timeline_key_evidence": [
            {"label": "Wallet Debited", "value": evidence.get("wallet_debited"), "status": "CONFIRMED" if evidence.get("wallet_debited") else "NO_DEBIT"},
            {"label": "Merchant Capture", "value": evidence.get("merchant_received"), "status": "ACKNOWLEDGED" if evidence.get("merchant_received") else "TIMEOUT/NOT_RECEIVED"},
            {"label": "Auto-Reversal", "value": evidence.get("reversal_found"), "status": "FOUND" if evidence.get("reversal_found") else "MISSING"},
            {"label": "Failure Code", "value": evidence.get("failure_code"), "status": "LOGGED" if evidence.get("failure_code") != "NONE" else "CLEAN"}
        ]
    }

    return {
        "status": "success",
        "investigation_id": f"INV-{tx_id}",
        "transaction": tx_obj,
        "evidence": evidence,
        "timeline": timeline,
        "complaint_analysis": {
            "text": text_to_analyze,
            "category": complaint_analysis.get("predicted_category"),
            "confidence": complaint_analysis.get("confidence"),
            "top_keywords": complaint_analysis.get("top_keywords", [])
        },
        "rule_engine": rule_res,
        "ml_prediction": ml_res,
        "anomaly_detection": anomaly_res,
        "similar_cases": similar_cases,
        "llm_report": llm_report,
        "explainability": explainability
    }
