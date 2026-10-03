from fastapi import APIRouter

router = APIRouter(prefix="/api/demo", tags=["Demo"])

DEMO_CASES = [
    {
        "id": "case-1",
        "title": "Case 1: Missing Reversal (Disputed ৳2,500)",
        "badge": "Core Dispute",
        "badge_color": "amber",
        "transaction_id": "TX10082",
        "customer_id": "C1024",
        "amount": 2500.0,
        "complaint_text": "I paid ৳2,500 to the shop around 2:30 PM but they didn't receive it. Money was deducted from my upay wallet and no reversal was received.",
        "expected_root_cause": "MISSING_REVERSAL",
        "expected_team": "Reconciliation",
        "description": "Customer wallet was debited, payment failed at downstream switch, but automated reversal job failed to trigger."
    },
    {
        "id": "case-2",
        "title": "Case 2: Successful Transaction (False Dispute)",
        "badge": "Healthy / No Issue",
        "badge_color": "green",
        "transaction_id": "TX10083",
        "customer_id": "C2050",
        "amount": 1200.0,
        "complaint_text": "Can you check my payment of ৳1,200? The merchant was unsure if it went through properly.",
        "expected_root_cause": "SUCCESS",
        "expected_team": "Customer Care Tier 2",
        "description": "Legitimate transaction. Core ledger debit confirmed, merchant acknowledged capture, no discrepancy found."
    },
    {
        "id": "case-3",
        "title": "Case 3: Anomalous Transaction (Velocity & High Ticket)",
        "badge": "Risk / Anomaly",
        "badge_color": "red",
        "transaction_id": "TX10084",
        "customer_id": "C9999",
        "amount": 75000.0,
        "complaint_text": "My ৳75,000 cash out failed and account seems restricted with security alert! Unblock immediately.",
        "expected_root_cause": "SUSPICIOUS_ACTIVITY",
        "expected_team": "Fraud & Security",
        "description": "Severe velocity spike and high ticket value triggered risk engine threshold and isolation forest outlier detection."
    },
    {
        "id": "case-4",
        "title": "Case 4: Merchant ACK Timeout",
        "badge": "Gateway Timeout",
        "badge_color": "orange",
        "transaction_id": "TX10085",
        "customer_id": "C3030",
        "amount": 500.0,
        "complaint_text": "Paid 500 taka at merchant POS, money deducted from wallet, merchant terminal timed out.",
        "expected_root_cause": "MERCHANT_ACK_FAILURE",
        "expected_team": "Reconciliation",
        "description": "Customer debited but merchant gateway failed to return ACK within 15s timeout window."
    },
    {
        "id": "case-5",
        "title": "Case 5: Duplicate Rapid Payment",
        "badge": "Duplicate Debit",
        "badge_color": "purple",
        "transaction_id": "TX10086",
        "customer_id": "C4040",
        "amount": 1000.0,
        "complaint_text": "I clicked pay once for ৳1,000 but received two debit alerts! Charged twice.",
        "expected_root_cause": "DUPLICATE_TRANSACTION",
        "expected_team": "Merchant Operations",
        "description": "Sub-second consecutive requests caused idempotency breach and duplicate debit for single purchase."
    }
]

@router.get("/cases")
def get_demo_cases():
    return {
        "count": len(DEMO_CASES),
        "demo_cases": DEMO_CASES
    }
