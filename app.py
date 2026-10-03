from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from openai import OpenAI
import os
import json
from config import Config
import database as db
from services.ml_predictor import predictor
from services.nlp_engine import extract_symptoms_from_text
from services.safety_engine import triage_engine
from services.prescription_validator import prescription_validator
from services.pdf_generator import generate_pdf_report
from train_model import SYMPTOMS_LIST

app = Flask(__name__)
app.config.from_object(Config)

# Enable Flask-WTF CSRF Protection globally
csrf = CSRFProtect(app)

# Initialize OpenAI Client (Strictly from environment, without hardcoded fallbacks)
client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None

def login_required(f):
    """Decorator requiring an authenticated user session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required."}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_global_vars():
    """Injects user session info into all templates."""
    return dict(session=session)

# Custom Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = db.authenticate_user(identifier, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']
            return redirect(url_for('home'))
        return render_template('login.html', error="Invalid username/email or password.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user_id, error = db.create_user(username, email, password)
        if error:
            return render_template('register.html', error=error)
        
        session['user_id'] = user_id
        session['username'] = username
        session['user_role'] = 'patient'
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Core Health Assessment Routes
from services.assessment_engine import assessment_engine

@app.route('/')
def home():
    """Healthcare Dashboard & Symptom Assessment Form."""
    return render_template('index.html', symptoms=SYMPTOMS_LIST)

@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    """Returns symptoms list and category mappings."""
    return jsonify({
        "symptoms": SYMPTOMS_LIST,
        "categories": {
            "Respiratory": ["Cough", "Shortness of Breath", "Sore Throat", "Runny Nose"],
            "General": ["Fever", "Fatigue", "Chills", "Sweating", "Muscle Aches"],
            "Neurological": ["Headache", "Dizziness", "Stiff Neck", "Confusion", "Loss of Taste or Smell"],
            "Digestive": ["Abdominal Pain", "Nausea", "Vomiting", "Diarrhea"],
            "Cardiovascular & Other": ["Chest Pain", "Joint Pain", "Skin Rash", "Back Pain", "High Blood Pressure", "Frequent Urination", "Excessive Thirst"]
        }
    })

@app.route('/assess/confirm', methods=['GET', 'POST'])
def confirm_symptoms():
    """Step 1 -> Step 2: Extract & normalize symptoms, prompt user to verify and provide context."""
    if request.method == 'GET':
        user_name = request.args.get('name', 'Anonymous Patient')
        user_age = request.args.get('age', 'Unspecified')
        user_gender = request.args.get('gender', 'Unspecified')
        selected_symptoms = request.args.getlist('symptoms')
        free_text_symptoms = request.args.get('free_text_symptoms', '').strip()
    else:
        user_name = request.form.get('name', 'Anonymous Patient')
        user_age = request.form.get('age', 'Unspecified')
        user_gender = request.form.get('gender', 'Unspecified')
        selected_symptoms = request.form.getlist('symptoms')
        free_text_symptoms = request.form.get('free_text_symptoms', '').strip()
    
    nlp_extracted = extract_symptoms_from_text(free_text_symptoms) if free_text_symptoms else []
    all_raw = list(dict.fromkeys(selected_symptoms + nlp_extracted))
    
    from services.ontology_manager import ontology_manager
    extracted_symptoms = [ontology_manager.get_canonical_name(s) for s in all_raw]
    extracted_symptoms = list(dict.fromkeys(extracted_symptoms))
    
    return render_template(
        'confirm_symptoms.html',
        name=user_name,
        age=user_age,
        gender=user_gender,
        extracted_symptoms=extracted_symptoms,
        raw_free_text=free_text_symptoms
    )

@app.route('/assess/submit', methods=['GET', 'POST'])
def submit_assessment():
    """Step 2 -> Step 3: Run Master Assessment Engine & synthesize differential results."""
    if request.method == 'GET':
        user_name = request.args.get('name', 'Anonymous Patient')
        user_age = request.args.get('age', 'Unspecified')
        user_gender = request.args.get('gender', 'Unspecified')
        confirmed_symptoms = request.args.getlist('confirmed_symptoms')
        duration_days = request.args.get('duration_days', '')
        severity = request.args.get('severity', '')
        raw_free_text = request.args.get('raw_free_text', '')
    else:
        user_name = request.form.get('name', 'Anonymous Patient')
        user_age = request.form.get('age', 'Unspecified')
        user_gender = request.form.get('gender', 'Unspecified')
        confirmed_symptoms = request.form.getlist('confirmed_symptoms')
        duration_days = request.form.get('duration_days', '')
        severity = request.form.get('severity', '')
        raw_free_text = request.form.get('raw_free_text', '')
    
    assessment_result = assessment_engine.evaluate(
        free_text_input=raw_free_text,
        selected_symptoms=confirmed_symptoms,
        duration_days=duration_days,
        severity=severity
    )
    
    symptoms_text = ", ".join(assessment_result["canonical_symptoms"]) if assessment_result["canonical_symptoms"] else "No specific symptoms reported"
    
    prompt = f"""
    You are a professional healthcare decision-support assistant.
    Patient: Name: {user_name}, Age: {user_age}, Gender: {user_gender}.
    Reported Symptoms: {symptoms_text}.
    Differential Assessment: {json.dumps(assessment_result['differential_conditions'], indent=2)}
    Emergency Status: {assessment_result['safety_result']['overall_severity']}

    Synthesize medical information:
    1. Clinical overview of top potential condition matches
    2. Recommended Next Steps (doctor visit, tests, home care)
    3. Triage Urgency Notice
    Always append disclaimer: 'AI-generated assessment for decision-support purposes only. Not a clinical diagnosis.'
    """

    ai_reply = ""
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional healthcare AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                timeout=6
            )
            ai_reply = response.choices[0].message.content.strip()
        except Exception as e:
            ai_reply = "ℹ️ [AI LLM Note: OpenAI API unavailable — Local ML & Safety Rules Active]"
    else:
        ai_reply = "ℹ️ [AI Decision-Support: Local Machine Learning & Emergency Safety Engine Active]"

    user_id = session.get('user_id')
    assessment_id = db.save_assessment(
        patient_name=user_name,
        patient_age=user_age,
        patient_gender=user_gender,
        symptoms=symptoms_text,
        ml_predictions=assessment_result["ml_predictions"],
        ai_summary=ai_reply,
        overall_urgency=assessment_result["overall_urgency"],
        user_id=user_id
    )

    return render_template(
        'result.html',
        assessment_id=assessment_id,
        name=user_name,
        age=user_age,
        gender=user_gender,
        symptoms=symptoms_text,
        symptoms_list=assessment_result["canonical_symptoms"],
        ml_predictions=assessment_result["ml_predictions"],
        assessment_result=assessment_result,
        result=assessment_result,
        ai_reply=ai_reply,
        safety_alerts=assessment_result["safety_result"],
        overall_urgency=assessment_result["overall_urgency"]
    )

@app.route('/predict', methods=['POST'])
def predict():
    """Processes symptoms via Master Hybrid Assessment Engine for direct calls."""
    user_name = request.form.get('name', 'Anonymous Patient')
    user_age = request.form.get('age', 'Unspecified')
    user_gender = request.form.get('gender', 'Unspecified')
    
    selected_symptoms = request.form.getlist('symptoms')
    free_text_symptoms = request.form.get('free_text_symptoms', '').strip()
    
    assessment_result = assessment_engine.evaluate(
        free_text_input=free_text_symptoms,
        selected_symptoms=selected_symptoms
    )
    
    symptoms_text = ", ".join(assessment_result["canonical_symptoms"]) if assessment_result["canonical_symptoms"] else "No specific symptoms reported"

    prompt = f"""
    You are a professional healthcare decision-support assistant.
    Patient: Name: {user_name}, Age: {user_age}, Gender: {user_gender}.
    Reported Symptoms: {symptoms_text}.
    Differential Assessment: {json.dumps(assessment_result['differential_conditions'], indent=2)}
    Emergency Status: {assessment_result['safety_result']['overall_severity']}

    Synthesize medical information:
    1. Clinical overview of top potential condition matches
    2. Recommended Next Steps (doctor visit, tests, home care)
    3. Triage Urgency Notice
    Always append disclaimer: 'AI-generated assessment for decision-support purposes only. Not a clinical diagnosis.'
    """

    ai_reply = ""
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional healthcare AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                timeout=6
            )
            ai_reply = response.choices[0].message.content.strip()
        except Exception as e:
            ai_reply = "ℹ️ [AI LLM Note: OpenAI API unavailable — Local ML & Safety Rules Active]"
    else:
        ai_reply = "ℹ️ [AI Decision-Support: Local Machine Learning & Emergency Safety Engine Active]"

    user_id = session.get('user_id')
    assessment_id = db.save_assessment(
        patient_name=user_name,
        patient_age=user_age,
        patient_gender=user_gender,
        symptoms=symptoms_text,
        ml_predictions=assessment_result["ml_predictions"],
        ai_summary=ai_reply,
        overall_urgency=assessment_result["overall_urgency"],
        user_id=user_id
    )

    return render_template(
        'result.html',
        assessment_id=assessment_id,
        name=user_name,
        age=user_age,
        gender=user_gender,
        symptoms=symptoms_text,
        symptoms_list=assessment_result["canonical_symptoms"],
        ml_predictions=assessment_result["ml_predictions"],
        assessment_result=assessment_result,
        result=assessment_result,
        ai_reply=ai_reply,
        safety_alerts=assessment_result["safety_result"],
        overall_urgency=assessment_result["overall_urgency"]
    )

# Prescription Safety Review Routes
@app.route('/prescription')
def prescription_page():
    return render_template('prescription.html')

@app.route('/prescription/review', methods=['POST'])
def review_prescription():
    patient_name = request.form.get('name', 'Patient')
    patient_age = request.form.get('age', 'Unspecified')
    patient_gender = request.form.get('gender', 'Unspecified')
    allergies = request.form.get('allergies', '')
    existing_conditions = request.form.get('existing_conditions', '')
    current_meds = request.form.get('current_meds', '')
    prescribed_medicine = request.form.get('prescribed_medicine', '')
    dose = request.form.get('dose', '')
    frequency = request.form.get('frequency', '')

    review_result = prescription_validator.validate_prescription(
        patient_age=patient_age,
        patient_gender=patient_gender,
        allergies=allergies,
        existing_conditions=existing_conditions,
        current_meds=current_meds,
        prescribed_med=prescribed_medicine,
        dose=dose,
        frequency=frequency
    )

    # Log Check to Database
    user_id = session.get('user_id')
    db.save_prescription_check(
        user_id=user_id,
        patient_name=patient_name,
        prescribed_medicine=prescribed_medicine,
        status=review_result['status'],
        status_label=review_result['status_label'],
        flags=review_result['flags']
    )

    return render_template('prescription_result.html', review=review_result, name=patient_name)

# Admin ML Evaluation Dashboard Route
@app.route('/ml-evaluation')
def ml_evaluation():
    """Renders Model Evaluation metrics computed on held-out test dataset."""
    metrics = predictor.metrics
    return render_template('ml_eval.html', metrics=metrics)

# Doctor Directory & Appointments
@app.route('/doctors')
def doctors_page():
    specialty = request.args.get('specialty', 'All')
    search = request.args.get('search', '')
    doctors_list = db.get_doctors(specialty=specialty, search_query=search)
    return render_template('doctors.html', doctors=doctors_list)

@app.route('/api/appointments', methods=['POST'])
def book_appointment():
    data = request.get_json() or {}
    doctor_id = data.get('doctor_id')
    patient_name = data.get('patient_name')
    patient_email = data.get('patient_email')
    appointment_date = data.get('appointment_date')
    reason = data.get('reason', '')

    if not patient_name or not patient_email or not appointment_date:
        return jsonify({"error": "Please fill out name, email, and date."}), 400

    doc_name = "Specialist Physician"
    if doctor_id:
        docs = db.get_doctors()
        for d in docs:
            if d['id'] == int(doctor_id):
                doc_name = d['name']
                break

    user_id = session.get('user_id')
    booking_id = db.create_appointment(doctor_id, doc_name, patient_name, patient_email, appointment_date, reason, user_id=user_id)
    return jsonify({
        "message": f"Appointment request submitted for {doc_name}!",
        "booking_id": booking_id
    })

# Knowledge Base Routes
@app.route('/knowledge')
def knowledge_page():
    search = request.args.get('search', '')
    cat = request.args.get('category', 'All')
    items = db.get_knowledge_items(search_query=search, category=cat)
    return render_template('knowledge.html', items=items)

# History Log Routes (Isolated by logged-in user_id)
@app.route('/history')
@login_required
def history_page():
    user_id = session.get('user_id')
    assessments_list = db.get_user_assessments(user_id=user_id)
    return render_template('history.html', assessments=assessments_list)

@app.route('/api/history/delete/<int:assessment_id>', methods=['POST', 'DELETE'])
@login_required
def delete_history_item(assessment_id):
    user_id = session.get('user_id')
    record = db.get_assessment_by_id(assessment_id)
    if not record:
        return jsonify({"error": "Record not found."}), 404
    if record['user_id'] != user_id:
        return jsonify({"error": "Unauthorized deletion."}), 403

    db.delete_assessment(assessment_id, user_id=user_id)
    return jsonify({"message": f"Record #{assessment_id} deleted."})

@app.route('/about')
def about_page():
    return render_template('about.html')

# PDF Report Streaming
@app.route('/download_pdf/<int:assessment_id>', methods=['GET', 'POST'])
@login_required
def download_pdf_by_id(assessment_id):
    user_id = session.get('user_id')
    record = db.get_assessment_by_id(assessment_id)
    if not record:
        return "Assessment Record Not Found", 404

    # Strict PDF Ownership Authorization:
    # Deny access if record has no user_id or belongs to another user.
    if not record['user_id'] or record['user_id'] != user_id:
        return "Access Denied: Unauthorized to view this report.", 403

    pdf_bytes = generate_pdf_report(
        patient_name=record['patient_name'],
        patient_age=record['patient_age'],
        patient_gender=record['patient_gender'],
        symptoms=record['symptoms'],
        predictions=record['ml_predictions'],
        ai_summary=record['ai_summary']
    )

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"AI_Health_Report_{record['patient_name'].replace(' ', '_')}_SAD-{assessment_id}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@app.route('/download_pdf', methods=['POST'])
def download_pdf_raw():
    user_name = request.form.get('name', 'Patient')
    user_age = request.form.get('age', 'Unspecified')
    user_gender = request.form.get('gender', 'Unspecified')
    symptoms = request.form.get('symptoms', '')
    ai_summary = request.form.get('ai_summary', '')
    
    symptoms_list = [s.strip() for s in symptoms.split(',') if s.strip()]
    ml_predictions = predictor.predict(symptoms_list)

    pdf_bytes = generate_pdf_report(
        patient_name=user_name,
        patient_age=user_age,
        patient_gender=user_gender,
        symptoms=symptoms,
        predictions=ml_predictions,
        ai_summary=ai_summary
    )

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"AI_Health_Report_{user_name.replace(' ', '_')}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@app.route('/calculate_bmi', methods=['POST'])
def calculate_bmi():
    data = request.get_json() or {}
    try:
        height_cm = float(data.get('height', 0))
        weight_kg = float(data.get('weight', 0))
        if height_cm <= 0 or weight_kg <= 0:
            return jsonify({"error": "Height and weight must be positive numbers."}), 400
        
        height_m = height_cm / 100.0
        bmi = round(weight_kg / (height_m * height_m), 1)
        
        if bmi < 18.5:
            category = "Underweight"
            color = "#3a86ff"
            advice = "Consider a nutrient-dense diet and consult a physician or nutritionist."
        elif 18.5 <= bmi < 25.0:
            category = "Normal Weight"
            color = "#38b000"
            advice = "Great job! Maintain a balanced diet and regular physical activity."
        elif 25.0 <= bmi < 30.0:
            category = "Overweight"
            color = "#ffb703"
            advice = "Incorporate regular exercise and monitor portion sizes."
        else:
            category = "Obesity"
            color = "#d90429"
            advice = "Consult a physician for personalized health and weight management advice."

        return jsonify({
            "bmi": bmi,
            "category": category,
            "color": color,
            "advice": advice
        })
    except ValueError:
        return jsonify({"error": "Invalid numerical input."}), 400

if __name__ == "__main__":
    is_debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(debug=is_debug, port=5000)
