import re

SYNONYM_MAP = {
    "fever": "Fever",
    "feverish": "Fever",
    "high temp": "Fever",
    "high temperature": "Fever",
    "hot feeling": "Fever",
    "pyrexia": "Fever",
    
    "cough": "Cough",
    "coughing": "Cough",
    "dry cough": "Cough",
    "wet cough": "Cough",
    "severe cough": "Cough",
    
    "headache": "Headache",
    "head pain": "Headache",
    "migraine": "Headache",
    "throbbing head": "Headache",
    
    "fatigue": "Fatigue",
    "tired": "Fatigue",
    "tiredness": "Fatigue",
    "exhausted": "Fatigue",
    "low energy": "Fatigue",
    "weakness": "Fatigue",
    
    "chest pain": "Chest Pain",
    "chest discomfort": "Chest Pain",
    "tight chest": "Chest Pain",
    "chest hurts": "Chest Pain",
    "pain in chest": "Chest Pain",
    
    "shortness of breath": "Shortness of Breath",
    "breathing difficulty": "Shortness of Breath",
    "difficulty breathing": "Shortness of Breath",
    "breathless": "Shortness of Breath",
    "hard to breathe": "Shortness of Breath",
    "dyspnea": "Shortness of Breath",
    "wheezing": "Shortness of Breath",
    
    "stomach pain": "Abdominal Pain",
    "abdominal pain": "Abdominal Pain",
    "stomach ache": "Abdominal Pain",
    "tummy pain": "Abdominal Pain",
    "belly ache": "Abdominal Pain",
    
    "sore throat": "Sore Throat",
    "throat pain": "Sore Throat",
    "scratchy throat": "Sore Throat",
    "pain swallowing": "Sore Throat",
    
    "joint pain": "Joint Pain",
    "pain in joints": "Joint Pain",
    "knee pain": "Joint Pain",
    "arthralgia": "Joint Pain",
    
    "nausea": "Nausea",
    "nauseous": "Nausea",
    "feeling sick": "Nausea",
    "queasy": "Nausea",
    
    "vomiting": "Vomiting",
    "throwing up": "Vomiting",
    "puking": "Vomiting",
    
    "diarrhea": "Diarrhea",
    "loose stools": "Diarrhea",
    "loose motion": "Diarrhea",
    "watery stool": "Diarrhea",
    
    "dizziness": "Dizziness",
    "dizzy": "Dizziness",
    "lightheaded": "Dizziness",
    "spinning head": "Dizziness",
    
    "runny nose": "Runny Nose",
    "nasal congestion": "Runny Nose",
    "stuffy nose": "Runny Nose",
    "sneezing": "Runny Nose",
    
    "body ache": "Muscle Aches",
    "body pain": "Muscle Aches",
    "muscle ache": "Muscle Aches",
    "myalgia": "Muscle Aches",
    
    "loss of smell": "Loss of Taste or Smell",
    "loss of taste": "Loss of Taste or Smell",
    "cannot smell": "Loss of Taste or Smell",
    "no taste": "Loss of Taste or Smell",
    
    "chills": "Chills",
    "shivering": "Chills",
    "cold chills": "Chills",
    
    "skin rash": "Skin Rash",
    "rash": "Skin Rash",
    "skin spots": "Skin Rash",
    "itching rash": "Skin Rash",
    
    "sweating": "Sweating",
    "night sweats": "Sweating",
    "profuse sweating": "Sweating",
    
    "back pain": "Back Pain",
    "backache": "Back Pain",
    "lower back pain": "Back Pain",
    
    "high blood pressure": "High Blood Pressure",
    "hypertension": "High Blood Pressure",
    "high bp": "High Blood Pressure",
    
    "frequent urination": "Frequent Urination",
    "peeing a lot": "Frequent Urination",
    "urinating constantly": "Frequent Urination",

    "burning while urinating": "Painful Urination",
    "burning when peeing": "Painful Urination",
    "painful urination": "Painful Urination",
    "dysuria": "Painful Urination",
    "burning urine": "Painful Urination",

    "light sensitivity": "Sensitivity to Light",
    "sensitive to light": "Sensitivity to Light",
    "photophobia": "Sensitivity to Light",
    
    "excessive thirst": "Excessive Thirst",
    "very thirsty": "Excessive Thirst",
    "constant thirst": "Excessive Thirst",
    
    "stiff neck": "Stiff Neck",
    "neck stiffness": "Stiff Neck",
    
    "confusion": "Confusion",
    "disoriented": "Confusion",
    "memory fog": "Confusion",

    "increased hunger": "Increased Hunger",
    "excessive hunger": "Increased Hunger",
    "constant hunger": "Increased Hunger",
    "unusually hungry": "Increased Hunger",
    "polyphagia": "Increased Hunger"
}

NEGATION_WORDS = ["no", "not", "neither", "nor", "without", "denies", "free of", "don't", "dont", "no sign of"]

def is_phrase_negated(text_lower, phrase):
    phrase_idx = text_lower.find(phrase)
    if phrase_idx == -1:
        return False
    
    start_idx = max(0, phrase_idx - 35)
    preceding_text = text_lower[start_idx:phrase_idx].strip()
    words_before = re.findall(r'\b\w+\b', preceding_text)
    
    for word in words_before[-3:]:
        if word in NEGATION_WORDS:
            return True
    return False

def extract_symptoms_from_text(user_text):
    if not user_text:
        return []
    
    text_lower = user_text.lower()
    extracted = set()
    negated = set()
    
    for phrase, canonical_symptom in SYNONYM_MAP.items():
        if phrase in text_lower:
            if is_phrase_negated(text_lower, phrase):
                negated.add(canonical_symptom)
            else:
                extracted.add(canonical_symptom)

    final_symptoms = list(extracted - negated)
    return final_symptoms
