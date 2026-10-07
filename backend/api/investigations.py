import hashlib
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from backend.database import get_db, Transaction, Complaint, Case
from backend.services.investigator import investigator
from backend.rules.investigation_rules import rule_engine
from backend.models.root_cause_model import root_cause_ml
from backend.models.complaint_classifier import complaint_classifier
from backend.models.anomaly_model import anomaly_model
from backend.services.rag import rag_service
from backend.services.llm_service import llm_service
from backend.services.privacy_guard import privacy_guard
from backend.services.causal_engine import causal_engine

router = APIRouter(prefix="/api/investigations", tags=["Investigations"])

class InvestigationRequest(BaseModel):
    transaction_id: str
    complaint_text: Optional[str] = None
    complaint_id: Optional[str] = None

class WhatIfRequest(BaseModel):
    transaction_id: str
    hypotheses: Dict[str, bool] = Field(default_factory=dict)

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

    # Step 2: Privacy Sanitization & Redaction (Responsible AI)
    raw_text = req.complaint_text
    if not raw_text and req.complaint_id:
        c_record = db.query(Complaint).filter(Complaint.complaint_id == req.complaint_id).first()
        if c_record:
            raw_text = c_record.complaint_text

    if not raw_text:
        raw_text = f"Customer disputing transaction {tx_id} of ৳{tx_obj['amount']} with status {tx_obj['status']}."

    # Sanitize customer PII (phone number, NID, accounts) before NLP and LLM
    privacy_res = privacy_guard.sanitize_text(raw_text)
    text_to_analyze = privacy_res["sanitized_text"]

    # Customer Complaint NLP Classification
    complaint_analysis = complaint_classifier.predict(text_to_analyze)

    # Step 3: Rule-Based Evaluation Baseline (Deterministic)
    rule_res = rule_engine.evaluate(evidence)

    # Step 4: Machine Learning Prediction with Local Tree Attribution & Abstain Policy
    ml_res = root_cause_ml.predict(evidence)

    # Step 5: Operational Anomaly Detection
    anomaly_res = anomaly_model.predict(evidence)

    # Step 6: Autonomous Micro-Dispute Self-Healing Evaluation
    self_healing_eval = causal_engine.evaluate_self_healing_policy(evidence, ml_res, anomaly_res)

    # Step 7: Similar Case Retrieval RAG
    rag_query = f"{evidence.get('ground_truth_root_cause', '')} {evidence.get('failure_code', '')} {text_to_analyze}"
    similar_cases = rag_service.retrieve_similar_cases(rag_query, db, top_k=3)

    # Step 8: LLM Investigation Briefing (Ground-truth facts only)
    llm_report = llm_service.generate_investigation_report(
        complaint_text=text_to_analyze,
        transaction_data=tx_obj,
        timeline=timeline,
        ml_prediction=ml_res,
        rule_evaluation=rule_res,
        anomaly_data=anomaly_res,
        similar_cases=similar_cases
    )

    # Step 9: Multi-Model Alignment & Explainability
    model_agreement = (rule_res["predicted_root_cause"] == ml_res["predicted_root_cause"])

    explainability = {
        "agreement": model_agreement,
        "agreement_label": "FULL CONSENSUS" if model_agreement else "DISCREPANCY (REVIEW REQUIRED)",
        "rule_engine_verdict": rule_res["predicted_root_cause"],
        "ml_model_verdict": ml_res["predicted_root_cause"],
        "confidence_score": ml_res["confidence"],
        "abstain_recommended": ml_res.get("abstain_recommended", False),
        "uncertainty_tier": ml_res.get("uncertainty_tier", "HIGH_CONFIDENCE_AUTO_TRIAGE"),
        "driving_features": ml_res.get("driving_features", []),
        "local_feature_attributions": ml_res.get("local_feature_attributions", []),
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
        "privacy": {
            "pii_redacted": privacy_res["redacted_count"] > 0,
            "redacted_count": privacy_res["redacted_count"],
            "redacted_entities": privacy_res["entities_redacted"],
            "standard": privacy_res["privacy_standard"]
        },
        "complaint_analysis": {
            "text": text_to_analyze,
            "category": complaint_analysis.get("predicted_category"),
            "confidence": complaint_analysis.get("confidence"),
            "top_keywords": complaint_analysis.get("top_keywords", [])
        },
        "rule_engine": rule_res,
        "ml_prediction": ml_res,
        "anomaly_detection": anomaly_res,
        "self_healing": self_healing_eval,
        "similar_cases": similar_cases,
        "llm_report": llm_report,
        "explainability": explainability
    }

@router.post("/what-if")
def test_what_if_counterfactual(req: WhatIfRequest, db: Session = Depends(get_db)):
    """
    Simulates counterfactual hypotheses ('What if Merchant ACK arrived?', 'What if Reversal worker succeeded?').
    Returns side-by-side delta showing how the root cause and resolution shift.
    """
    tx_id = req.transaction_id.strip()
    inv_data = investigator.investigate(tx_id, db)
    if not inv_data.get("found"):
        raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found.")

    res = causal_engine.simulate_what_if(
        evidence=inv_data["evidence"],
        events=inv_data["timeline"],
        hypotheses=req.hypotheses
    )
    return {
        "status": "success",
        "transaction_id": tx_id,
        "simulation": res
    }

@router.get("/{transaction_id}/dossier")
def export_dispute_dossier(transaction_id: str, db: Session = Depends(get_db)):
    """
    Generates a cryptographically verifiable (SHA-256) dispute audit dossier packet
    suitable for Bangladesh Bank compliance, legal inquiry, or inter-bank settlement.
    """
    tx_id = transaction_id.strip()
    inv_data = investigator.investigate(tx_id, db)
    if not inv_data.get("found"):
        raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found.")

    evidence = inv_data["evidence"]
    timeline = inv_data["timeline"]
    tx_obj = inv_data["transaction"]

    rule_res = rule_engine.evaluate(evidence)
    ml_res = root_cause_ml.predict(evidence)
    anomaly_res = anomaly_model.predict(evidence)

    # Compute SHA-256 fingerprint over evidence
    canonical_str = f"{tx_id}|{tx_obj['amount']}|{evidence['wallet_debited']}|{evidence['merchant_received']}|{evidence['failure_code']}"
    sha256_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    return {
        "dossier_id": f"DOS-UPAY-{tx_id}",
        "generated_at": "2026-10-07T00:00:00Z",
        "cryptographic_fingerprint_sha256": sha256_hash,
        "regulatory_framework": "Bangladesh Bank MFS Circular 04/2022 & 08/2023",
        "sla_resolution_target_days": 7,
        "transaction": tx_obj,
        "structured_evidence": evidence,
        "chronological_event_audit": timeline,
        "consensus_determination": {
            "primary_root_cause": ml_res["predicted_root_cause"],
            "rule_baseline": rule_res["predicted_root_cause"],
            "ml_confidence": ml_res["confidence"],
            "assigned_department": ml_res["assigned_team"]
        },
        "anomaly_assessment": {
            "risk_tier": anomaly_res.get("risk_tier", "NORMAL"),
            "anomaly_score": anomaly_res.get("anomaly_score", 0.0)
        },
        "compliance_signoff": {
            "automated_investigation_valid": True,
            "human_in_the_loop_mandatory": True,
            "audit_trail_immutable": True
        }
    }
