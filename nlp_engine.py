import re
from ml_model import SYMPTOMS_LIST

# Mapping common natural language phrases to standardized symptom names
SYNONYM_MAP = {
    "fever": "Fever",
    "high temp": "Fever",
    "temperature": "Fever",
    "hot feeling": "Fever",
    "pyrexia": "Fever",
    
    "cough": "Cough",
    "coughing": "Cough",
    "dry cough": "Cough",
    "wet cough": "Cough",
    
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
    "pain in chest": "Chest Pain",
    
    "shortness of breath": "Shortness of Breath",
    "breathing difficulty": "Shortness of Breath",
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
    
    "excessive thirst": "Excessive Thirst",
    "very thirsty": "Excessive Thirst",
    "constant thirst": "Excessive Thirst",
    
    "stiff neck": "Stiff Neck",
    "neck stiffness": "Stiff Neck",
    
    "confusion": "Confusion",
    "disoriented": "Confusion",
    "memory fog": "Confusion"
}

def extract_symptoms_from_text(user_text):
    """
    Parses free-text input and returns a unique list of recognized symptom strings.
    """
    if not user_text:
        return []
    
    text_lower = user_text.lower()
    extracted = set()
    
    # 1. Match against Synonym Map
    for phrase, canonical_symptom in SYNONYM_MAP.items():
        # Match word boundaries or substring
        pattern = r'\b' + re.escape(phrase) + r'\b'
        if re.search(pattern, text_lower) or phrase in text_lower:
            extracted.add(canonical_symptom)
            
    # 2. Match directly against Symptoms List
    for sym in SYMPTOMS_LIST:
        sym_lower = sym.lower()
        pattern = r'\b' + re.escape(sym_lower) + r'\b'
        if re.search(pattern, text_lower) or sym_lower in text_lower:
            extracted.add(sym)

    return list(extracted)
