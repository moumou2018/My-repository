# Clinic Management System

## Project Overview

This project is a desktop-based Clinic Management System designed to handle core administrative and medical record-keeping tasks for a gynecology clinic. It features a Python Flask backend API and a Python Tkinter frontend desktop application.

## Features

*   **User Authentication**: Secure login for application access.
*   **Patient Management**:
    *   Add, edit, and delete patient records.
    *   View a list of all patients with their details (ID, Name, Date of Birth, Phone, History Summary).
*   **Appointment Scheduling**:
    *   Schedule new appointments for patients.
    *   View, edit, and delete existing appointments.
    *   Appointments include details like patient, doctor, date/time, reason, and status.
*   **Medical Records**:
    *   Add, view/edit, and delete medical notes for each patient.
    *   Notes include doctor's name, record date, free-text notes, diagnosis, and prescribed medication.
    *   Option to link medical notes to specific appointments.

## Technology Stack

*   **Backend**:
    *   Python
    *   Flask (for the RESTful API)
    *   Flask-SQLAlchemy (for database ORM)
    *   SQLite (for the database)
    *   Werkzeug (for password hashing)
    *   ItsDangerous (for token generation and validation)
*   **Desktop UI (Frontend)**:
    *   Python
    *   Tkinter (standard Python GUI library)
    *   Requests (for making API calls to the backend)
*   **Development Environment**: Standard Python 3.x environment.

## Prerequisites

*   Python 3.7 or higher.
*   `pip` (Python package installer).

## Setup Instructions

Follow these steps to set up and run the Clinic Management System:

### 1. Backend API Setup

The backend provides the data and logic for the application.

1.  **Navigate to the Backend Directory**:
    ```bash
    cd clinic_management
    ```

2.  **Create and Activate a Python Virtual Environment** (recommended):
    ```bash
    python -m venv venv
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install Backend Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    This will install Flask, Flask-SQLAlchemy, Werkzeug, and ItsDangerous.

4.  **Run the Flask Backend Server**:
    ```bash
    python app/app.py
    ```
    The backend API will start, typically on `http://127.0.0.1:5000`.
    *   **Important**: On the first run, a SQLite database file (`clinic.db`) will be created in the `clinic_management/app/` directory.
    *   A **default user** will also be created with the following credentials:
        *   Username: `admin`
        *   Password: `password123`

    Keep this terminal window open and the backend server running while using the desktop application.

### 2. Desktop UI Setup

The desktop application is the user interface for interacting with the system.

1.  **Navigate to the Desktop App Directory** (from the project root):
    ```bash
    cd clinic_desktop_app
    ```

2.  **Create and Activate a Python Virtual Environment** (optional, can use the same as backend if preferred, but separate is cleaner):
    ```bash
    # If creating a new one:
    # python -m venv venv_desktop
    # On Windows:
    # venv_desktop\Scripts\activate
    # On macOS/Linux:
    # source venv_desktop/bin/activate
    ```

3.  **Install Desktop App Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    This will primarily install the `requests` library. Tkinter is part of the standard Python library.

4.  **Run the Tkinter Desktop Application**:
    *   **Ensure the backend Flask server is already running!**
    ```bash
    python main_desktop_app.py
    ```

## How to Use

1.  **Login**: When the desktop application starts, a login dialog will appear. Use the default credentials (`admin` / `password123`) or credentials of any user registered via the API.
2.  **Navigation**: After successful login, the main application window will appear. Use the menu buttons on the left ("Patients", "Appointments") to switch between different modules.
3.  **Patients View**:
    *   View the list of patients.
    *   Use the buttons ("Add Patient", "Edit Patient", "Delete Patient", "Refresh List") to manage patient records.
    *   When a patient is selected from the list, their medical notes will be displayed in the lower pane.
    *   Use the buttons in the "Medical Notes" section ("Add Note", "View/Edit Note", "Delete Note") to manage notes for the selected patient.
4.  **Appointments View**:
    *   View the list of scheduled appointments.
    *   Use the buttons ("Add Appointment", "Edit Appointment", "Delete Appointment", "Refresh List") to manage appointments.

---
This README provides a basic guide to get the Clinic Management System up and running.
