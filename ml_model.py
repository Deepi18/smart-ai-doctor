import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB

# Master list of supported symptoms
SYMPTOMS_LIST = [
    "Fever", "Cough", "Headache", "Fatigue", "Chest Pain", 
    "Shortness of Breath", "Abdominal Pain", "Sore Throat", "Joint Pain", "Nausea",
    "Vomiting", "Diarrhea", "Dizziness", "Runny Nose", "Muscle Aches",
    "Loss of Taste or Smell", "Chills", "Skin Rash", "Sweating", "Back Pain",
    "High Blood Pressure", "Frequent Urination", "Painful Urination", "Excessive Thirst", "Stiff Neck", "Confusion", "Increased Hunger"
]

# Disease Database mapping symptoms to medical information
DISEASE_DB = {
    "Influenza (Flu)": {
        "symptoms": ["Fever", "Cough", "Fatigue", "Muscle Aches", "Chills", "Sore Throat", "Runny Nose"],
        "description": "A viral infection that attacks your respiratory system including lungs, throat, and nose.",
        "urgency": "Moderate",
        "specialist": "General Physician / Pulmonologist",
        "precautions": [
            "Get plenty of rest and drink adequate fluids.",
            "Take over-the-counter fever reducers if advised by a doctor.",
            "Isolate to prevent spreading to family members."
        ]
    },
    "COVID-19": {
        "symptoms": ["Fever", "Cough", "Fatigue", "Shortness of Breath", "Loss of Taste or Smell", "Sore Throat", "Muscle Aches"],
        "description": "A respiratory illness caused by the SARS-CoV-2 virus ranging from mild to severe symptoms.",
        "urgency": "Moderate",
        "specialist": "Pulmonologist / Infectious Disease Specialist",
        "precautions": [
            "Isolate immediately and wear a mask around others.",
            "Monitor oxygen saturation (SpO2) levels using a pulse oximeter.",
            "Seek urgent medical care if experiencing severe difficulty breathing."
        ]
    },
    "Common Cold": {
        "symptoms": ["Cough", "Runny Nose", "Sore Throat", "Chills", "Fatigue"],
        "description": "A mild viral infection of the upper respiratory tract.",
        "urgency": "Low",
        "specialist": "General Practitioner",
        "precautions": [
            "Stay hydrated with warm water and herbal teas.",
            "Use saline nasal sprays or steam inhalation.",
            "Rest adequately to support immune system recovery."
        ]
    },
    "Pneumonia": {
        "symptoms": ["Fever", "Cough", "Shortness of Breath", "Chest Pain", "Fatigue", "Sweating", "Chills"],
        "description": "Infection that inflames air sacs in one or both lungs, which may fill with fluid.",
        "urgency": "High",
        "specialist": "Pulmonologist / Emergency Care Practitioner",
        "precautions": [
            "Seek urgent medical evaluation and chest X-ray.",
            "Complete prescribed antibiotic or antiviral medication.",
            "Avoid exertion and stay well rested."
        ]
    },
    "Migraine": {
        "symptoms": ["Headache", "Nausea", "Vomiting", "Dizziness", "Fatigue"],
        "description": "A neurological condition causing severe throbbing pain or pulsing sensation usually on one side of head.",
        "urgency": "Moderate",
        "specialist": "Neurologist",
        "precautions": [
            "Rest in a quiet, dark room away from bright screens.",
            "Apply cold or warm compresses to your forehead.",
            "Maintain regular sleep and hydration schedules."
        ]
    },
    "Gastroenteritis (Stomach Flu)": {
        "symptoms": ["Nausea", "Vomiting", "Diarrhea", "Abdominal Pain", "Fever", "Fatigue"],
        "description": "Intestinal infection marked by watery diarrhea, abdominal cramps, nausea, and vomiting.",
        "urgency": "Moderate",
        "specialist": "Gastroenterologist",
        "precautions": [
            "Sip Oral Rehydration Salts (ORS) frequently to prevent dehydration.",
            "Follow the BRAT diet (Bananas, Rice, Applesauce, Toast).",
            "Consult a doctor if unable to keep liquids down for 24 hours."
        ]
    },
    "Hypertension (High Blood Pressure)": {
        "symptoms": ["Headache", "Dizziness", "High Blood Pressure", "Chest Pain", "Shortness of Breath"],
        "description": "A condition in which the force of the blood against artery walls is consistently too high.",
        "urgency": "High",
        "specialist": "Cardiologist",
        "precautions": [
            "Monitor blood pressure regularly at home.",
            "Reduce dietary sodium and processed food intake.",
            "Consult a physician for prescription blood pressure management."
        ]
    },
    "Diabetes Mellitus": {
        "symptoms": ["Frequent Urination", "Excessive Thirst", "Increased Hunger", "Fatigue", "Dizziness"],
        "description": "A group of diseases that affect how your body uses blood sugar (glucose).",
        "urgency": "Moderate",
        "specialist": "Endocrinologist",
        "precautions": [
            "Check fasting blood glucose and HbA1c levels.",
            "Follow a balanced low-glycemic dietary plan.",
            "Engage in regular moderate physical exercise."
        ]
    },
    "Angina / Cardiac Event Risk": {
        "symptoms": ["Chest Pain", "Shortness of Breath", "Sweating", "Fatigue", "Dizziness"],
        "description": "Chest pain or discomfort caused by reduced blood flow to heart muscle.",
        "urgency": "High",
        "specialist": "Cardiologist / Emergency Physician",
        "precautions": [
            "⚠️ IMMEDIATE ACTION REQUIRED: Seek emergency medical care (Call 911 / 112).",
            "Stop all physical activity and sit in a comfortable position.",
            "Do not drive yourself to the emergency hospital."
        ]
    },
    "Malaria / Dengue Fever": {
        "symptoms": ["Fever", "Chills", "Sweating", "Joint Pain", "Muscle Aches", "Headache", "Nausea", "Skin Rash"],
        "description": "Mosquito-borne infectious diseases causing high fever, joint pain, and systemic infection.",
        "urgency": "High",
        "specialist": "Infectious Disease Specialist / Physician",
        "precautions": [
            "Get immediate blood test (Complete Blood Count / Malaria Parasite test).",
            "Stay thoroughly hydrated with fluids and electrolyte solutions.",
            "Avoid aspirin/ibuprofen until Dengue is ruled out by a doctor."
        ]
    },
    "Meningitis": {
        "symptoms": ["Fever", "Headache", "Stiff Neck", "Confusion", "Nausea", "Vomiting"],
        "description": "Inflammation of fluid and membranes surrounding brain and spinal cord.",
        "urgency": "High",
        "specialist": "Neurologist / Emergency Care",
        "precautions": [
            "⚠️ EMERGENCY: Seek immediate emergency room medical evaluation.",
            "Bacterial meningitis requires prompt intravenous antibiotics.",
            "Avoid delaying hospital care."
        ]
    },
    "Asthma Exacerbation": {
        "symptoms": ["Shortness of Breath", "Cough", "Chest Pain", "Fatigue"],
        "description": "Condition in which your airways narrow and swell and may produce extra mucus.",
        "urgency": "High",
        "specialist": "Pulmonologist / Allergist",
        "precautions": [
            "Use prescribed rescue inhaler (Albuterol/Salbutamol) as directed.",
            "Sit upright and stay calm to ease breathing.",
            "Seek urgent emergency care if breathing does not improve."
        ]
    },
    "Urinary Tract Infection (UTI)": {
        "symptoms": ["Painful Urination", "Frequent Urination", "Abdominal Pain", "Fever"],
        "description": "Infection in any part of your urinary system including bladder and urethra.",
        "urgency": "Moderate",
        "specialist": "Urologist / General Physician",
        "precautions": [
            "Drink plenty of water to help flush out bacteria.",
            "Consult a physician for clinical evaluation and urinalysis.",
            "Avoid holding urine for prolonged periods."
        ]
    }
}

class LocalMedicalClassifier:
    """Scikit-Learn Machine Learning Classifier for Disease Diagnosis"""
    
    def __init__(self):
        self.symptom_to_idx = {sym: idx for idx, sym in enumerate(SYMPTOMS_LIST)}
        self.diseases = list(DISEASE_DB.keys())
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self._train_dummy_synthetic_dataset()

    def _train_dummy_synthetic_dataset(self):
        """Train classifier on synthetic symptom binary vectors generated from disease DB"""
        X = []
        y = []
        
        # Generate training samples with clinical weights
        np.random.seed(42)
        for disease_name, info in DISEASE_DB.items():
            syms = info["symptoms"]
            vec = np.zeros(len(SYMPTOMS_LIST))
            for s in syms:
                if s in self.symptom_to_idx:
                    vec[self.symptom_to_idx[s]] = 1
            
            # Base exact match (weight x 50)
            for _ in range(50):
                X.append(vec.copy())
                y.append(disease_name)
            
            # Synthetic variations (drop non-essential symptoms)
            for _ in range(30):
                noisy_vec = vec.copy()
                if len(syms) > 1 and np.random.rand() > 0.3:
                    # Drop 1 symptom randomly
                    drop_symptom = np.random.choice(syms)
                    if drop_symptom in self.symptom_to_idx:
                        noisy_vec[self.symptom_to_idx[drop_symptom]] = 0
                
                # Add mild noise (only if not conflicting with primary indicators like Fever)
                if np.random.rand() > 0.85:
                    noise_idx = np.random.randint(0, len(SYMPTOMS_LIST))
                    # Prevent adding fever to non-fever conditions like Asthma/Migraine
                    if SYMPTOMS_LIST[noise_idx] != "Fever" or "Fever" in syms:
                        noisy_vec[noise_idx] = 1
                
                X.append(noisy_vec)
                y.append(disease_name)

        X = np.array(X)
        y = np.array(y)
        self.model.fit(X, y)

    def predict(self, user_symptoms):
        """
        Given a list of user symptom strings, return top ranked disease predictions.
        """
        if not user_symptoms:
            return []
        
        # Build input vector
        vec = np.zeros(len(SYMPTOMS_LIST))
        matched_count = 0
        for s in user_symptoms:
            # Case insensitive match
            s_clean = s.strip().lower()
            for known_sym, idx in self.symptom_to_idx.items():
                if s_clean == known_sym.lower() or s_clean in known_sym.lower() or known_sym.lower() in s_clean:
                    vec[idx] = 1
                    matched_count += 1

        if matched_count == 0:
            return []

        # Predict probabilities
        probabilities = self.model.predict_proba([vec])[0]
        classes = self.model.classes_

        # Sort by confidence descending
        sorted_indices = np.argsort(probabilities)[::-1]
        
        results = []
        for idx in sorted_indices[:3]:  # Top 3 predictions
            disease_name = classes[idx]
            confidence = float(probabilities[idx])
            
            # Filter low confidence predictions unless it's top 1
            if confidence < 0.08 and len(results) > 0:
                continue

            info = DISEASE_DB.get(disease_name, {
                "description": "Condition characterized by reported symptom pattern.",
                "urgency": "Moderate",
                "specialist": "General Physician",
                "precautions": ["Consult a medical healthcare provider for evaluation."]
            })

            results.append({
                "disease": disease_name,
                "confidence_percent": round(confidence * 100, 1),
                "description": info["description"],
                "urgency": info["urgency"],
                "specialist": info["specialist"],
                "precautions": info["precautions"]
            })

        return results

# Singleton instance
classifier = LocalMedicalClassifier()
