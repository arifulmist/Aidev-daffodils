import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from backend.database import SessionLocal, init_db
from backend.api.investigations import run_investigation, InvestigationRequest
from backend.services.transaction_matcher import transaction_matcher
from backend.api.cases import submit_feedback, FeedbackRequest, create_case, CaseCreateRequest

def test_pipeline():
    print("[TEST] Initializing pipeline test...")
    init_db()
    db = SessionLocal()

    # Test 1: Case 1 - Missing Reversal
    print("\n--- Test 1: TX10082 (Missing Reversal) ---")
    req1 = InvestigationRequest(
        transaction_id="TX10082",
        complaint_text="I paid 2,500 to the shop around 2:30 PM but they didn't receive it. Money was deducted and no reversal was received."
    )
    res1 = run_investigation(req1, db)
    print(f"Transaction ID: {res1['transaction']['transaction_id']}")
    print(f"Rule Engine: {res1['rule_engine']['predicted_root_cause']} (Rule: {res1['rule_engine']['rule_matched']})")
    print(f"ML Model: {res1['ml_prediction']['predicted_root_cause']} (Confidence: {res1['ml_prediction']['confidence']*100:.1f}%)")
    print(f"Consensus: {res1['explainability']['agreement_label']}")
    print(f"Assigned Team: {res1['llm_report']['assigned_team']}")
    print(f"Action: {res1['llm_report']['recommended_action'][:80]}...")
    assert res1['ml_prediction']['predicted_root_cause'] == "MISSING_REVERSAL"
    assert res1['llm_report']['assigned_team'] == "Reconciliation"

    # Test 2: Case 2 - Successful Transaction
    print("\n--- Test 2: TX10083 (Successful Transaction) ---")
    req2 = InvestigationRequest(
        transaction_id="TX10083",
        complaint_text="Can you check my payment of 1,200? The merchant was unsure if it went through."
    )
    res2 = run_investigation(req2, db)
    print(f"ML Model: {res2['ml_prediction']['predicted_root_cause']} (Confidence: {res2['ml_prediction']['confidence']*100:.1f}%)")
    print(f"Anomaly: {res2['anomaly_detection']['status']} (Score: {res2['anomaly_detection']['anomaly_score']})")
    assert res2['ml_prediction']['predicted_root_cause'] == "SUCCESS"

    # Test 3: Case 3 - Anomaly
    print("\n--- Test 3: TX10084 (Suspicious Activity Anomaly) ---")
    req3 = InvestigationRequest(
        transaction_id="TX10084",
        complaint_text="My 75,000 cash out failed and account restricted!"
    )
    res3 = run_investigation(req3, db)
    print(f"ML Model: {res3['ml_prediction']['predicted_root_cause']}")
    print(f"Anomaly Status: {res3['anomaly_detection']['status']} (Score: {res3['anomaly_detection']['anomaly_score']})")
    print(f"Anomaly Reasons: {res3['anomaly_detection']['reasons']}")
    assert res3['anomaly_detection']['status'] == "ANOMALOUS"

    # Test 4: Transaction Candidate Matching
    print("\n--- Test 4: Candidate Matching without Transaction ID ---")
    matched = transaction_matcher.find_candidates(
        db=db,
        customer_id="C1024",
        amount=2500.0,
        merchant_id="M44"
    )
    print(f"Found {len(matched)} candidates.")
    for c in matched:
        print(f" -> {c['transaction_id']} (৳{c['amount']}, Score: {c['match_score']}, Reason: {c['match_reason']})")
    assert any(c['transaction_id'] == "TX10082" for c in matched)

    # Test 5: Human-in-the-Loop Feedback Loop
    print("\n--- Test 5: Human-in-the-Loop Feedback Submission ---")
    case_req = CaseCreateRequest(
        transaction_id="TX10082",
        root_cause=res1['ml_prediction']['predicted_root_cause'],
        confidence=res1['ml_prediction']['confidence'],
        priority="HIGH",
        assigned_team=res1['llm_report']['assigned_team'],
        recommendation=res1['llm_report']['recommended_action']
    )
    created = create_case(case_req, db)
    case_id = created["case_id"]

    fb_req = FeedbackRequest(
        operator_action="ACCEPTED",
        actual_root_cause="MISSING_REVERSAL",
        actual_team="Reconciliation",
        resolved_by="Senior_Officer_Tariq",
        resolution_notes="Audited core switch logs. Missing auto-reversal verified. Initiated manual refund."
    )
    fb_res = submit_feedback(case_id, fb_req, db)
    print(f"Feedback Status: {fb_res['status']}, Operator Action: {fb_res['operator_action']}")
    assert fb_res["feedback_logged"] is True

    db.close()
    print("\n[ALL TESTS PASSED] Pipeline is 100% operational!")

if __name__ == "__main__":
    test_pipeline()
