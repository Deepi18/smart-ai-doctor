import os
import json
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from config import Config

# Master List of Supported Symptoms for Vectorizer Encoding
SYMPTOMS_LIST = [
    "Fever", "Cough", "Headache", "Fatigue", "Chest Pain", 
    "Shortness of Breath", "Abdominal Pain", "Sore Throat", "Joint Pain", "Nausea",
    "Vomiting", "Diarrhea", "Dizziness", "Runny Nose", "Muscle Aches",
    "Loss of Taste or Smell", "Chills", "Skin Rash", "Sweating", "Back Pain",
    "High Blood Pressure", "Frequent Urination", "Painful Urination", "Excessive Thirst", "Stiff Neck", "Confusion", "Increased Hunger"
]

def encode_symptoms(symptoms_str, symptom_list):
    """Encodes a comma-separated symptom string into a binary feature vector."""
    vec = np.zeros(len(symptom_list), dtype=int)
    if not isinstance(symptoms_str, str):
        return vec
    
    parsed = [s.strip().lower() for s in symptoms_str.split(',') if s.strip()]
    for idx, known in enumerate(symptom_list):
        known_lower = known.lower()
        if any(known_lower in p or p in known_lower for p in parsed):
            vec[idx] = 1
    return vec

def train_and_evaluate():
    """Trains the RandomForestClassifier, computes metrics on held-out test dataset, and saves artifacts."""
    csv_path = os.path.join(Config.DATA_DIR, 'disease_symptoms.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"Loaded dataset with {len(df)} samples across {df['disease'].nunique()} conditions.")

    X = np.array([encode_symptoms(row['symptoms'], SYMPTOMS_LIST) for _, row in df.iterrows()])
    y = df['disease'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=12)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
    rec = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
    cm = confusion_matrix(y_test, y_pred, labels=clf.classes_).tolist()

    metrics = {
        "dataset_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "classes": clf.classes_.tolist(),
        "confusion_matrix": cm,
        "symptoms_list": SYMPTOMS_LIST
    }

    print("\n--- MODEL EVALUATION METRICS (HELD-OUT TEST DATASET) ---")
    print(f"Accuracy:  {round(acc * 100, 2)}%")
    print(f"Precision: {round(prec * 100, 2)}%")
    print(f"Recall:    {round(rec * 100, 2)}%")
    print(f"F1-Score:  {round(f1 * 100, 2)}%")

    model_path = os.path.join(Config.MODELS_DIR, 'disease_classifier.joblib')
    metrics_path = os.path.join(Config.MODELS_DIR, 'ml_metrics.json')

    joblib.dump(clf, model_path)
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved trained model to: {model_path}")
    print(f"Saved evaluation metrics to: {metrics_path}")

    return clf, metrics

if __name__ == "__main__":
    train_and_evaluate()
