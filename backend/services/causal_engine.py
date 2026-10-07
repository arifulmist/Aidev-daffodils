import copy
from typing import Dict, Any, List
from backend.rules.investigation_rules import rule_engine
from backend.models.root_cause_model import root_cause_ml
from backend.models.anomaly_model import anomaly_model

class CausalCounterfactualEngine:
    """
    Causal Counterfactual What-If Engine & Autonomous Self-Healing Resolver.
    Enables operators to test counterfactual hypotheses ('What if Merchant ACK had arrived?')
    and evaluates automated self-healing eligibility for micro-disputes.
    """

    @classmethod
    def simulate_what_if(
        cls,
        evidence: Dict[str, Any],
        events: List[Dict[str, Any]],
        hypotheses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs counterfactual causal graph simulation.
        Mutates evidence parameters according to hypothetical conditions,
        re-evaluates deterministic rules and Random Forest ML, and computes causal delta.
        """
        # Create mutated deep-copy
        mutated_evidence = copy.deepcopy(evidence)
        mutated_events = copy.deepcopy(events)
        applied_hypotheses = []

        # 1. Hypothesis: What if Merchant ACK had succeeded?
        if hypotheses.get("merchant_ack_received", False):
            mutated_evidence["merchant_received"] = True
            mutated_evidence["merchant_ack"] = True
            mutated_evidence["failure_code"] = "NONE"
            mutated_events.append({
                "event_id": 9991,
                "timestamp": "14:32:15",
                "event_type": "MERCHANT_ACK_RECEIVED",
                "event_status": "SUCCESS",
                "human_description": "[Counterfactual] Merchant gateway sent HTTP 200 ACK within timeout window"
            })
            applied_hypotheses.append("Merchant ACK arrived at T+4s (HTTP 200)")

        # 2. Hypothesis: What if automated reversal worker executed?
        if hypotheses.get("reversal_succeeded", False):
            mutated_evidence["reversal_found"] = True
            mutated_events.append({
                "event_id": 9992,
                "timestamp": "14:32:20",
                "event_type": "REVERSAL_COMPLETED",
                "event_status": "SUCCESS",
                "human_description": "[Counterfactual] Core banking rollback worker credited wallet immediately"
            })
            applied_hypotheses.append("Automated reversal rollback worker executed at T+9s")

        # 3. Hypothesis: What if balance check passed?
        if hypotheses.get("balance_sufficient", False):
            mutated_evidence["balance_check_failed"] = False
            mutated_evidence["failure_code"] = "NONE"
            applied_hypotheses.append("Customer balance validation passed (sufficient funds)")

        # 4. Hypothesis: What if network timeout didn't occur?
        if hypotheses.get("network_timeout_cleared", False):
            mutated_evidence["network_timeout_event"] = False
            if mutated_evidence.get("failure_code") == "NET_TIMEOUT":
                mutated_evidence["failure_code"] = "NONE"
            applied_hypotheses.append("Telecom/NPSB gateway latency remained under 1,500ms")

        # Re-run rule engine on mutated evidence
        mutated_rule_eval = rule_engine.evaluate(mutated_evidence)

        # Re-run ML model on mutated evidence
        mutated_ml_pred = root_cause_ml.predict(mutated_evidence)

        # Re-run anomaly model
        mutated_anomaly = anomaly_model.predict(mutated_evidence)

        # Original baseline results
        original_cause = evidence.get("failure_code", "UNKNOWN")
        new_cause = mutated_ml_pred.get("predicted_root_cause", "UNKNOWN")

        # Determine causal impact
        if new_cause in ["SUCCESS", "No issue"]:
            causal_outcome = "TRANSACTION_WOULD_SUCCEED"
            explanation = "Under these counterfactual conditions, the transaction completes with 0 customer dispute."
        elif new_cause != original_cause:
            causal_outcome = f"ROOT_CAUSE_TRANSFORMS_TO_{new_cause}"
            explanation = f"Failure switches from {original_cause} to {new_cause}."
        else:
            causal_outcome = "OUTCOME_UNCHANGED"
            explanation = "Hypothetical changes insufficient to alter the primary failure pathway."

        return {
            "applied_hypotheses": applied_hypotheses,
            "original_root_cause": original_cause,
            "counterfactual_root_cause": new_cause,
            "causal_outcome": causal_outcome,
            "confidence": mutated_ml_pred.get("confidence", 0.0),
            "assigned_team": mutated_ml_pred.get("assigned_team", ""),
            "explanation": explanation,
            "mutated_evidence": mutated_evidence,
            "mutated_events": mutated_events,
            "mutated_rule": mutated_rule_eval,
            "mutated_ml": mutated_ml_pred,
            "mutated_anomaly": mutated_anomaly
        }

    @classmethod
    def evaluate_self_healing_policy(
        cls,
        evidence: Dict[str, Any],
        ml_prediction: Dict[str, Any],
        anomaly_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Autonomous Micro-Dispute Self-Healing Policy.
        Allows instant automated settlement for low-risk micro-disputes (e.g. <= ৳500),
        eliminating 24-72h waiting times for small retail customers while bounding financial risk.
        """
        amount = float(evidence.get("amount", 0.0))
        predicted_cause = ml_prediction.get("predicted_root_cause", "")
        anomaly_score = float(anomaly_data.get("anomaly_score", 0.0))
        is_anomalous = anomaly_data.get("is_anomaly", False)

        # Micro-dispute self-healing eligibility criteria:
        # 1. Amount <= 500 BDT
        # 2. Predicted root cause is a proven platform/gateway fault
        # 3. Not marked as an anomaly (no velocity fraud flag)
        # 4. ML confidence >= 85%
        eligible_causes = ["MERCHANT_ACK_FAILURE", "MISSING_REVERSAL", "STATUS_SYNC_DELAY", "NETWORK_TIMEOUT"]

        is_eligible = (
            amount <= 500.0 and
            predicted_cause in eligible_causes and
            not is_anomalous and
            anomaly_score < 0.25 and
            ml_prediction.get("confidence", 0.0) >= 0.85
        )

        if is_eligible:
            return {
                "eligible": True,
                "policy_name": "upay Instant Micro-Dispute Settlement Policy (Circular 04/2022 compliant)",
                "action": "AUTO_PROVISIONAL_CREDIT",
                "recommended_action_title": "Instant Provisional Refund Triggered (৳" + str(amount) + ")",
                "resolution_time_seconds": 1.2,
                "risk_exposure_bdt": amount,
                "reconciliation_protocol": "Auto-schedule EOD merchant settlement clawback with 0 customer friction",
                "customer_impact": "Customer receives instant wallet restoration; zero 24-hour waiting period."
            }
        else:
            reasons = []
            if amount > 500.0:
                reasons.append(f"Amount ৳{amount:,.2f} exceeds micro-threshold (৳500 limit)")
            if is_anomalous or anomaly_score >= 0.25:
                reasons.append("Flagged by Isolation Forest for velocity/volume anomaly check")
            if predicted_cause not in eligible_causes:
                reasons.append(f"Root cause {predicted_cause} requires Tier 2 manual ops review")

            return {
                "eligible": False,
                "policy_name": "Standard Operational Governance Workflow",
                "action": "MANUAL_OPERATOR_DISPATCH",
                "recommended_action_title": "Manual Operator Dispatch Required",
                "reasons": reasons,
                "customer_impact": "Requires officer confirmation to prevent fraud and maintain regulatory auditability."
            }

causal_engine = CausalCounterfactualEngine()
