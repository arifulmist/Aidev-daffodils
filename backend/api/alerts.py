from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

ACTIVE_ALERTS = [
    {
        "id": "ALT-101",
        "title": "Severe Velocity Risk Anomaly",
        "severity": "CRITICAL",
        "badge_color": "rose",
        "transaction_id": "TX10084",
        "location": "Dispute Investigator",
        "description": "Customer C9999 cash-out of ৳75,000 breached core velocity threshold. Isolation Forest flagged outlier (0.62).",
        "target_tab": "investigation",
        "time": "4 mins ago",
        "complaint_text": "My ৳75,000 cash out failed and account seems restricted with security alert! Unblock immediately."
    },
    {
        "id": "ALT-102",
        "title": "Missing Auto-Reversal Dropped",
        "severity": "HIGH",
        "badge_color": "amber",
        "transaction_id": "TX10082",
        "location": "Dispute Investigator",
        "description": "Customer debited ৳2,500, merchant capture failed (DOWNSTREAM_UNAVAILABLE), auto-reversal job dropped.",
        "target_tab": "investigation",
        "time": "12 mins ago",
        "complaint_text": "I paid ৳2,500 to the shop around 2:30 PM but they didn't receive it. Money was deducted and no reversal was received."
    },
    {
        "id": "ALT-103",
        "title": "Merchant ACK Timeout Spike",
        "severity": "MEDIUM",
        "badge_color": "orange",
        "transaction_id": "TX10085",
        "location": "Dispute Investigator",
        "description": "Merchant POS aggregator failed to acknowledge ৳500 within 15s timeout SLA.",
        "target_tab": "investigation",
        "time": "25 mins ago",
        "complaint_text": "Paid 500 taka at merchant POS, money deducted from wallet, merchant terminal timed out."
    },
    {
        "id": "ALT-104",
        "title": "Sub-Second Duplicate Payment Breach",
        "severity": "HIGH",
        "badge_color": "purple",
        "transaction_id": "TX10086",
        "location": "Dispute Investigator",
        "description": "Idempotency collision detected: ৳1,000 deducted twice within 3 seconds for single purchase.",
        "target_tab": "investigation",
        "time": "38 mins ago",
        "complaint_text": "I clicked pay once for ৳1,000 but received two debit alerts! Charged twice."
    },
    {
        "id": "ALT-105",
        "title": "Dispute SLA Queue Approaching Threshold",
        "severity": "INFO",
        "badge_color": "blue",
        "transaction_id": None,
        "location": "Operations Dashboard",
        "description": "18 High-Priority disputes currently in queue. SLA target is < 15 minutes.",
        "target_tab": "dashboard",
        "time": "Just now",
        "complaint_text": None
    }
]

@router.get("")
def get_alerts():
    return {
        "count": len(ACTIVE_ALERTS),
        "alerts": ACTIVE_ALERTS
    }
