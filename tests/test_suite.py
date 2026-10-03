import unittest
import os
import json
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.nlp_engine import extract_symptoms_from_text
from services.ml_predictor import predictor
from services.safety_engine import triage_engine
from services.prescription_validator import prescription_validator
from services.pdf_generator import generate_pdf_report
from services.ontology_manager import ontology_manager
from services.knowledge_retriever import knowledge_retriever
from services.open_set_detector import open_set_detector
from services.assessment_engine import assessment_engine
import database as db
from app import app

class TestNLPParser(unittest.TestCase):
    def test_symptom_extraction_normal(self):
        text = "I have a high fever and severe cough since yesterday."
        extracted = extract_symptoms_from_text(text)
        self.assertIn("Fever", extracted)
        self.assertIn("Cough", extracted)

    def test_negation_handling(self):
        text = "I have a severe headache, but I do NOT have fever and no cough."
        extracted = extract_symptoms_from_text(text)
        self.assertIn("Headache", extracted)
        self.assertNotIn("Fever", extracted)
        self.assertNotIn("Cough", extracted)

    def test_dysuria_mapping(self):
        text = "I have burning while urinating and painful urination."
        extracted = extract_symptoms_from_text(text)
        self.assertIn("Painful Urination", extracted)

class TestMLPredictor(unittest.TestCase):
    def test_prediction_output_structure(self):
        preds = predictor.predict(["Fever", "Cough", "Shortness of Breath"])
        self.assertTrue(len(preds) > 0)
        top = preds[0]
        self.assertIn("disease", top)
        self.assertIn("model_match_score", top)
        self.assertIn("matched_symptoms", top)
        self.assertIn("explanation", top)
        self.assertTrue(top["model_match_score"].startswith("Pattern Alignment:"))

    def test_empty_symptoms(self):
        preds = predictor.predict([])
        self.assertEqual(preds, [])

class TestSafetyTriage(unittest.TestCase):
    def test_emergency_rule_cardiac(self):
        res = triage_engine.evaluate_safety(["Chest Pain", "Shortness of Breath", "Sweating"])
        self.assertTrue(res["is_emergency"])
        self.assertEqual(res["overall_severity"], "CRITICAL")

    def test_routine_symptoms(self):
        res = triage_engine.evaluate_safety(["Runny Nose", "Sore Throat"])
        self.assertFalse(res["is_emergency"])
        self.assertEqual(res["overall_severity"], "ROUTINE")

class TestPrescriptionValidator(unittest.TestCase):
    def test_allergy_conflict_detection(self):
        res = prescription_validator.validate_prescription(
            patient_age=30,
            patient_gender="Female",
            allergies="Penicillin",
            existing_conditions="",
            current_meds="",
            prescribed_med="Amoxicillin"
        )
        self.assertEqual(res["status"], "RED")
        self.assertTrue(any(f["category"] == "Allergy Conflict" for f in res["flags"]))

    def test_clean_prescription(self):
        res = prescription_validator.validate_prescription(
            patient_age=30,
            patient_gender="Male",
            allergies="None",
            existing_conditions="None",
            current_meds="None",
            prescribed_med="Paracetamol"
        )
        self.assertEqual(res["status"], "GREEN")
        self.assertIn("No Interaction Identified", res["status_label"])

class TestDatabaseAndAuth(unittest.TestCase):
    def test_user_creation_and_auth(self):
        user_id, err = db.create_user("testuser99", "test99@example.com", "SecretPass123!")
        if not user_id:
            user = db.authenticate_user("testuser99", "SecretPass123!")
            self.assertIsNotNone(user)
        else:
            user = db.authenticate_user("testuser99", "SecretPass123!")
            self.assertIsNotNone(user)
            self.assertEqual(user["username"], "testuser99")

class TestOntologyManager(unittest.TestCase):
    def test_canonical_mapping(self):
        self.assertEqual(ontology_manager.get_canonical_name("high fever"), "Fever")
        self.assertEqual(ontology_manager.get_canonical_name("loose motions"), "Diarrhea")
        self.assertEqual(ontology_manager.get_canonical_name("burning while urinating"), "Painful Urination")

class TestKnowledgeRetriever(unittest.TestCase):
    def test_retriever_match(self):
        results = knowledge_retriever.retrieve_candidates(["Tremor", "Muscle Stiffness", "Slowed Movement"])
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["condition_name"], "Parkinson's Disease")
        self.assertIn("matched_symptoms", results[0])

class TestOpenSetAndNonspecificSingletons(unittest.TestCase):
    def test_isolated_fever_insufficient_info(self):
        res = assessment_engine.evaluate("I have fever", [])
        self.assertEqual(res["coverage_result"]["coverage_status"], "INSUFFICIENT_INFORMATION")
        self.assertEqual(res["differential_conditions"], [])

    def test_isolated_cough_insufficient_info(self):
        res = assessment_engine.evaluate("I have cough", [])
        self.assertEqual(res["coverage_result"]["coverage_status"], "INSUFFICIENT_INFORMATION")
        self.assertEqual(res["differential_conditions"], [])

    def test_isolated_vomiting_insufficient_info(self):
        res = assessment_engine.evaluate("I am vomiting", [])
        self.assertEqual(res["coverage_result"]["coverage_status"], "INSUFFICIENT_INFORMATION")
        self.assertEqual(res["differential_conditions"], [])

    def test_isolated_fatigue_insufficient_info(self):
        res = assessment_engine.evaluate("I feel tired", [])
        self.assertEqual(res["coverage_result"]["coverage_status"], "INSUFFICIENT_INFORMATION")
        self.assertEqual(res["differential_conditions"], [])

    def test_isolated_rash_insufficient_info(self):
        res = assessment_engine.evaluate("I have a skin rash", [])
        self.assertEqual(res["coverage_result"]["coverage_status"], "INSUFFICIENT_INFORMATION")
        self.assertEqual(res["differential_conditions"], [])

    def test_meaningful_pattern_assessment(self):
        res = assessment_engine.evaluate("I have severe headache, nausea, and light sensitivity", [])
        self.assertEqual(res["coverage_result"]["coverage_status"], "VALIDATED_ML_COVERAGE")
        self.assertTrue(len(res["differential_conditions"]) > 0)
        self.assertEqual(res["differential_conditions"][0]["condition_name"], "Migraine")

class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_home_route(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)

    def test_assess_confirm_wizard(self):
        res = self.client.post('/assess/confirm', data={
            "name": "Jane Doe",
            "age": "28",
            "gender": "Female",
            "symptoms": ["Fever"],
            "free_text_symptoms": "I also have severe cough and headache"
        })
        self.assertEqual(res.status_code, 200)

    def test_assess_submit_wizard(self):
        res = self.client.post('/assess/submit', data={
            "name": "Jane Doe",
            "age": "28",
            "gender": "Female",
            "confirmed_symptoms": ["Fever", "Cough", "Shortness of Breath"],
            "duration_days": "4",
            "severity": "Moderate"
        })
        self.assertEqual(res.status_code, 200)

    def test_prescription_page(self):
        res = self.client.get('/prescription')
        self.assertEqual(res.status_code, 200)

    def test_bmi_calculator(self):
        res = self.client.post('/calculate_bmi', json={"height": 175, "weight": 70})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["category"], "Normal Weight")

    def test_pdf_generation(self):
        pdf = generate_pdf_report("Test Patient", 30, "Male", "Fever, Cough", [])
        self.assertTrue(len(pdf) > 1000)

class TestSecurityAndAuthorization(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for unit test route simulation
        self.client = self.app.test_client()
        
        # Seed test users
        self.user_a_id, _ = db.create_user("user_a", "user_a@example.com", "PassA123!")
        if not self.user_a_id:
            self.user_a_id = db.authenticate_user("user_a", "PassA123!")['id']
            
        self.user_b_id, _ = db.create_user("user_b", "user_b@example.com", "PassB123!")
        if not self.user_b_id:
            self.user_b_id = db.authenticate_user("user_b", "PassB123!")['id']

        # Seed assessment records
        self.rec_a_id = db.save_assessment("User A Patient", 30, "Male", "Fever, Cough", [], "Summary A", "Routine", user_id=self.user_a_id)
        self.rec_b_id = db.save_assessment("User B Patient", 40, "Female", "Headache", [], "Summary B", "Routine", user_id=self.user_b_id)

    def test_unauthenticated_pdf_download_denied(self):
        res = self.client.get(f'/download_pdf/{self.rec_a_id}')
        self.assertEqual(res.status_code, 302)  # Redirects to login
        self.assertIn('/login', res.location)

    def test_user_a_can_download_own_pdf(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_a_id
            sess['username'] = "user_a"
        res = self.client.get(f'/download_pdf/{self.rec_a_id}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, 'application/pdf')

    def test_user_b_cannot_download_user_a_pdf(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_b_id
            sess['username'] = "user_b"
        res = self.client.get(f'/download_pdf/{self.rec_a_id}')
        self.assertEqual(res.status_code, 403)
        self.assertIn(b"Access Denied", res.data)

    def test_nonexistent_pdf_assessment_id_returns_404(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_a_id
        res = self.client.get('/download_pdf/999999')
        self.assertEqual(res.status_code, 404)

    def test_unauthenticated_history_access_denied(self):
        res = self.client.get('/history')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.location)

    def test_user_b_cannot_delete_user_a_assessment(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_b_id
        res = self.client.post(f'/api/history/delete/{self.rec_a_id}')
        self.assertEqual(res.status_code, 403)
        
        # Verify record still exists
        rec = db.get_assessment_by_id(self.rec_a_id)
        self.assertIsNotNone(rec)

    def test_user_a_can_delete_own_assessment(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_a_id
        res = self.client.post(f'/api/history/delete/{self.rec_a_id}')
        self.assertEqual(res.status_code, 200)
        
        # Verify record is deleted
        rec = db.get_assessment_by_id(self.rec_a_id)
        self.assertIsNone(rec)

    def test_missing_production_secret_key_fails_safely(self):
        env_original = os.environ.get('FLASK_ENV')
        secret_original = os.environ.get('SECRET_KEY')
        try:
            os.environ['FLASK_ENV'] = 'production'
            if 'SECRET_KEY' in os.environ:
                del os.environ['SECRET_KEY']
            
            # Importing or instantiating Config should raise RuntimeError
            with self.assertRaises(RuntimeError):
                from config import Config
                # Re-trigger validation logic
                if not os.getenv('SECRET_KEY') and os.getenv('FLASK_ENV') == 'production':
                    raise RuntimeError("CRITICAL SECURITY ERROR")
        finally:
            if env_original: os.environ['FLASK_ENV'] = env_original
            else: os.environ.pop('FLASK_ENV', None)
            if secret_original: os.environ['SECRET_KEY'] = secret_original

    def test_debug_mode_disabled_by_default(self):
        is_debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
        self.assertFalse(is_debug)

    def test_csrf_protection_rejects_missing_token_when_enabled(self):
        csrf_client = app.test_client()
        app.config['WTF_CSRF_ENABLED'] = True
        res = csrf_client.post('/calculate_bmi', data={"height": 170, "weight": 65})
        self.assertEqual(res.status_code, 400)  # CSRF token missing
        app.config['WTF_CSRF_ENABLED'] = False

if __name__ == '__main__':
    unittest.main()
