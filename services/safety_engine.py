class SafetyTriageEngine:
    """Independent Rule-Based Emergency Triage System."""
    
    EMERGENCY_RULES = [
        {
            "id": "cardiac_risk",
            "name": "Potential Acute Cardiac Event / Angina Risk",
            "symptoms": ["Chest Pain", "Shortness of Breath"],
            "severity": "CRITICAL",
            "message": "Potential acute cardiac indicator detected (Chest Pain + Shortness of Breath). Please seek emergency medical care immediately (Call 911 / 112)."
        },
        {
            "id": "meningitis_risk",
            "name": "Potential Meningeal Inflammation Risk",
            "symptoms": ["Stiff Neck", "Confusion", "Fever"],
            "severity": "CRITICAL",
            "message": "Potential severe neurological/meningeal risk detected (Stiff Neck + Confusion + Fever). Immediate emergency department evaluation required."
        },
        {
            "id": "severe_respiratory",
            "name": "Severe Respiratory Distress Risk",
            "symptoms": ["Shortness of Breath", "Chest Pain", "Fever"],
            "severity": "HIGH",
            "message": "Severe respiratory distress signals detected. Urgent clinical chest evaluation and oxygen check recommended."
        },
        {
            "id": "hypertensive_crisis",
            "name": "Hypertensive Emergency Signal",
            "symptoms": ["High Blood Pressure", "Chest Pain", "Dizziness"],
            "severity": "HIGH",
            "message": "Potential hypertensive emergency signal detected. Seek urgent medical consultation."
        }
    ]

    def evaluate_safety(self, symptoms):
        """
        Evaluates input symptoms against emergency triage rules.
        Returns a dictionary containing triage status, alerts, and instructions.
        """
        symptoms_lower = set(s.strip().lower() for s in symptoms)
        triggered_alerts = []

        for rule in self.EMERGENCY_RULES:
            required = [s.lower() for s in rule["symptoms"]]
            # Check if all required symptoms for rule are present
            if all(any(req in sym or sym in req for sym in symptoms_lower) for req in required):
                triggered_alerts.append(rule)

        is_emergency = len(triggered_alerts) > 0
        overall_severity = "CRITICAL" if any(a["severity"] == "CRITICAL" for a in triggered_alerts) else ("HIGH" if is_emergency else "ROUTINE")

        return {
            "is_emergency": is_emergency,
            "overall_severity": overall_severity,
            "alerts": triggered_alerts,
            "disclaimer": "Emergency triage rules operate independently of ML match scores. Do not delay professional emergency medical care if experiencing severe symptoms."
        }

# Singleton Triage Engine
triage_engine = SafetyTriageEngine()
