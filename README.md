# SMART AI DOCTOR
### AI-Powered Healthcare Decision-Support & Prescription Safety Platform

> **Disclaimer**: SMART AI DOCTOR is designed strictly as an artificial intelligence educational and decision-support research project. All generated assessments, match scores, and prescription safety reviews are for informational decision-support purposes only. It does not constitute formal clinical diagnosis, medical prescription, or treatment planning, and does not replace a qualified healthcare professional.

---

## 1. Project Title
**SMART AI DOCTOR** — Intelligent Healthcare Decision-Support, Emergency Triage, and Prescription Safety Web Platform.

---

## 2. Overview
**SMART AI DOCTOR** is a full-stack Python decision-support web application. It combines machine-learning-based condition ranking (`RandomForestClassifier`), natural language symptom parsing with negation detection (`services/nlp_engine.py`), an independent rule-based emergency triage safety engine (`services/safety_engine.py`), structured prescription safety verification (`services/prescription_validator.py`), SQLite user session persistence (`database.py`), and automated PDF report generation (`services/pdf_generator.py`).

---

## 3. Problem Statement
When patients describe symptoms in everyday natural language (e.g., *"I have a severe headache, but no fever and no cough"*), simple keyword matching algorithms often fail by falsely flagging negated symptoms or overlooking life-threatening emergency signals. Furthermore, prescription safety checking requires strict multi-point verification (contraindications, dosage thresholds, and drug interactions) that machine learning models alone cannot guarantee deterministically.

**SMART AI DOCTOR** solves this by using a hybrid architecture: leveraging machine learning and NLP for patient-friendly symptom extraction and explainable condition ranking, while enforcing deterministic, non-overridable safety rules for emergency triage and prescription validation.

---

## 4. Key Features
- **Explainable AI Disease Ranking**: Ranks top clinical conditions based on matching symptoms, displaying model confidence scores, matched symptoms (`✓`), and unreported typical symptoms (`•`).
- **Natural Language Parsing with Negation Detection**: Extracts canonical symptom IDs from free text while filtering out negated phrases (`"no fever"`, `"without cough"`).
- **Independent Emergency Triage Engine**: Evaluates high-risk clinical triggers (e.g., *Chest Pain + Shortness of Breath*, *Stiff Neck + Confusion + Fever*) and raises prominent red-flag emergency alerts regardless of ML probability.
- **Structured Prescription Safety Checker**: Evaluates prescribed drugs against structured reference data (`data/medicine_reference.csv`) for drug-drug interactions, patient allergies, contraindications, age warnings, and daily dosage ceilings.
- **Condition-Based Medication Reference**: Displays informational reference drugs listed in configured clinical databases for ranked conditions without prescribing or recommending specific treatments.
- **Patient History & PDF Export**: Persists assessment records in SQLite (`smart_doctor.db`) with user authorization controls and exports formal PDF health summaries via ReportLab.
- **Session Authentication & Security Hardening**: Provides session authentication (`werkzeug.security`), owner-isolated PDF downloads, user-isolated history management, and Flask-WTF CSRF protection.

---

## 5. How It Works
The end-to-end clinical decision-support pipeline operates as follows:

```
[ User Natural Language Input ]
               │
               ▼
   [ 1. NLP Extraction & Negation Parsing ]
   (Identifies affirmative symptoms & strips negated phrases)
               │
               ▼
   [ 2. Symptom Ontology Mapping ]
   (Maps extracted phrases to canonical SYM_* IDs in symptom_ontology.json)
               │
               ▼
   [ 3. Deterministic Emergency Triage Check ]
   (Evaluates critical red-flag rules; triggers non-overridable SOS alert if matched)
               │
               ▼
   [ 4. ML Condition Ranking & Evidence Scoring ]
   (RandomForestClassifier & pattern alignment scoring calculate match percentages)
               │
               ▼
   [ 5. Explainable AI & Patient-Facing Result Assembly ]
   (Formats matched symptoms, missing typical symptoms, specialist recommendations, and medication references)
```

---

## 6. System Architecture

### Core Components
1. **Frontend Layer**: Responsive HTML5, Vanilla CSS (Glassmorphism design system), and AJAX JavaScript (`static/script.js`) with CSRF meta token header propagation.
2. **Web Framework & Controller**: Flask web server (`app.py`) managing routing, session authentication (`@login_required`), user data isolation, and CSRF protection (`Flask-WTF`).
3. **Intelligence Engines (`services/`)**:
   - `nlp_engine.py`: Natural language processing with phrase normalization and negation detection.
   - `ml_predictor.py`: Pre-trained `RandomForestClassifier` inference engine.
   - `safety_engine.py`: Rule-based emergency triage classifier.
   - `prescription_validator.py`: Multi-factor prescription safety reviewer.
   - `pdf_generator.py`: PDF document builder using ReportLab.
4. **Data & Persistence Layer**:
   - `data/disease_symptoms.csv`: Multi-symptom clinical training dataset (30+ conditions).
   - `data/symptom_ontology.json`: Canonical symptom ontology registry.
   - `data/medicine_reference.csv`: Drug safety, interaction, and dosage reference database.
   - `smart_doctor.db`: SQLite database for user accounts, doctor directory, and assessment history.

---

## 7. Technology Stack
- **Language**: Python 3.10+
- **Web Framework**: Flask, Flask-WTF, Werkzeug Security
- **Machine Learning & Data Science**: Scikit-Learn, Joblib, Pandas, NumPy
- **Natural Language Processing**: RegEx-based clinical pattern matcher with negation parsing, spaCy
- **Document Generation**: ReportLab
- **Database**: SQLite 3
- **Frontend**: HTML5, Vanilla CSS, JavaScript (ES6 AJAX), FontAwesome 6, Bootstrap 5
- **Configuration & Security**: Python-Dotenv, Werkzeug password hashing

---

## 8. Project Structure
```
smart_ai_doctor/
├── app.py                      # Flask Application Controller & API Routes
├── config.py                   # Environment Configuration & Secret Key Security
├── train_model.py              # ML Training & Model Artifact Generation Script
├── database.py                 # SQLite ORM, User Auth & History Management
├── seed_db.py                  # Database Seeder (Doctors Directory & Library)
│
├── services/                   # Business & Clinical Logic Engines
│   ├── ml_predictor.py         # Loaded ML Model Predictor & Feature Scaling
│   ├── nlp_engine.py           # Symptom Extractor & Negation Detection Engine
│   ├── safety_engine.py        # Rule-Based Emergency Triage Classifier
│   ├── prescription_validator.py # Structured Prescription Safety Engine
│   └── pdf_generator.py        # ReportLab PDF Report Generator
│
├── data/                       # Clinical Reference Datasets
│   ├── disease_symptoms.csv    # Training Dataset (30+ Conditions)
│   ├── symptom_ontology.json   # Canonical Symptom ID & Synonym Mapping
│   └── medicine_reference.csv  # Drug Interaction & Safety Reference Database
│
├── models/                     # Trained ML Artifacts
│   ├── disease_classifier.joblib # Trained RandomForest Model
│   └── ml_metrics.json         # Held-out Evaluation Performance Metrics
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Base Layout, Emergency SOS Banner & CSRF Meta
│   ├── index.html              # Symptom Assessment Portal & Input Form
│   ├── confirm_symptoms.html   # Step 2 Symptom Review & Confirmation
│   ├── result.html             # Assessment Results & Explainable AI View
│   ├── prescription.html       # Prescription Safety Review Input Form
│   ├── prescription_result.html# Prescription Safety Analysis Output
│   ├── doctors.html            # Specialist Doctor Directory
│   ├── history.html            # User Assessment History Log
│   ├── login.html              # User Authentication Login Page
│   └── register.html           # User Account Registration Page
│
├── static/                     # Static Web Assets
│   ├── style.css               # Modern Glassmorphism CSS Design System
│   └── script.js               # Dynamic AJAX Handling & CSRF Header Propagation
│
├── tests/                      # Automated Unit Test Suite
│   └── test_suite.py           # Complete Test Suite (34 Unit & Security Tests)
│
├── requirements.txt            # Python Package Dependencies
├── .env.example                # Environment Variables Configuration Template
├── .gitignore                  # Git Exclusion Rules
└── README.md                   # Project Documentation
```

---

## 9. Installation and Setup

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 1. Clone & Navigate
```bash
git clone https://github.com/your-username/smart_ai_doctor.git
cd smart_ai_doctor
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 10. Environment Variables
Create a `.env` file in the root directory by copying `.env.example`:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Configure your `.env` settings:
```ini
# App Configuration
FLASK_ENV=development
SECRET_KEY=your-secure-random-secret-key-here

# Optional: OpenAI API Key (Required only for optional LLM summaries; app works 100% locally without it)
OPENAI_API_KEY=your_openai_api_key_here

# Database URI
DATABASE_URL=sqlite:///smart_doctor.db
```

---

## 11. Running the Application

### 1. Train ML Model (Generate Artifacts)
Train the `RandomForestClassifier` on `data/disease_symptoms.csv` and export model artifacts:
```bash
python train_model.py
```

### 2. Seed Database
Initialize SQLite database tables and seed doctor directory and knowledge base:
```bash
python seed_db.py
```

### 3. Start Flask Web Server
```bash
python app.py
```
Navigate to **`http://127.0.0.1:5000`** in your web browser.

---

## 12. Running Tests
The repository includes a comprehensive automated `unittest` suite covering NLP parsing, ML inference, emergency triage, prescription validation, session authentication, PDF owner authorization, CSRF protection, and environment secret handling.

Run the test suite:
```bash
python -m unittest discover -s tests -p "test_suite.py"
```

**Verified Test Result**:
```text
Ran 34 tests in 5.996s — OK
```

---

## 13. Security Features
- **PDF Authorization & Ownership Verification**: PDF downloads (`/download_pdf/<id>`) enforce session authentication (`@login_required`) and explicitly verify that `record['user_id'] == current_user_id`, blocking unauthorized access to patient reports.
- **User-Isolated History Management**: History views (`/history`) and record deletion routes (`/api/history/delete/<id>`) strictly filter and verify user ownership before performing state modifications.
- **CSRF Protection**: All POST endpoints and HTML forms are protected using `Flask-WTF` CSRF tokens, with AJAX requests automatically forwarding the `X-CSRFToken` header.
- **Secret Key Management**: Hardcoded secret keys have been removed; production environments require an explicitly configured `SECRET_KEY` environment variable.
- **Safe Debug Default**: Flask interactive debugging defaults to `debug=False` unless `FLASK_DEBUG=1` is explicitly set in development environments.

---

## 14. Medical Safety and Limitations
- **Decision-Support Scope**: SMART AI DOCTOR is designed solely as an artificial intelligence educational and research decision-support tool. It does NOT provide clinical diagnoses or prescriptions.
- **Emergency Situations**: In life-threatening emergencies (e.g., severe chest pain, dyspnea, acute neurological deficits), users must immediately call emergency medical services (911 / 112).
- **Curated Dataset Boundaries**: ML prediction accuracy and medication safety checks are bounded by the clinical data configured in `data/disease_symptoms.csv` and `data/medicine_reference.csv`.

---

## 15. Future Enhancements
- Integration of multi-lingual NLP symptom extraction.
- Expansion of structured clinical dataset coverage beyond 30+ conditions.
- Enhanced FHIR (Fast Healthcare Interoperability Resources) data import/export standards support.
- User feedback integration for doctor booking appointment scheduling.

---

## 16. Author
**AI & Data Science Specialist**  
Developed as a portfolio project showcasing machine learning, natural language processing, safety engineering, and full-stack Python web development.
