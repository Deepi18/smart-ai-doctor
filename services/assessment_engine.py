from services.ontology_manager import ontology_manager
from services.nlp_engine import extract_symptoms_from_text
from services.safety_engine import triage_engine
from services.ml_predictor import predictor
from services.knowledge_retriever import knowledge_retriever
from services.open_set_detector import open_set_detector

class MasterHybridAssessmentEngine:
    """Master Hybrid Differential Assessment Engine synthesizing ML, Knowledge Retrieval, & Safety."""

    ALIGNMENT_PRIORITY = {
        "Pattern Alignment: Strong": 3,
        "Pattern Alignment: Moderate": 2,
        "Pattern Alignment: Limited": 1
    }

    def evaluate(self, free_text_input, selected_symptoms, duration_days=None, severity=None):
        """
        Executes hybrid assessment workflow:
        1. Parse NLP + Negation
        2. Normalize to Canonical Ontology
        3. Safety Engine Triage Check
        4. ML Model Prediction
        5. Knowledge Base Retrieval
        6. Open-Set & Insufficient Information Analysis
        7. Missing Information Questions Generator
        """
        # 1. Parse free-text symptoms with negation handling
        nlp_symptoms = extract_symptoms_from_text(free_text_input) if free_text_input else []
        
        # Combine with selected pill symptoms
        raw_symptoms = list(dict.fromkeys(selected_symptoms + nlp_symptoms))
        
        # 2. Canonical Symptom Normalization
        canonical_symptoms = [ontology_manager.get_canonical_name(s) for s in raw_symptoms]
        canonical_symptoms = list(dict.fromkeys(canonical_symptoms))

        # 3. Independent Safety Triage Engine
        safety_result = triage_engine.evaluate_safety(canonical_symptoms)

        # 4. ML Model Prediction
        ml_predictions = predictor.predict(canonical_symptoms)

        # 5. Broad Medical Knowledge Retrieval
        retrieved_candidates = knowledge_retriever.retrieve_candidates(canonical_symptoms)

        # 6. Open-Set & Insufficient Information Domain Assessment
        coverage_result = open_set_detector.evaluate_coverage(canonical_symptoms, ml_predictions)

        # 7. Merge & Rank Differential Conditions using Evidence-Aware Alignment
        if coverage_result["coverage_status"] in ["INSUFFICIENT_INFORMATION", "EMPTY_INPUT", "OPEN_SET_UNSUPPORTED_CASE"]:
            differential_conditions = []
        else:
            differential_conditions = self._merge_differential(
                ml_predictions=ml_predictions if coverage_result["is_in_ml_domain"] else [],
                retrieved_candidates=retrieved_candidates
            )

        # 8. Generate Targeted Missing Information Questions
        missing_questions = self._generate_missing_questions(canonical_symptoms, duration_days, severity)

        # Determine Overall Triage Urgency Level
        urgency_levels = [c.get("urgency", "Moderate") for c in differential_conditions]
        if safety_result["is_emergency"] or "High" in urgency_levels:
            overall_urgency = "High"
        elif "Moderate" in urgency_levels:
            overall_urgency = "Moderate"
        else:
            overall_urgency = "Low"

        return {
            "canonical_symptoms": canonical_symptoms,
            "safety_result": safety_result,
            "coverage_result": coverage_result,
            "ml_predictions": ml_predictions if coverage_result["is_in_ml_domain"] else [],
            "retrieved_candidates": retrieved_candidates,
            "differential_conditions": differential_conditions,
            "missing_questions": missing_questions,
            "overall_urgency": overall_urgency,
            "duration_days": duration_days,
            "severity": severity,
            "disclaimer": (
                "AI-generated assessment for informational and decision-support purposes only. "
                "It is not a medical diagnosis and does not replace a qualified healthcare professional."
            )
        }

    def _merge_differential(self, ml_predictions, retrieved_candidates):
        """
        Merges ML predictions and retrieved candidates using an evidence-aware priority model:
        Strong > Moderate > Limited.
        Preserves non-duplicate records while prioritizing stronger evidence alignment.
        """
        candidates_map = {}

        # 1. Process Knowledge Base Candidates
        for kb in retrieved_candidates:
            name = kb["condition_name"]
            key = name.lower()
            label = kb["alignment_label"]
            priority = self.ALIGNMENT_PRIORITY.get(label, 1)

            candidates_map[key] = {
                "condition_name": name,
                "score_label": label,
                "priority": priority,
                "evidence_score": kb.get("evidence_score", 0.0),
                "source_type": "Medical Knowledge Base Retrieval",
                "description": kb["description"],
                "urgency": "Moderate",
                "specialist": kb["specialist"],
                "precautions": ["Consult a medical physician for clinical evaluation."],
                "matched_symptoms": kb["matched_symptoms"],
                "unreported_symptoms": kb["unreported_symptoms"],
                "explanation": kb["explanation"],
                "reference": kb.get("reference", "Trusted Medical Reference Database"),
                "source_url": kb.get("source_url", ""),
                "last_updated": kb.get("last_updated", "")
            }

        # 2. Process ML Predictions
        for ml in ml_predictions:
            name = ml["disease"]
            key = name.lower()
            label = ml["model_match_score"]
            priority = self.ALIGNMENT_PRIORITY.get(label, 1)

            if key in candidates_map:
                # If already exists, update priority if ML has higher alignment or preserve KB metadata
                existing = candidates_map[key]
                if priority > existing["priority"]:
                    existing["priority"] = priority
                    existing["score_label"] = label
                existing["source_type"] = "Hybrid ML Classifier & Clinical Knowledge Base"
            else:
                candidates_map[key] = {
                    "condition_name": name,
                    "score_label": label,
                    "priority": priority,
                    "evidence_score": ml.get("match_percent", 0.0),
                    "source_type": "Validated Clinical Classifier",
                    "description": ml["description"],
                    "urgency": ml["urgency"],
                    "specialist": ml["specialist"],
                    "precautions": ml["precautions"],
                    "matched_symptoms": ml["matched_symptoms"],
                    "unreported_symptoms": ml["unreported_symptoms"],
                    "explanation": ml["explanation"],
                    "reference": "Clinical Feature Match Matrix"
                }

        # Convert to list and sort by Priority descending, then evidence_score descending
        merged = list(candidates_map.values())
        merged.sort(key=lambda x: (x["priority"], x["evidence_score"]), reverse=True)

        # Attach condition-specific medication reference metadata without altering condition ranking
        from services.prescription_validator import prescription_validator
        for item in merged:
            item["medication_references"] = prescription_validator.get_condition_specific_references(item["condition_name"])

        return merged[:5]

    def _generate_missing_questions(self, canonical_symptoms, duration_days, severity):
        """Generates targeted missing information questions to refine differential assessment."""
        questions = []
        sym_set = set(s.lower() for s in canonical_symptoms)

        if not duration_days:
            questions.append("How many days have you been experiencing these symptoms?")
        if not severity:
            questions.append("How would you rate the overall severity (Mild, Moderate, or Severe)?")

        if "cough" in sym_set and "fever" not in sym_set:
            questions.append("Are you experiencing any fever or chills along with your cough?")
        if "fever" in sym_set and "cough" not in sym_set and "stiff neck" not in sym_set:
            questions.append("Do you have respiratory symptoms (cough, sore throat) or neck stiffness?")
        if "headache" in sym_set and "nausea" not in sym_set and "sensitivity to light" not in sym_set:
            questions.append("Is your headache accompanied by nausea, dizziness, or sensitivity to bright light?")
        if "vomiting" in sym_set and "diarrhea" not in sym_set:
            questions.append("Are you experiencing loose bowel movements or abdominal stomach cramps?")
        if "chest pain" in sym_set and "shortness of breath" not in sym_set:
            questions.append("Do you experience shortness of breath or pain radiating to your arm or jaw?")
        if "painful urination" in sym_set and "frequent urination" not in sym_set:
            questions.append("Are you experiencing increased urgency or frequent urination?")

        return questions

assessment_engine = MasterHybridAssessmentEngine()
