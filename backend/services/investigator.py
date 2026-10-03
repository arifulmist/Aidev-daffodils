from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database import Transaction, TransactionEvent

class TransactionInvestigator:
    """
    Core Deterministic Transaction Investigation Engine (Phase 4).
    Reconstructs chronological event timeline and extracts structured factual evidence
    from core transaction ledger and event stream without LLM hallucinations.
    """

    def investigate(self, transaction_id: str, db: Session) -> Dict[str, Any]:
        tx: Optional[Transaction] = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()

        if not tx:
            return {
                "found": False,
                "error": f"Transaction {transaction_id} not found in database."
            }

        # Fetch all chronological events
        events: List[TransactionEvent] = db.query(TransactionEvent).filter(
            TransactionEvent.transaction_id == transaction_id
        ).order_by(TransactionEvent.timestamp.asc()).all()

        # Reconstruct timeline
        timeline = []
        wallet_debited = False
        merchant_received = False
        merchant_ack = False
        reversal_found = False
        duplicate_detected = False
        network_timeout_event = False
        security_alert_event = False
        balance_check_failed = False
        
        for ev in events:
            ev_type = ev.event_type
            ev_status = ev.event_status
            ev_meta = ev.event_metadata

            # Event timeline item
            timeline.append({
                "event_id": ev.event_id,
                "timestamp": ev.timestamp.strftime("%H:%M:%S") if ev.timestamp else "",
                "timestamp_iso": ev.timestamp.isoformat() if ev.timestamp else "",
                "event_type": ev_type,
                "event_status": ev_status,
                "metadata": ev_meta,
                "human_description": self._format_event_description(ev_type, ev_status, ev_meta)
            })

            # Structured evidence derivation
            if ev_type == "WALLET_DEBITED" and ev_status == "SUCCESS":
                wallet_debited = True
            elif ev_type in ["MERCHANT_ACK_RECEIVED", "MERCHANT_CREDITED"] and ev_status == "SUCCESS":
                merchant_received = True
                merchant_ack = True
            elif ev_type == "MERCHANT_ACK_TIMEOUT":
                merchant_ack = False
                merchant_received = False
            elif ev_type in ["REVERSAL_COMPLETED", "REVERSAL_SUCCESS"]:
                reversal_found = True
            elif ev_type in ["DUPLICATE_REQUEST_DETECTED", "DUPLICATE_PAYMENT"]:
                duplicate_detected = True
            elif ev_type in ["GATEWAY_DISPATCH", "NETWORK_TIMEOUT"] and ev_status == "FAILED":
                network_timeout_event = True
            elif ev_type in ["SECURITY_ALERT", "RISK_ALERT"]:
                security_alert_event = True
            elif ev_type == "BALANCE_CHECK" and ev_status == "FAILED":
                balance_check_failed = True

        # Calculate transaction duration
        duration_sec = 0.0
        if events and len(events) >= 2:
            duration_sec = (events[-1].timestamp - events[0].timestamp).total_seconds()
        elif tx.completed_at and tx.created_at:
            duration_sec = (tx.completed_at - tx.created_at).total_seconds()

        # Compile structured factual evidence
        evidence = {
            "transaction_id": tx.transaction_id,
            "customer_id": tx.customer_id,
            "merchant_id": tx.merchant_id,
            "amount": float(tx.amount),
            "transaction_type": tx.transaction_type,
            "transaction_status": tx.transaction_status,
            "failure_code": tx.failure_code,
            "wallet_debited": wallet_debited,
            "merchant_received": merchant_received,
            "merchant_ack": merchant_ack,
            "reversal_found": reversal_found,
            "duplicate_detected": duplicate_detected,
            "network_timeout_event": network_timeout_event,
            "security_alert_event": security_alert_event,
            "balance_check_failed": balance_check_failed,
            "number_of_events": len(events),
            "duration_sec": max(0.0, duration_sec),
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "completed_at": tx.completed_at.isoformat() if tx.completed_at else None,
            "ground_truth_root_cause": tx.ground_truth_root_cause
        }

        return {
            "found": True,
            "transaction": {
                "transaction_id": tx.transaction_id,
                "customer_id": tx.customer_id,
                "merchant_id": tx.merchant_id,
                "amount": tx.amount,
                "transaction_type": tx.transaction_type,
                "status": tx.transaction_status,
                "failure_code": tx.failure_code,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            },
            "timeline": timeline,
            "evidence": evidence
        }

    def _format_event_description(self, event_type: str, status: str, meta: Dict) -> str:
        descriptions = {
            "PAYMENT_INITIATED": "Payment session initiated by customer via App QR / Gateway",
            "WALLET_DEBITED": "Funds debited from customer wallet ledger",
            "MERCHANT_NOTIFIED": "Transaction dispatch message forwarded to merchant gateway",
            "MERCHANT_ACK_RECEIVED": "Merchant gateway acknowledged and confirmed order capture",
            "MERCHANT_ACK_TIMEOUT": "Merchant gateway failed to respond within timeout window (15s)",
            "BALANCE_CHECK": "Core ledger pre-flight balance and credit limit validation",
            "SECURITY_ALERT": "Risk engine velocity alert triggered for abnormal transaction frequency",
            "DUPLICATE_REQUEST_DETECTED": "Idempotency layer detected duplicate request token within seconds",
            "GATEWAY_DISPATCH": "Core routing network dispatch to acquiring switch",
            "STATUS_SYNC_LAG": "State synchronization delay between core ledger and app cache",
            "TRANSACTION_COMPLETED": "Transaction successfully closed and settled",
            "TRANSACTION_FAILED": f"Transaction marked failed (Code: {meta.get('failure_code') or meta.get('error', 'ERR')})",
            "REVERSAL_FAILED": "Automatic reversal queue worker failed to refund customer debit",
            "REVERSAL_COMPLETED": "Disputed amount successfully refunded to customer wallet"
        }
        return descriptions.get(event_type, f"{event_type.replace('_', ' ').capitalize()} [{status}]")

investigator = TransactionInvestigator()
