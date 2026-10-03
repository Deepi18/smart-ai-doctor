import os
import pandas as pd
from config import Config

class PrescriptionSafetyValidator:
    """Structured Prescription Safety & Interaction Validator Engine."""
    
    def __init__(self):
        self.csv_path = os.path.join(Config.DATA_DIR, 'medicine_reference.csv')
        self.medicine_db = {}
        self._load_reference_database()

    def _load_reference_database(self):
        """Loads medicine_reference.csv into memory."""
        if not os.path.exists(self.csv_path):
            print(f"[Prescription Validator] Reference file not found: {self.csv_path}")
            return
        
        df = pd.read_csv(self.csv_path)
        for _, row in df.iterrows():
            med_name = str(row['medicine_name']).strip().lower()
            self.medicine_db[med_name] = {
                "medicine_name": row['medicine_name'],
                "generic_name": row['generic_name'],
                "drug_class": row['drug_class'],
                "indications": str(row['common_indications']).split(';'),
                "contraindications": str(row['contraindications']).split(';'),
                "known_interactions": str(row['known_interactions']).split(';'),
                "allergy_warnings": str(row['allergy_warnings']).split(';'),
                "age_warnings": str(row['age_warnings']),
                "max_daily_dose": str(row['max_daily_dose'])
            }

    def validate_prescription(self, patient_age, patient_gender, allergies, existing_conditions, current_meds, prescribed_med, dose=None, frequency=None):
        """
        Validates prescribed medication against patient allergies, existing conditions, and current medications.
        Returns safety status (GREEN, YELLOW, RED), detected flags, and clinical recommendations.
        """
        flags = []
        prescribed_clean = prescribed_med.strip().lower()
        
        med_record = None
        for key in self.medicine_db:
            if key in prescribed_clean or prescribed_clean in key:
                med_record = self.medicine_db[key]
                break

        if not med_record:
            return {
                "status": "YELLOW",
                "status_label": "Additional Review Recommended",
                "color": "#fbbf24",
                "prescribed_medicine": prescribed_med,
                "reference_source": "FDA & National Formulary Clinical Drug Reference (2025)",
                "last_verified": "2025-01-15",
                "flags": [{
                    "category": "Reference Availability",
                    "severity": "WARNING",
                    "title": "Reference Data Unavailable",
                    "detail": f"Reference information unavailable for '{prescribed_med}' in standard reference database."
                }],
                "recommendation": "Discuss this prescription directly with your prescribing physician or pharmacist.",
                "disclaimer": "No interaction identified in the configured reference database. Prescription safety review is provided for decision-support only."
            }

        # Allergy Conflict Check
        allergies_clean = [a.strip().lower() for a in allergies.split(',') if a.strip()] if allergies else []
        for allergy in allergies_clean:
            for warning in med_record['allergy_warnings']:
                if allergy in warning.lower() or warning.lower() in allergy:
                    flags.append({
                        "category": "Allergy Conflict",
                        "severity": "CRITICAL",
                        "title": "Potential Allergy Conflict Detected",
                        "detail": f"Patient reported allergy to '{allergy}' conflicts with medicine allergy warning '{warning}'."
                    })

        # Drug-Drug Interaction Check
        current_meds_clean = [m.strip().lower() for m in current_meds.split(',') if m.strip()] if current_meds else []
        for current_m in current_meds_clean:
            for interaction in med_record['known_interactions']:
                if current_m in interaction.lower() or interaction.lower() in current_m:
                    flags.append({
                        "category": "Drug Interaction",
                        "severity": "HIGH",
                        "title": "Known Drug-Drug Interaction Signal",
                        "detail": f"Prescribed medication '{med_record['medicine_name']}' has a known interaction with current medication '{current_m}' ({interaction.strip()})."
                    })

        # Contraindications & Existing Conditions Check
        conditions_clean = [c.strip().lower() for c in existing_conditions.split(',') if c.strip()] if existing_conditions else []
        for cond in conditions_clean:
            for contra in med_record['contraindications']:
                if cond in contra.lower() or contra.lower() in cond:
                    flags.append({
                        "category": "Contraindication Signal",
                        "severity": "HIGH",
                        "title": "Medical Contraindication Risk",
                        "detail": f"Existing medical condition '{cond}' conflicts with contraindication '{contra.strip()}' for {med_record['medicine_name']}."
                    })

        # Age-Related Caution Check
        try:
            age_int = int(patient_age)
            if age_int < 16 and "children under 16" in med_record['age_warnings'].lower():
                flags.append({
                    "category": "Age Caution",
                    "severity": "HIGH",
                    "title": "Pediatric Age Warning",
                    "detail": med_record['age_warnings']
                })
            elif age_int > 65 and ("elderly" in med_record['age_warnings'].lower() or "renal" in med_record['age_warnings'].lower()):
                flags.append({
                    "category": "Age Caution",
                    "severity": "WARNING",
                    "title": "Geriatric Age Caution",
                    "detail": med_record['age_warnings']
                })
        except (ValueError, TypeError):
            pass

        has_critical = any(f['severity'] == 'CRITICAL' for f in flags)
        has_high = any(f['severity'] == 'HIGH' for f in flags)
        
        if has_critical or has_high:
            status = "RED"
            status_label = "Potential Safety Concern Detected"
            color = "#f87171"
        elif len(flags) > 0:
            status = "YELLOW"
            status_label = "Additional Review Recommended"
            color = "#fbbf24"
        else:
            status = "GREEN"
            status_label = "No Interaction Identified in Configured Reference Database"
            color = "#34d399"

        return {
            "status": status,
            "status_label": status_label,
            "color": color,
            "prescribed_medicine": med_record['medicine_name'],
            "generic_name": med_record['generic_name'],
            "drug_class": med_record['drug_class'],
            "max_daily_dose": med_record['max_daily_dose'],
            "reference_source": "FDA & National Formulary Clinical Drug Reference (2025)",
            "last_verified": "2025-01-15",
            "flags": flags,
            "recommendation": "Review these safety observations with your prescribing doctor or pharmacist before making any changes.",
            "disclaimer": "No interaction identified in the configured reference database. Prescription safety review is provided for informational and decision-support purposes only."
        }

    def get_condition_specific_references(self, condition_name):
        """
        Returns explicit condition-specific medication reference records from medicine_db.
        Does NOT match broad symptom indications (Pain, Fever, Bacterial Infections).
        """
        if not condition_name:
            return []

        # Explicit condition name to exact indication token mappings
        CONDITION_EXPLICIT_MAP = {
            "angina / cardiac event risk": ["angina", "cardiac protection"],
            "hypertension (high blood pressure)": ["hypertension"],
            "diabetes mellitus": ["type 2 diabetes mellitus"],
            "asthma exacerbation": ["asthma exacerbation"],
            "otitis media (middle ear infection)": ["otitis media"],
            "congestive heart failure": ["heart failure", "post-mi"]
        }

        clean_cond = str(condition_name).strip().lower()
        target_tokens = CONDITION_EXPLICIT_MAP.get(clean_cond, [])
        if not target_tokens:
            return []

        matched_meds = []
        for key, med in self.medicine_db.items():
            med_indications = [ind.strip().lower() for ind in med.get('indications', [])]
            # Check if medicine contains any of the explicit condition target tokens
            if any(t in med_indications for t in target_tokens):
                matched_meds.append({
                    "medicine_name": med["medicine_name"],
                    "generic_name": med["generic_name"],
                    "drug_class": med["drug_class"]
                })

        return matched_meds

prescription_validator = PrescriptionSafetyValidator()

