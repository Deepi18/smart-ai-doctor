import os
import json
import numpy as np
import joblib
from config import Config
from train_model import SYMPTOMS_LIST, encode_symptoms
from ml_model import DISEASE_DB

class LoadedMLPredictor:
    """Production Predictor loading trained joblib model and computing Explainable AI predictions."""
    
    def __init__(self):
        self.model_path = os.path.join(Config.MODELS_DIR, 'disease_classifier.joblib')
        self.metrics_path = os.path.join(Config.MODELS_DIR, 'ml_metrics.json')
        self.model = None
        self.metrics = {}
        self.symptoms_list = SYMPTOMS_LIST
        self.symptom_to_idx = {sym: idx for idx, sym in enumerate(self.symptoms_list)}
        self._load_artifacts()

    def _load_artifacts(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"[ML Engine] Loaded trained model artifact from {self.model_path}")
        else:
            print("[ML Engine] Joblib model artifact not found. Run train_model.py first.")

        if os.path.exists(self.metrics_path):
            with open(self.metrics_path, 'r', encoding='utf-8') as f:
                self.metrics = json.load(f)

    def predict(self, user_symptoms):
        """
        Given a list of user symptoms, returns ranked predictions with qualitative pattern alignment labels.
        Excludes raw probability percentages from patient-facing output.
        """
        if not user_symptoms or self.model is None:
            return []

        vec = encode_symptoms(", ".join(user_symptoms), self.symptoms_list)
        if np.sum(vec) == 0:
            return []

        probs = self.model.predict_proba([vec])[0]
        classes = self.model.classes_

        sorted_indices = np.argsort(probs)[::-1]
        results = []

        user_symptoms_lower = [s.strip().lower() for s in user_symptoms]

        for idx in sorted_indices[:3]:
            condition_name = classes[idx]
            prob_val = float(probs[idx])
            match_score = round(prob_val * 100, 1)

            if match_score < 10.0 and len(results) > 0:
                continue

            if match_score >= 60.0:
                alignment_label = "Pattern Alignment: Strong"
            elif match_score >= 30.0:
                alignment_label = "Pattern Alignment: Moderate"
            else:
                alignment_label = "Pattern Alignment: Limited"

            disease_info = DISEASE_DB.get(condition_name, {
                "symptoms": [],
                "description": "Clinical condition corresponding to reported symptoms.",
                "urgency": "Moderate",
                "specialist": "General Physician",
                "precautions": ["Consult a medical physician for evaluation."]
            })

            expected_syms = disease_info.get("symptoms", [])

            matched_symptoms = []
            unreported_symptoms = []

            for s in expected_syms:
                s_lower = s.lower()
                if any(s_lower in u or u in s_lower for u in user_symptoms_lower):
                    matched_symptoms.append(s)
                else:
                    unreported_symptoms.append(s)

            explanation = (
                f"Symptom overlap identified between reported symptoms ({', '.join(matched_symptoms) if matched_symptoms else 'None'}) "
                f"and expected clinical features for {condition_name}."
            )

            results.append({
                "disease": condition_name,
                "model_match_score": alignment_label,
                "match_percent": match_score,
                "description": disease_info["description"],
                "urgency": disease_info["urgency"],
                "specialist": disease_info["specialist"],
                "precautions": disease_info["precautions"],
                "matched_symptoms": matched_symptoms,
                "unreported_symptoms": unreported_symptoms,
                "explanation": explanation
            })

        return results

predictor = LoadedMLPredictor()
