class OpenSetCoverageDetector:
    """Out-of-Distribution (OOD) & Open-Set Coverage Evaluator."""

    # Symptoms validated in ML model training dataset
    ML_TRAINED_SYMPTOMS = {
        "Fever", "Cough", "Headache", "Fatigue", "Chest Pain", 
        "Shortness of Breath", "Abdominal Pain", "Sore Throat", "Joint Pain", "Nausea",
        "Vomiting", "Diarrhea", "Dizziness", "Runny Nose", "Muscle Aches",
        "Loss of Taste or Smell", "Chills", "Skin Rash", "Sweating", "Back Pain",
        "High Blood Pressure", "Frequent Urination", "Painful Urination", "Excessive Thirst", "Stiff Neck", "Confusion"
    }

    # Isolated nonspecific symptoms that cannot produce a reliable disease diagnosis alone
    NONSPECIFIC_SINGLETONS = {
        "fever", "cough", "vomiting", "fatigue", "skin rash", "headache",
        "diarrhea", "runny nose", "chills", "sweating", "dizziness", "back pain",
        "frequent urination", "painful urination"
    }

    def evaluate_coverage(self, canonical_symptoms, ml_predictions):
        """
        Evaluates whether user input falls within the validated ML model coverage domain
        and whether sufficient symptom specificity exists for an assessment.
        """
        if not canonical_symptoms:
            return {
                "is_in_ml_domain": False,
                "coverage_status": "EMPTY_INPUT",
                "message": "No symptoms provided for assessment."
            }

        user_symptom_set = set(s.strip().lower() for s in canonical_symptoms)
        trained_lower = set(s.lower() for s in self.ML_TRAINED_SYMPTOMS)

        in_domain_symptoms = user_symptom_set.intersection(trained_lower)
        out_of_domain_symptoms = user_symptom_set - trained_lower

        # Check if input is a single isolated nonspecific symptom
        if len(user_symptom_set) == 1 and list(user_symptom_set)[0] in self.NONSPECIFIC_SINGLETONS:
            return {
                "is_in_ml_domain": False,
                "coverage_status": "INSUFFICIENT_INFORMATION",
                "message": "Insufficient information for a reliable assessment. A single nonspecific symptom requires additional clinical context or symptom details.",
                "notice": "Insufficient information for a reliable assessment."
            }

        if len(in_domain_symptoms) == 0:
            return {
                "is_in_ml_domain": False,
                "coverage_status": "OPEN_SET_UNSUPPORTED_CASE",
                "message": "The reported symptoms fall outside the current assessment coverage domain.",
                "notice": "This case is outside the current assessment coverage."
            }

        return {
            "is_in_ml_domain": True,
            "coverage_status": "VALIDATED_ML_COVERAGE",
            "in_domain_count": len(in_domain_symptoms),
            "out_of_domain_count": len(out_of_domain_symptoms),
            "out_of_domain_symptoms": list(out_of_domain_symptoms),
            "message": "Input symptoms fall within the supported assessment domain."
        }

open_set_detector = OpenSetCoverageDetector()
