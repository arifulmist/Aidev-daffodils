import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.database import Transaction

class TransactionMatcher:
    """
    Transaction Candidate Matching Service (Phase 8).
    Extracts implicit cues (amount, merchant ID, customer ID) from customer complaint
    and queries candidate transactions with confidence ranking for operator confirmation.
    """

    def extract_cues_from_text(self, text: str) -> Dict[str, Any]:
        cues = {
            "amount": None,
            "merchant_id": None,
            "customer_id": None,
            "extracted_tx_id": None
        }

        # Check explicit transaction ID pattern (e.g. TX10082, TX20140)
        tx_match = re.search(r'\b(TX\d{4,6})\b', text, re.IGNORECASE)
        if tx_match:
            cues["extracted_tx_id"] = tx_match.group(1).upper()

        # Check explicit customer ID pattern (e.g. C1024, C2050)
        cust_match = re.search(r'\b(C\d{3,5})\b', text, re.IGNORECASE)
        if cust_match:
            cues["customer_id"] = cust_match.group(1).upper()

        # Check merchant ID pattern (e.g. M44, M12, M88)
        merch_match = re.search(r'\b(M\d{1,4})\b', text, re.IGNORECASE)
        if merch_match:
            cues["merchant_id"] = merch_match.group(1).upper()

        # Extract amount (supports "৳2500", "2,500 taka", "2500 BDT", "2500 tk", "2500")
        amt_match = re.search(r'(?:[৳$]|taka|tk|bdt)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(?:[৳$]|taka|tk|bdt)?', text, re.IGNORECASE)
        if amt_match:
            try:
                clean_num = amt_match.group(1).replace(",", "")
                val = float(clean_num)
                # Filter out numbers that look like dates/years
                if 10.0 <= val <= 250000.0 and val != 2026.0:
                    cues["amount"] = val
            except ValueError:
                pass

        return cues

    def find_candidates(
        self,
        db: Session,
        customer_id: Optional[str] = None,
        amount: Optional[float] = None,
        merchant_id: Optional[str] = None,
        complaint_text: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        # If complaint text provided, extract missing cues
        if complaint_text:
            extracted = self.extract_cues_from_text(complaint_text)
            if not customer_id and extracted["customer_id"]:
                customer_id = extracted["customer_id"]
            if not amount and extracted["amount"]:
                amount = extracted["amount"]
            if not merchant_id and extracted["merchant_id"]:
                merchant_id = extracted["merchant_id"]
            if extracted["extracted_tx_id"]:
                # If exact TX is mentioned, return it directly at highest confidence
                exact = db.query(Transaction).filter(Transaction.transaction_id == extracted["extracted_tx_id"]).first()
                if exact:
                    return [self._format_candidate(exact, match_score=1.0, reason="Exact Transaction ID matched")]

        query = db.query(Transaction)

        if customer_id:
            query = query.filter(Transaction.customer_id == customer_id)
        
        candidates = query.order_by(Transaction.created_at.desc()).limit(50).all()

        # Score candidates based on multidimensional match (amount, merchant, status)
        scored_candidates = []
        for tx in candidates:
            score = 0.50
            reasons = []

            if customer_id and tx.customer_id == customer_id:
                score += 0.20
                reasons.append("Customer ID match")

            if amount:
                diff = abs(tx.amount - amount)
                if diff < 1.0:
                    score += 0.35
                    reasons.append(f"Exact amount match (৳{tx.amount:,.2f})")
                elif diff <= 50.0:
                    score += 0.15
                    reasons.append(f"Near amount match (diff ৳{diff:.2f})")

            if merchant_id and tx.merchant_id == merchant_id:
                score += 0.25
                reasons.append(f"Merchant {merchant_id} match")

            if tx.transaction_status in ["FAILED", "PENDING"]:
                score += 0.10
                reasons.append(f"Status is {tx.transaction_status}")

            final_score = min(0.99, round(score, 2))
            scored_candidates.append(self._format_candidate(tx, final_score, ", ".join(reasons)))

        # Sort by match score descending
        scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_candidates[:limit]

    def _format_candidate(self, tx: Transaction, match_score: float, reason: str) -> Dict[str, Any]:
        return {
            "transaction_id": tx.transaction_id,
            "customer_id": tx.customer_id,
            "merchant_id": tx.merchant_id or "N/A",
            "amount": float(tx.amount),
            "transaction_type": tx.transaction_type,
            "status": tx.transaction_status,
            "failure_code": tx.failure_code,
            "created_at": tx.created_at.strftime("%Y-%m-%d %H:%M:%S") if tx.created_at else "",
            "time_formatted": tx.created_at.strftime("%H:%M") if tx.created_at else "",
            "match_score": match_score,
            "match_reason": reason
        }

transaction_matcher = TransactionMatcher()
