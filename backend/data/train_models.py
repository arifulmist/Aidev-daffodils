import os
import pandas as pd
from backend.config import settings
from backend.database import SessionLocal, init_db
from backend.services.investigator import investigator
from backend.models.root_cause_model import root_cause_ml
from backend.models.complaint_classifier import complaint_classifier
from backend.models.anomaly_model import anomaly_model

def train_all_models():
    print("=" * 60)
    print("[INIT] Training AI Models for upay Ops Intelligence...")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    # Step 1: Load generated transactions and extract evidence features
    print("Loading synthetic datasets...")
    df_tx = pd.read_csv(settings.DATA_DIR / "transactions.csv")
    df_comp = pd.read_csv(settings.DATA_DIR / "complaints.csv")

    print(f"Loaded {len(df_tx)} transactions and {len(df_comp)} complaints.")

    # Prepare evidence dataframe for Root Cause ML & Anomaly Model
    # We can reconstruct evidence for sample transactions using investigator service
    print("Extracting structured evidence features for training...")
    sample_txs = df_tx.head(5000)
    evidence_records = []

    for _, row in sample_txs.iterrows():
        tx_id = row["transaction_id"]
        inv_res = investigator.investigate(tx_id, db)
        if inv_res.get("found"):
            evidence_records.append(inv_res["evidence"])

    df_evidence = pd.DataFrame(evidence_records)
    print(f"Extracted {len(df_evidence)} evidence records.")

    # 1. Train Root Cause Random Forest
    print("\n--- [Phase 6] Training Root Cause Random Forest Model ---")
    rc_metrics = root_cause_ml.train(df_evidence)
    print(f"Root Cause Accuracy: {rc_metrics['accuracy']:.4f}, Weighted F1: {rc_metrics['f1_weighted']:.4f}")

    # 2. Train Complaint Classifier
    print("\n--- [Phase 7] Training Complaint Intent Classifier (TF-IDF + Logistic Regression) ---")
    comp_metrics = complaint_classifier.train(df_comp)
    print(f"Complaint Classifier Accuracy: {comp_metrics['accuracy']:.4f}, Weighted F1: {comp_metrics['f1_weighted']:.4f}")

    # 3. Train Operational Anomaly Detector
    print("\n--- [Phase 9] Training Operational Anomaly Detector (Isolation Forest) ---")
    anom_metrics = anomaly_model.train(df_evidence)
    print(f"Operational Anomalies Detected: {anom_metrics['detected_anomalies']} ({anom_metrics['anomaly_rate']*100:.2f}%)")

    db.close()
    print("\n[SUCCESS] All AI models successfully trained and artifacts saved to backend/saved_models/!")

if __name__ == "__main__":
    train_all_models()
