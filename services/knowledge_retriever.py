import os
import json
from config import Config
from services.ontology_manager import ontology_manager

class MedicalKnowledgeRetriever:
    """Retriever Engine ranking candidate conditions across broad medical reference data."""

    def __init__(self):
        self.kb_path = os.path.join(Config.DATA_DIR, 'medical_knowledge.json')
        self.knowledge_db = {}
        self._load_knowledge()

    def _load_knowledge(self):
        if not os.path.exists(self.kb_path):
            print(f"[Knowledge Retriever] Warning: {self.kb_path} not found.")
            return

        with open(self.kb_path, 'r', encoding='utf-8') as f:
            self.knowledge_db = json.load(f)

    def retrieve_candidates(self, canonical_symptoms):
        """
        Ranks candidate conditions based on symptom relevance, primary match weight, and overlap.
        Uses qualitative alignment labels rather than raw probability scores.
        """
        if not canonical_symptoms:
            return []

        user_symptom_set = set(s.strip().lower() for s in canonical_symptoms)
        candidates = []

        for key, cond in self.knowledge_db.items():
            primary_set = set(s.lower() for s in cond.get("primary_symptoms", []))
            secondary_set = set(s.lower() for s in cond.get("secondary_symptoms", []))
            all_cond_symptoms = primary_set.union(secondary_set)

            matched_primary = user_symptom_set.intersection(primary_set)
            matched_secondary = user_symptom_set.intersection(secondary_set)
            all_matched = matched_primary.union(matched_secondary)

            if not all_matched:
                continue

            primary_weight = len(matched_primary) * 2.0
            secondary_weight = len(matched_secondary) * 1.0
            total_weight = primary_weight + secondary_weight

            jaccard_similarity = len(all_matched) / len(user_symptom_set.union(all_cond_symptoms))
            numeric_score = round(min(95.0, (jaccard_similarity * 60.0) + (total_weight * 12.0)), 1)

            if numeric_score >= 65.0:
                alignment_label = "Pattern Alignment: Strong"
            elif numeric_score >= 40.0:
                alignment_label = "Pattern Alignment: Moderate"
            else:
                alignment_label = "Pattern Alignment: Limited"

            matched_names = [ontology_manager.get_canonical_name(s) for s in all_matched]
            unreported_names = [ontology_manager.get_canonical_name(s) for s in all_cond_symptoms if s not in all_matched]

            candidates.append({
                "condition_id": cond.get("condition_id"),
                "condition_name": cond["condition_name"],
                "category": cond.get("category", "General"),
                "alignment_label": alignment_label,
                "evidence_score": numeric_score,
                "description": cond["description"],
                "specialist": cond.get("specialist", "General Physician"),
                "reference": cond.get("reference", "Medical Knowledge Reference"),
                "source_url": cond.get("source_url", ""),
                "last_updated": cond.get("last_updated", ""),
                "matched_symptoms": matched_names,
                "unreported_symptoms": unreported_names,
                "red_flags": cond.get("red_flags", []),
                "explanation": f"Reported symptoms ({', '.join(matched_names)}) match clinical reference features for {cond['condition_name']}."
            })

        candidates.sort(key=lambda x: x["evidence_score"], reverse=True)
        return candidates[:5]

knowledge_retriever = MedicalKnowledgeRetriever()
