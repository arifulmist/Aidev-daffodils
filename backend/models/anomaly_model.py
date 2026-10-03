import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.ensemble import IsolationForest
from backend.config import settings

class OperationalAnomalyModel:
    """
    Operational Anomaly Detector (Phase 9).
    Uses Isolation Forest to detect abnormal operational transaction behavior,
    unusual latency spikes, excessive retry velocity, or outlier transaction amounts.
    """

    def __init__(self):
        self.model = None
        self.feature_columns = [
            "amount",
            "duration_sec",
            "number_of_events",
            "is_failed",
            "is_high_value",
            "velocity_score"
        ]
        self.metrics_ = {}
        self.model_path = settings.SAVED_MODELS_DIR / "anomaly_iforest.joblib"
        self.meta_path = settings.SAVED_MODELS_DIR / "anomaly_meta.joblib"

    def _extract_features(self, evidence: Dict[str, Any]) -> pd.DataFrame:
        amount = float(evidence.get("amount", 0.0))
        duration = float(evidence.get("duration_sec", 0.0))
        num_events = int(evidence.get("number_of_events", 1))
        is_failed = int(evidence.get("transaction_status") == "FAILED")
        is_high_value = int(amount > 25000.0)
        
        # Velocity score heuristic based on security alert or rapid repeated transactions
        velocity = 1.0 if evidence.get("security_alert_event") else 0.1
        if duration > 20.0 or duration < 0.5:
            velocity += 0.3

        row = {
            "amount": amount,
            "duration_sec": duration,
            "number_of_events": num_events,
            "is_failed": is_failed,
            "is_high_value": is_high_value,
            "velocity_score": velocity
        }
        return pd.DataFrame([row])[self.feature_columns]

    def train(self, df_evidence: pd.DataFrame) -> Dict[str, Any]:
        os.makedirs(settings.SAVED_MODELS_DIR, exist_ok=True)

        # Build training features
        records = []
        for _, row in df_evidence.iterrows():
            amt = float(row.get("amount", 0.0))
            dur = float(row.get("duration_sec", 1.0))
            scen = row.get("ground_truth_root_cause", "")
            records.append({
                "amount": amt,
                "duration_sec": dur,
                "number_of_events": int(row.get("number_of_events", 2)),
                "is_failed": int(row.get("transaction_status") == "FAILED"),
                "is_high_value": int(amt > 25000.0),
                "velocity_score": 1.0 if scen == "SUSPICIOUS_ACTIVITY" else 0.1
            })

        X = pd.DataFrame(records)[self.feature_columns]

        # Fit Isolation Forest with 5% expected contamination
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X)

        scores = self.model.decision_function(X)
        preds = self.model.predict(X)
        anomaly_count = int(np.sum(preds == -1))

        self.metrics_ = {
            "total_samples": len(X),
            "detected_anomalies": anomaly_count,
            "anomaly_rate": round(anomaly_count / len(X), 4)
        }

        joblib.dump(self.model, self.model_path)
        joblib.dump({"metrics": self.metrics_}, self.meta_path)

        print(f"Operational Anomaly Model trained! Anomaly rate: {self.metrics_['anomaly_rate'] * 100:.2f}%")
        return self.metrics_

    def load(self) -> bool:
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
            self.model = joblib.load(self.model_path)
            meta = joblib.load(self.meta_path)
            self.metrics_ = meta["metrics"]
            return True
        return False

    def predict(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model:
            if not self.load():
                return {
                    "is_anomaly": False,
                    "anomaly_score": 0.12,
                    "status": "NORMAL",
                    "reasons": []
                }

        X_input = self._extract_features(evidence)
        raw_score = float(self.model.decision_function(X_input)[0])
        pred = int(self.model.predict(X_input)[0])

        # Normalize score into [0.0, 1.0] where 1.0 is extremely anomalous
        # decision_function gives negative for anomalies, positive for normal
        norm_score = float(1.0 / (1.0 + np.exp(raw_score * 4.0)))

        is_anomaly = bool(pred == -1 or norm_score > 0.65)
        status = "ANOMALOUS" if is_anomaly else "NORMAL"

        reasons = []
        if float(evidence.get("amount", 0.0)) > 25000:
            reasons.append(f"High ticket value (৳{evidence.get('amount'):,.2f}) deviates from standard distribution")
        if evidence.get("security_alert_event"):
            reasons.append("Security velocity breach detected in core event log")
        if float(evidence.get("duration_sec", 0.0)) > 15.0:
            reasons.append(f"Abnormal gateway execution latency ({evidence.get('duration_sec'):.1f}s)")
        if evidence.get("duplicate_detected"):
            reasons.append("Sub-second duplicate request burst")

        return {
            "engine": "isolation_forest",
            "is_anomaly": is_anomaly,
            "anomaly_score": round(norm_score, 4),
            "status": status,
            "reasons": reasons
        }

anomaly_model = OperationalAnomalyModel()
