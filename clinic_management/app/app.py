from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature # For token generation and validation
from functools import wraps # For creating decorators

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# --- Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'clinic.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable SQLAlchemy event system if not needed
# SECRET_KEY is crucial for session management and token signing
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key_for_development_CHANGE_ME')
app.config['TOKEN_MAX_AGE_SECONDS'] = 3600 # Tokens are valid for 1 hour

# Initialize SQLAlchemy extension
db = SQLAlchemy(app)
# Initialize serializer for generating and validating tokens
auth_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# --- Models ---

class User(db.Model):
    """User model for authentication."""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Store hashed passwords

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Returns a dictionary representation of the user, excluding sensitive info."""
        return {'id': self.id, 'username': self.username}

class Patient(db.Model):
    """Patient model to store patient information."""
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.String(20)) # Consider using db.Date for better type safety
    phone_number = db.Column(db.String(20))
    medical_history_summary = db.Column(db.Text)

    # Relationships
    # One-to-many relationship with Appointment: a patient can have multiple appointments
    appointments = relationship("Appointment", back_populates="patient")
    # One-to-many relationship with MedicalNote: a patient can have multiple medical notes
    # cascade="all, delete-orphan": if a patient is deleted, their medical notes are also deleted
    medical_notes = relationship("MedicalNote", back_populates="patient", cascade="all, delete-orphan")

    def to_dict(self):
        """Returns a dictionary representation of the patient."""
        return {
            'id': self.id,
            'name': self.name,
            'date_of_birth': self.date_of_birth,
            'phone_number': self.phone_number,
            'medical_history_summary': self.medical_history_summary
        }

class Appointment(db.Model):
    """Appointment model to store appointment details."""
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, ForeignKey('patient.id'), nullable=False) # Foreign key to Patient model
    doctor_name = db.Column(db.String(100))
    appointment_datetime = db.Column(db.DateTime, nullable=False) # Stores date and time of appointment
    reason_for_visit = db.Column(db.Text)
    status = db.Column(db.String(50), default='Scheduled') # e.g., Scheduled, Completed, Cancelled

    # Relationships
    # Many-to-one relationship with Patient: an appointment belongs to one patient
    patient = relationship("Patient", back_populates="appointments")
    # One-to-many relationship with MedicalNote: an appointment can have associated medical notes
    medical_notes = relationship("MedicalNote", back_populates="appointment")

    def to_dict(self):
        """Returns a dictionary representation of the appointment."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else None, # Include patient name for convenience
            'doctor_name': self.doctor_name,
            'appointment_datetime': self.appointment_datetime.isoformat() if self.appointment_datetime else None,
            'reason_for_visit': self.reason_for_visit,
            'status': self.status
        }

class MedicalNote(db.Model):
    """MedicalNote model to store clinical notes for patients."""
    __tablename__ = 'medical_note'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, ForeignKey('patient.id'), nullable=False) # Foreign key to Patient
    appointment_id = db.Column(db.Integer, ForeignKey('appointment.id'), nullable=True) # Optional link to an Appointment
    record_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Timestamp of note creation/update
    doctor_name = db.Column(db.String(100)) # Name of the doctor making the note
    notes = db.Column(db.Text, nullable=False) # Main content of the medical note
    diagnosis = db.Column(db.Text) # Optional diagnosis
    prescribed_medication = db.Column(db.Text) # Optional prescribed medication

    # Relationships
    # Many-to-one relationship with Patient
    patient = relationship("Patient", back_populates="medical_notes")
    # Many-to-one relationship with Appointment
    appointment = relationship("Appointment", back_populates="medical_notes")

    def to_dict(self):
        """Returns a dictionary representation of the medical note."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'appointment_id': self.appointment_id,
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'doctor_name': self.doctor_name,
            'notes': self.notes,
            'diagnosis': self.diagnosis,
            'prescribed_medication': self.prescribed_medication,
            'patient_name': self.patient.name if self.patient else None, # Convenience field
            'appointment_datetime': self.appointment.appointment_datetime.isoformat() if self.appointment else None # Convenience field
        }

# --- Token Required Decorator ---
def token_required(f):
    """Decorator to protect API routes, requiring a valid Bearer token in the Authorization header."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        # Check for Authorization header and Bearer token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token_type, token = auth_header.split(None, 1) # Split "Bearer <token>"
                if token_type.lower() != 'bearer':
                    return jsonify({'message': 'Invalid token type. Use Bearer token.'}), 401
            except ValueError:
                return jsonify({'message': 'Invalid Authorization header format.'}), 401

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Deserialize and validate the token, checking for expiry
            data = auth_serializer.loads(token, max_age=app.config['TOKEN_MAX_AGE_SECONDS'])
            # Fetch the user associated with the token
            current_user = db.session.get(User, data['user_id'])
            if not current_user:
                 return jsonify({'message': 'User not found for token.'}), 401
        except SignatureExpired:
            return jsonify({'message': 'Token has expired!'}), 401
        except BadTimeSignature: # Catches various invalid signature/token errors
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e: # Catch-all for other token validation issues
            app.logger.error(f"Token validation error: {str(e)}") # Log the error
            return jsonify({'message': f'Token validation error: Unexpected issue.'}), 401

        # Pass the authenticated user object to the decorated route function
        return f(current_user, *args, **kwargs)
    return decorated_function

# --- Database Initialization ---
# Create all database tables if they don't exist, within application context
with app.app_context():
    db.create_all()

# --- Auth API Endpoints ---

@app.route('/api/register', methods=['POST'])
def register_user():
    """Registers a new user."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400

    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409 # 409 Conflict

    new_user = User(username=data['username'])
    new_user.set_password(data['password']) # Hash password before saving
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully', 'user': new_user.to_dict()}), 201

@app.route('/api/login', methods=['POST'])
def login_user():
    """Logs in an existing user and returns an authentication token."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=data['username']).first()
    # Validate user existence and password
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401 # 401 Unauthorized

    # Generate a timed token for the authenticated user
    token = auth_serializer.dumps({'user_id': user.id})
    return jsonify({'token': token, 'user': user.to_dict()}), 200

@app.route('/api/protected_test', methods=['GET'])
@token_required # Example of a protected route
def protected_test(current_user): # current_user is injected by the decorator
    """An example protected route to test token authentication."""
    return jsonify({'message': f'Hello {current_user.username}! This is a protected area.'}), 200

# --- Patient APIs (Protected) ---

@app.route('/api/patients', methods=['POST'])
@token_required
def create_patient(current_user):
    """Creates a new patient. Requires authentication."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': 'Missing patient name'}), 400
    new_patient = Patient(
        name=data['name'],
        date_of_birth=data.get('date_of_birth'),
        phone_number=data.get('phone_number'),
        medical_history_summary=data.get('medical_history_summary')
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify(new_patient.to_dict()), 201

@app.route('/api/patients', methods=['GET'])
@token_required
def get_patients(current_user):
    """Returns a list of all patients. Requires authentication."""
    patients = Patient.query.all()
    return jsonify([p.to_dict() for p in patients]), 200

@app.route('/api/patients/<int:patient_id>', methods=['GET'])
@token_required
def get_patient(current_user, patient_id):
    """Returns details of a specific patient. Requires authentication."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404
    return jsonify(patient.to_dict()), 200

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
@token_required
def update_patient(current_user, patient_id):
    """Updates an existing patient. Requires authentication."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update'}), 400

    patient.name = data.get('name', patient.name)
    patient.date_of_birth = data.get('date_of_birth', patient.date_of_birth)
    patient.phone_number = data.get('phone_number', patient.phone_number)
    patient.medical_history_summary = data.get('medical_history_summary', patient.medical_history_summary)
    db.session.commit()
    return jsonify(patient.to_dict()), 200

@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
@token_required
def delete_patient(current_user, patient_id):
    """Deletes a patient. Requires authentication."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404
    db.session.delete(patient) # Medical notes associated will be deleted due to cascade rule
    db.session.commit()
    return jsonify({'message': 'Patient deleted successfully'}), 200

# --- Appointment APIs (Protected) ---

@app.route('/api/appointments', methods=['POST'])
@token_required
def create_appointment(current_user):
    """Creates a new appointment. Requires authentication."""
    data = request.get_json()
    if not data or not data.get('patient_id') or not data.get('appointment_datetime'):
        return jsonify({'message': 'Missing required fields (patient_id, appointment_datetime)'}), 400

    try:
        # Parse appointment_datetime from ISO format string
        appointment_dt = datetime.fromisoformat(data['appointment_datetime'])
    except ValueError:
        return jsonify({'message': 'Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

    patient = db.session.get(Patient, data['patient_id'])
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    new_appt = Appointment(
        patient_id=data['patient_id'],
        doctor_name=data.get('doctor_name'),
        appointment_datetime=appointment_dt,
        reason_for_visit=data.get('reason_for_visit'),
        status=data.get('status', 'Scheduled') # Default status to 'Scheduled'
    )
    db.session.add(new_appt)
    db.session.commit()
    return jsonify(new_appt.to_dict()), 201

@app.route('/api/appointments', methods=['GET'])
@token_required
def get_appointments(current_user):
    """Returns a list of all appointments, ordered by date. Requires authentication."""
    appointments = Appointment.query.order_by(Appointment.appointment_datetime.asc()).all()
    return jsonify([a.to_dict() for a in appointments]), 200

@app.route('/api/appointments/<int:appointment_id>', methods=['GET'])
@token_required
def get_appointment(current_user, appointment_id):
    """Returns details of a specific appointment. Requires authentication."""
    appt = db.session.get(Appointment, appointment_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404
    return jsonify(appt.to_dict()), 200

@app.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
@token_required
def update_appointment(current_user, appointment_id):
    """Updates an existing appointment. Requires authentication."""
    appt = db.session.get(Appointment, appointment_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update'}), 400

    # Validate patient_id if provided for update
    if 'patient_id' in data:
        patient = db.session.get(Patient, data['patient_id'])
        if not patient:
            return jsonify({'message': 'Patient not found for update'}), 404
        appt.patient_id = data['patient_id']

    if 'appointment_datetime' in data:
        try:
            appt.appointment_datetime = datetime.fromisoformat(data['appointment_datetime'])
        except ValueError:
            return jsonify({'message': 'Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

    appt.doctor_name = data.get('doctor_name', appt.doctor_name)
    appt.reason_for_visit = data.get('reason_for_visit', appt.reason_for_visit)
    appt.status = data.get('status', appt.status)

    db.session.commit()
    return jsonify(appt.to_dict()), 200

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
@token_required
def delete_appointment(current_user, appointment_id):
    """Deletes an appointment. Requires authentication."""
    appt = db.session.get(Appointment, appointment_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404
    db.session.delete(appt)
    db.session.commit()
    return jsonify({'message': 'Appointment deleted successfully'}), 200

# --- Medical Note APIs (Protected) ---

@app.route('/api/patients/<int:patient_id>/medical_notes', methods=['POST'])
@token_required
def create_medical_note(current_user, patient_id):
    """Creates a new medical note for a specific patient. Requires authentication."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    data = request.get_json()
    if not data or not data.get('notes'):
        return jsonify({'message': 'Missing required field: notes'}), 400

    appointment_id = data.get('appointment_id')
    if appointment_id: # If an appointment_id is provided, validate it
        appointment = db.session.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({'message': 'Specified appointment_id not found'}), 404
        # Ensure the appointment belongs to the correct patient
        if appointment.patient_id != patient_id:
             return jsonify({'message': 'Appointment does not belong to this patient'}), 400

    new_note = MedicalNote(
        patient_id=patient_id,
        appointment_id=appointment_id, # Can be None
        record_date=datetime.fromisoformat(data['record_date']) if data.get('record_date') else datetime.utcnow(),
        doctor_name=data.get('doctor_name', current_user.username), # Default doctor to current authenticated user
        notes=data['notes'],
        diagnosis=data.get('diagnosis'),
        prescribed_medication=data.get('prescribed_medication')
    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify(new_note.to_dict()), 201

@app.route('/api/patients/<int:patient_id>/medical_notes', methods=['GET'])
@token_required
def get_medical_notes_for_patient(current_user, patient_id):
    """Returns all medical notes for a specific patient. Supports filtering by appointment_id. Requires authentication."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    query = MedicalNote.query.filter_by(patient_id=patient_id)
    # Optional filtering by appointment_id from query parameters
    appointment_id_filter = request.args.get('appointment_id')
    if appointment_id_filter:
        query = query.filter_by(appointment_id=appointment_id_filter)

    notes = query.order_by(MedicalNote.record_date.desc()).all() # Order by most recent first
    return jsonify([note.to_dict() for note in notes]), 200

@app.route('/api/medical_notes/<int:note_id>', methods=['GET'])
@token_required
def get_medical_note(current_user, note_id):
    """Returns details of a specific medical note. Requires authentication."""
    note = db.session.get(MedicalNote, note_id)
    if not note:
        return jsonify({'message': 'Medical note not found'}), 404
    return jsonify(note.to_dict()), 200

@app.route('/api/medical_notes/<int:note_id>', methods=['PUT'])
@token_required
def update_medical_note(current_user, note_id):
    """Updates an existing medical note. Requires authentication."""
    note = db.session.get(MedicalNote, note_id)
    if not note:
        return jsonify({'message': 'Medical note not found'}), 404

    data = request.get_json()
    if not data:
         return jsonify({'message': 'No data provided for update'}), 400

    # Handle updating appointment_id link
    if 'appointment_id' in data:
        new_appointment_id = data.get('appointment_id') # Could be None to unlink
        if new_appointment_id is not None: # If trying to link or change
            appointment = db.session.get(Appointment, new_appointment_id)
            if not appointment:
                return jsonify({'message': f'Appointment with id {new_appointment_id} not found'}), 404
            if appointment.patient_id != note.patient_id: # Security check
                 return jsonify({'message': 'Cannot link note to an appointment of a different patient'}), 400
            note.appointment_id = new_appointment_id
        else: # Explicitly setting appointment_id to null
            note.appointment_id = None

    if data.get('record_date'): # Update record_date if provided
        try:
            note.record_date = datetime.fromisoformat(data['record_date'])
        except ValueError:
            return jsonify({'message': 'Invalid record_date format. Use ISO format.'}), 400

    # Update other fields
    note.doctor_name = data.get('doctor_name', note.doctor_name)
    note.notes = data.get('notes', note.notes)
    note.diagnosis = data.get('diagnosis', note.diagnosis)
    note.prescribed_medication = data.get('prescribed_medication', note.prescribed_medication)

    db.session.commit()
    return jsonify(note.to_dict()), 200

@app.route('/api/medical_notes/<int:note_id>', methods=['DELETE'])
@token_required
def delete_medical_note(current_user, note_id):
    """Deletes a medical note. Requires authentication."""
    note = db.session.get(MedicalNote, note_id)
    if not note:
        return jsonify({'message': 'Medical note not found'}), 404

    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Medical note deleted successfully'}), 200

# --- Old Web Routes (Not protected, primarily for initial structure or basic testing) ---
# These routes are not part of the core API used by the desktop app but were part of earlier web frontend plans.
@app.route('/')
def index_web_root():
    """Basic root endpoint for the API, indicating it's running."""
    return "Clinic Management API. Use desktop app or protected API endpoints."

@app.route('/view_patients')
def view_patients_page_web():
    """Example web route, placeholder from earlier web UI plan."""
    template_path = os.path.join(app.template_folder, 'patients.html')
    if os.path.exists(template_path):
        return render_template('patients.html')
    return "Patients web view not available or template missing."


# --- Main Application Runner ---
if __name__ == '__main__':
    with app.app_context(): # Ensure operations are within Flask app context
        db.create_all() # Create database tables from models
        # Create a default admin user if no users exist, for easier initial setup
        if not User.query.first():
            print("Creating default user: admin / password123")
            default_user = User(username='admin')
            default_user.set_password('password123')
            db.session.add(default_user)
            db.session.commit()
    app.run(debug=True, port=5000) # Run the Flask development server
