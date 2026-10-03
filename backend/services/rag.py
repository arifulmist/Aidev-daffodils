import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.database import HistoricalCase

class SimilarCaseRAG:
    """
    Similar Case Retrieval Engine (Phase 10).
    Indexes resolved historical dispute incidents and retrieves the Top-3 nearest
    precedents based on semantic similarity of factual symptoms and complaint descriptions.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.corpus_cases = []
        self.tfidf_matrix = None

    def _sync_index(self, db: Session):
        cases: List[HistoricalCase] = db.query(HistoricalCase).all()
        if not cases:
            return

        self.corpus_cases = cases
        texts = [
            f"{c.title} {c.scenario} {c.symptoms} {c.root_cause} {c.resolution}"
            for c in cases
        ]
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)

    def retrieve_similar_cases(
        self,
        query_text: str,
        db: Session,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        if not self.corpus_cases or self.tfidf_matrix is None:
            self._sync_index(db)

        if not self.corpus_cases or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query_text])
        sim_scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        top_indices = sim_scores.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(sim_scores[idx])
            c = self.corpus_cases[idx]
            results.append({
                "case_code": c.case_code,
                "title": c.title,
                "scenario": c.scenario,
                "symptoms": c.symptoms,
                "root_cause": c.root_cause,
                "resolution": c.resolution,
                "assigned_team": c.assigned_team,
                "similarity_score": round(max(0.1, score), 3)
            })

        return results

rag_service = SimilarCaseRAG()
