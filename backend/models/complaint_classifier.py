import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score
from backend.config import settings

class ComplaintClassifier:
    """
    NLP Complaint Intent Classifier (Phase 7).
    Uses TF-IDF Vectorizer + Logistic Regression with n-gram character/word support
    to accurately categorize customer dispute complaints in English and Banglish.
    """

    def __init__(self):
        self.pipeline = None
        self.metrics_ = {}
        self.model_path = settings.SAVED_MODELS_DIR / "complaint_clf.joblib"
        self.meta_path = settings.SAVED_MODELS_DIR / "complaint_meta.joblib"

    def train(self, df_complaints: pd.DataFrame) -> Dict[str, Any]:
        os.makedirs(settings.SAVED_MODELS_DIR, exist_ok=True)

        X = df_complaints["complaint_text"].fillna("")
        y = df_complaints["category"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True
            )),
            ("clf", LogisticRegression(
                max_iter=1000,
                C=2.0,
                class_weight="balanced",
                random_state=42
            ))
        ])

        self.pipeline.fit(X_train, y_train)

        y_pred = self.pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")
        report = classification_report(y_test, y_pred, output_dict=True)

        self.metrics_ = {
            "accuracy": round(float(acc), 4),
            "f1_weighted": round(float(f1), 4),
            "categories": sorted(list(set(y))),
            "classification_report": report
        }

        joblib.dump(self.pipeline, self.model_path)
        joblib.dump({"metrics": self.metrics_}, self.meta_path)

        print(f"Complaint Classifier trained! Accuracy: {acc * 100:.2f}%, F1-Score: {f1:.4f}")
        return self.metrics_

    def load(self) -> bool:
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
            self.pipeline = joblib.load(self.model_path)
            meta = joblib.load(self.meta_path)
            self.metrics_ = meta["metrics"]
            return True
        return False

    def predict(self, text: str) -> Dict[str, Any]:
        if not self.pipeline:
            if not self.load():
                return {
                    "category": "TRANSACTION_DISPUTE",
                    "confidence": 0.50,
                    "all_scores": []
                }

        probs = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        top_idx = int(np.argmax(probs))
        predicted_cat = classes[top_idx]
        confidence = float(probs[top_idx])

        # Distribution of top categories
        scores = [
            {"category": classes[i], "score": round(float(probs[i]), 4)}
            for i in np.argsort(probs)[::-1][:4]
        ]

        # Extract top keywords using tfidf
        vectorizer = self.pipeline.named_steps["tfidf"]
        feature_names = vectorizer.get_feature_names_out()
        tfidf_vec = vectorizer.transform([text]).toarray()[0]
        top_keyword_indices = np.argsort(tfidf_vec)[::-1][:5]
        top_keywords = [
            feature_names[i] for i in top_keyword_indices if tfidf_vec[i] > 0
        ]

        return {
            "predicted_category": predicted_cat,
            "confidence": round(confidence, 4),
            "top_keywords": top_keywords,
            "category_distribution": scores
        }

complaint_classifier = ComplaintClassifier()
