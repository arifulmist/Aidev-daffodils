from typing import Dict, Any, Tuple

class RuleBasedInvestigator:
    """
    Deterministic Rule-Based Root Cause Engine (Phase 5).
    Provides an interpretable, auditable baseline for root cause diagnosis
    and team routing based on business logic.
    """

    def evaluate(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        wallet_debited = evidence.get("wallet_debited", False)
        merchant_received = evidence.get("merchant_received", False)
        reversal_found = evidence.get("reversal_found", False)
        merchant_ack = evidence.get("merchant_ack", False)
        failure_code = evidence.get("failure_code", "NONE")
        status = evidence.get("transaction_status", "UNKNOWN")
        duplicate_detected = evidence.get("duplicate_detected", False)
        network_timeout_event = evidence.get("network_timeout_event", False)
        security_alert_event = evidence.get("security_alert_event", False)
        balance_check_failed = evidence.get("balance_check_failed", False)

        rule_matched = None
        predicted_cause = "UNKNOWN_FAILURE"
        confidence = 0.85
        assigned_team = "Customer Care Tier 2"
        recommendation = "Review system logs for unclassified exception."
        explanation = []

        # Rule 1: Normal Success
        if status == "SUCCESS" and wallet_debited and merchant_received and failure_code == "NONE" and not duplicate_detected:
            rule_matched = "RULE_01_NORMAL_SUCCESS"
            predicted_cause = "SUCCESS"
            confidence = 0.99
            assigned_team = "Customer Care Tier 2"
            recommendation = "No operational action required. Inform customer that transaction completed successfully."
            explanation = [
                "Wallet successfully debited",
                "Merchant gateway confirmed receipt",
                "No failure code or timeout logged"
            ]

        # Rule 2: Duplicate transaction
        elif duplicate_detected or failure_code == "DUP_IDEMPOTENCY_ERR":
            rule_matched = "RULE_02_DUPLICATE_PAYMENT"
            predicted_cause = "DUPLICATE_TRANSACTION"
            confidence = 0.95
            assigned_team = "Merchant Operations"
            recommendation = "Initiate chargeback/adjustment against merchant settlement for duplicate debit."
            explanation = [
                "Idempotency token matched previous debit request",
                "Rapid consecutive requests detected within seconds",
                "Merchant received duplicate credit"
            ]

        # Rule 3: Suspicious Activity
        elif security_alert_event or failure_code == "RISK_VELOCITY_BREACH":
            rule_matched = "RULE_03_VELOCITY_RISK"
            predicted_cause = "SUSPICIOUS_ACTIVITY"
            confidence = 0.92
            assigned_team = "Fraud & Security"
            recommendation = "Freeze temporary cash-out privileges and verify account owner KYC credentials."
            explanation = [
                "Risk engine velocity threshold breached",
                "High transaction amount or abnormal burst frequency",
                "Flagged by real-time security rules"
            ]

        # Rule 4: Insufficient Balance
        elif balance_check_failed or failure_code == "BAL_INSUFFICIENT":
            rule_matched = "RULE_04_INSUFFICIENT_BALANCE"
            predicted_cause = "INSUFFICIENT_BALANCE"
            confidence = 0.98
            assigned_team = "Customer Care Tier 2"
            recommendation = "Advise customer on account balance and fee schedule."
            explanation = [
                "Pre-flight ledger balance check rejected transaction",
                "No funds deducted from customer wallet"
            ]

        # Rule 5: Network Gateway Timeout (Before debit)
        elif network_timeout_event or failure_code in ["NET_GATEWAY_TIMEOUT", "NET_DROP"]:
            rule_matched = "RULE_05_NETWORK_TIMEOUT"
            predicted_cause = "NETWORK_TIMEOUT"
            confidence = 0.93
            assigned_team = "Network & Core Banking"
            recommendation = "Verify acquiring switch uptime; confirm customer balance was not impacted."
            explanation = [
                "Network gateway timed out before core debit ledger confirmation",
                "No customer wallet deduction occurred"
            ]

        # Rule 6: Status Synchronization Lag (Merchant received, but app shows pending)
        elif merchant_received and (status == "PENDING" or failure_code == "SYNC_LAG"):
            rule_matched = "RULE_06_STATUS_SYNC_LAG"
            predicted_cause = "STATUS_SYNC_DELAY"
            confidence = 0.94
            assigned_team = "Network & Core Banking"
            recommendation = "Invalidate Redis state cache and broadcast status update notification to customer app."
            explanation = [
                "Merchant received and acknowledged payment",
                "Core app wallet cache is in pending state",
                "Downstream settlement is intact"
            ]

        # Rule 7: Missing Reversal (Wallet debited, transaction failed, no reversal)
        elif wallet_debited and not merchant_received and not reversal_found and failure_code in ["REV_NOT_TRIGGERED", "DOWNSTREAM_UNAVAILABLE"]:
            rule_matched = "RULE_07_MISSING_REVERSAL"
            predicted_cause = "MISSING_REVERSAL"
            confidence = 0.96
            assigned_team = "Reconciliation"
            recommendation = "Trigger immediate automated credit reversal to restore customer balance."
            explanation = [
                "Customer wallet was debited",
                "Merchant did not receive payment",
                "Auto-reversal routine failed to execute within SLA window"
            ]

        # Rule 8: Merchant ACK Failure (Wallet debited, merchant timed out)
        elif wallet_debited and not merchant_received and failure_code == "MRC_TIMEOUT":
            rule_matched = "RULE_08_MERCHANT_ACK_TIMEOUT"
            predicted_cause = "MERCHANT_ACK_FAILURE"
            confidence = 0.95
            assigned_team = "Reconciliation"
            recommendation = "Cross-check merchant POS/API gateway logs; execute reconciliation refund."
            explanation = [
                "Customer wallet debited successfully",
                "Merchant gateway timed out after 15 seconds without ACK",
                "Funds pending in intermediate settlement holding account"
            ]

        # Fallback / Unknown
        else:
            rule_matched = "RULE_99_DEFAULT_EXCEPTION"
            predicted_cause = "UNKNOWN_FAILURE"
            confidence = 0.60
            assigned_team = "Network & Core Banking"
            recommendation = "Assign senior switch engineer to inspect raw gateway telemetry."
            explanation = [
                f"Unmatched operational condition (Status: {status}, Failure code: {failure_code})"
            ]

        return {
            "engine": "rule_based",
            "rule_matched": rule_matched,
            "predicted_root_cause": predicted_cause,
            "confidence": confidence,
            "assigned_team": assigned_team,
            "recommendation": recommendation,
            "explanation_points": explanation
        }

rule_engine = RuleBasedInvestigator()
