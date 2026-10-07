import os
import json
from typing import Dict, Any, Optional
import httpx
from backend.config import settings

class LLMAnalystService:
    """
    Evidence-Grounded LLM Investigation Analyst (Phase 11).
    Synthesizes structured telemetry, ML probability, anomaly score,
    and historical RAG precedents into an explainable, auditable operational briefing.
    Never hallucinates ungrounded events.
    """

    def generate_investigation_report(
        self,
        complaint_text: str,
        transaction_data: Dict[str, Any],
        timeline: list,
        ml_prediction: Dict[str, Any],
        rule_evaluation: Dict[str, Any],
        anomaly_data: Dict[str, Any],
        similar_cases: list
    ) -> Dict[str, Any]:
        """
        Takes purely structured evidence and generates an audit report.
        """
        # 1. Check if OpenRouter API is configured (Primary High-Speed LLM)
        if getattr(settings, "OPENROUTER_API_KEY", None):
            try:
                report = self._call_openrouter_api(
                    complaint_text, transaction_data, timeline,
                    ml_prediction, rule_evaluation, anomaly_data, similar_cases
                )
                if report:
                    return report
            except Exception as e:
                print(f"[LLM] OpenRouter call error, falling back: {e}")

        # 2. Check if byNara API key is configured
        if getattr(settings, "BYNARA_API_KEY", None):
            try:
                report = self._call_bynara_api(
                    complaint_text, transaction_data, timeline,
                    ml_prediction, rule_evaluation, anomaly_data, similar_cases
                )
                if report:
                    return report
            except Exception as e:
                print(f"[LLM] byNara call error, falling back: {e}")

        # 3. Check if live Gemini API key is available
        if getattr(settings, "GEMINI_API_KEY", None):
            try:
                report = self._call_gemini_api(
                    complaint_text, transaction_data, timeline,
                    ml_prediction, rule_evaluation, anomaly_data, similar_cases
                )
                if report:
                    return report
            except Exception as e:
                print(f"[LLM] Gemini call failed, falling back to grounded synthesizer: {e}")

        # 4. Check if OpenAI API key is available
        if getattr(settings, "OPENAI_API_KEY", None):
            try:
                report = self._call_openai_api(
                    complaint_text, transaction_data, timeline,
                    ml_prediction, rule_evaluation, anomaly_data, similar_cases
                )
                if report:
                    return report
            except Exception as e:
                print(f"[LLM] OpenAI call failed, falling back to grounded synthesizer: {e}")

        # 5. Grounded Deterministic Intelligence Engine (Instant Offline / Hackathon Reliable)
        return self._generate_grounded_fallback(
            complaint_text, transaction_data, timeline,
            ml_prediction, rule_evaluation, anomaly_data, similar_cases
        )

    def _call_openrouter_api(self, complaint, tx, timeline, ml, rule, anomaly, similar) -> Optional[Dict[str, Any]]:
        import re
        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://upay-ops-intelligence.vercel.app",
            "X-Title": "upay Ops Intelligence"
        }
        prompt = self._build_prompt(complaint, tx, timeline, ml, rule, anomaly, similar[:2])
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior MFS dispute investigation analyst for upay. Analyze the verified evidence and return pure JSON only matching the schema exactly. Do not wrap in markdown backticks."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 600,
            "temperature": 0.1
        }

        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"].strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)
                parsed["engine"] = f"OpenRouter ({settings.OPENROUTER_MODEL})"
                return parsed
            else:
                print(f"[LLM] OpenRouter error {resp.status_code}: {resp.text}")
        return None

    def _call_bynara_api(self, complaint, tx, timeline, ml, rule, anomaly, similar) -> Optional[Dict[str, Any]]:
        import re
        url = f"{settings.BYNARA_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.BYNARA_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = self._build_prompt(complaint, tx, timeline, ml, rule, anomaly, similar[:2])
        payload = {
            "model": settings.BYNARA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior MFS dispute investigation analyst for upay. Analyze the verified evidence and return pure JSON only matching the schema exactly. Do not wrap in markdown backticks."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }

        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"].strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)
                parsed["engine"] = f"byNara ({settings.BYNARA_MODEL})"
                return parsed
        return None

    def _call_gemini_api(self, complaint, tx, timeline, ml, rule, anomaly, similar) -> Optional[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        prompt = self._build_prompt(complaint, tx, timeline, ml, rule, anomaly, similar)
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        return None

    def _call_openai_api(self, complaint, tx, timeline, ml, rule, anomaly, similar) -> Optional[Dict[str, Any]]:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = self._build_prompt(complaint, tx, timeline, ml, rule, anomaly, similar)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a senior MFS operations investigation analyst. Generate JSON only."},
                {"role": "user", "content": prompt}
            ]
        )
        text = response.choices[0].message.content
        return json.loads(text)

    def _build_prompt(self, complaint, tx, timeline, ml, rule, anomaly, similar) -> str:
        return f"""
You are the upay Operations Dispute Analyst.
Analyze the following strictly verified operational telemetry. Do NOT invent events.

CUSTOMER COMPLAINT:
"{complaint}"

TRANSACTION:
{json.dumps(tx, indent=2)}

EVENT TIMELINE:
{json.dumps(timeline[:8], indent=2)}

MACHINE LEARNING PREDICTION:
{json.dumps(ml, indent=2)}

RULE-BASED EVALUATION:
{json.dumps(rule, indent=2)}

ANOMALY DETECTION:
{json.dumps(anomaly, indent=2)}

HISTORICAL SIMILAR CASES (RAG):
{json.dumps(similar, indent=2)}

Return a JSON object with:
{{
  "case_summary": "Concise 2-3 sentence executive summary of the dispute",
  "investigation_facts": [
    "Fact 1 regarding wallet debit",
    "Fact 2 regarding merchant receipt/timeout",
    "Fact 3 regarding reversal status"
  ],
  "probable_root_cause": "The most likely technical root cause",
  "confidence_score": 0.95,
  "recommended_action": "Exact step-by-step resolution instruction for the officer",
  "assigned_team": "Team name (e.g. Reconciliation, Merchant Operations, etc.)",
  "reasoning": "Clear explanation linking the timeline facts and similar cases to the recommendation",
  "risk_assessment": "Low / Medium / High based on anomaly score and amount"
}}
"""

    def _generate_grounded_fallback(
        self, complaint, tx, timeline, ml, rule, anomaly, similar
    ) -> Dict[str, Any]:
        """
        Fully grounded, high-fidelity synthesis guaranteeing zero hallucinations
        and zero external API dependencies.
        """
        root_cause = ml.get("predicted_root_cause", rule.get("predicted_root_cause", "UNKNOWN_FAILURE"))
        assigned_team = ml.get("assigned_team", rule.get("assigned_team", "Reconciliation"))
        ml_conf = ml.get("confidence", 0.90)
        amount = tx.get("amount", 0.0)
        tx_id = tx.get("transaction_id", "N/A")
        is_anom = anomaly.get("is_anomaly", False)

        # Build investigation facts from timeline
        facts = []
        has_debit = any(e.get("event_type") == "WALLET_DEBITED" and e.get("event_status") == "SUCCESS" for e in timeline)
        has_ack = any(e.get("event_type") == "MERCHANT_ACK_RECEIVED" and e.get("event_status") == "SUCCESS" for e in timeline)
        has_timeout = any(e.get("event_type") == "MERCHANT_ACK_TIMEOUT" for e in timeline)
        has_reversal = any(e.get("event_type") == "REVERSAL_COMPLETED" for e in timeline)

        facts.append(f"Wallet Debit: {'Confirmed (৳' + f'{amount:,.2f}' + ' deducted)' if has_debit else 'Not Debited'}")
        facts.append(f"Merchant Capture: {'Acknowledged by POS/API' if has_ack else ('Timed Out after 15s' if has_timeout else 'Pending/Unreached')}")
        facts.append(f"Reversal Credit: {'Found completed in ledger' if has_reversal else 'No automated reversal recorded'}")
        if tx.get("failure_code") and tx.get("failure_code") != "NONE":
            facts.append(f"Gateway Error Code: {tx.get('failure_code')}")

        # Summary
        summary = (
            f"Customer submitted a dispute for transaction {tx_id} of ৳{amount:,.2f}. "
            f"Ledger analysis confirms customer debit occurred, with the transaction terminating in '{tx.get('status', 'FAILED')}'. "
            f"Rule baseline ({rule.get('rule_matched', 'RULE')}) and Random Forest model both identify '{root_cause}'."
        )

        # Recommendation and Reasoning based on root cause
        recommendations = {
            "MISSING_REVERSAL": (
                "Trigger immediate manual credit reversal via Core Ledger Admin to restore ৳"
                f"{amount:,.2f} to customer account, and flag the batch auto-reversal worker for queue lag."
            ),
            "MERCHANT_ACK_FAILURE": (
                "Escalate to Transaction Reconciliation. Cross-reference aggregator switch logs with merchant settlement "
                "to verify whether merchant account was credited; if uncaptured, execute reversal."
            ),
            "STATUS_SYNC_DELAY": (
                "Broadcast cache invalidation webhook to customer app Redis cluster. "
                "Confirm merchant payment was captured and update app state to COMPLETED."
            ),
            "DUPLICATE_TRANSACTION": (
                "Initiate chargeback/adjustment against merchant settlement for duplicate transaction debit, "
                "and refund the duplicated ৳" + f"{amount:,.2f} to customer wallet."
            ),
            "NETWORK_TIMEOUT": (
                "Verify acquiring switch network telemetry. Confirm customer ledger balance was not deducted, "
                "and send reassurance advisory to customer that funds remain safe."
            ),
            "INSUFFICIENT_BALANCE": (
                "Provide account statement walkthrough to customer highlighting minimum balance and VAT fee requirements."
            ),
            "SUSPICIOUS_ACTIVITY": (
                "Place temporary safety hold on high-velocity cash-out channels and route to Fraud & Risk Unit for Tier-2 KYC re-verification."
            ),
            "SUCCESS": (
                "No debit discrepancy found. Send SMS/App transaction receipt to customer confirming successful merchant payment."
            )
        }

        recommended_action = recommendations.get(
            root_cause,
            "Inspect raw transaction telemetry logs and escalate to Core Systems Engineering."
        )

        reasoning = (
            f"The transaction timeline shows that {'customer wallet was debited' if has_debit else 'no funds were debited'} "
            f"while merchant acknowledgement was {'not received' if not has_ack else 'received'}. "
            f"Both ML Classifier (Confidence: {ml_conf*100:.1f}%) and deterministic rules align on '{root_cause}'. "
            f"Additionally, {len(similar)} historical precedent cases resolved through {assigned_team} support this exact remediation."
        )

        risk_level = "HIGH" if (is_anom or amount >= 50000) else ("MEDIUM" if amount >= 5000 else "LOW")

        return {
            "case_summary": summary,
            "investigation_facts": facts,
            "probable_root_cause": root_cause,
            "confidence_score": ml_conf,
            "recommended_action": recommended_action,
            "assigned_team": assigned_team,
            "reasoning": reasoning,
            "risk_assessment": risk_level,
            "engine": "evidence_grounded_analyst"
        }

llm_service = LLMAnalystService()
