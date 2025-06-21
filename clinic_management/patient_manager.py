# This file will handle patient-related functions.
import csv
import os

DATA_DIR = 'data'
PATIENTS_FILE = os.path.join(DATA_DIR, 'patients.csv')

def generate_patient_id():
    """
    Generates a new patient ID.
    Reads patients.csv, finds the highest existing Patient ID, and returns the next integer.
    If the file doesn't exist or is empty, it starts with Patient ID 1.
    """
    try:
        if not os.path.exists(PATIENTS_FILE) or os.path.getsize(PATIENTS_FILE) == 0:
            return 1

        highest_id = 0
        with open(PATIENTS_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)  # Skip header
            if not header: # File only had a header or was empty after header
                return 1
            for row in reader:
                if row: # Ensure row is not empty
                    try:
                        patient_id = int(row[0])
                        if patient_id > highest_id:
                            highest_id = patient_id
                    except ValueError:
                        # Handle cases where PatientID might not be a valid integer in a row
                        # For now, we'll just skip such rows.
                        # A more robust solution might log this or raise an error.
                        continue
            return highest_id + 1
    except FileNotFoundError:
        return 1
    except Exception as e:
        print(f"Error generating patient ID: {e}")
        # Fallback or re-raise, depending on desired error handling
        # For now, let's assume starting from 1 if any other error occurs
        return 1

def add_patient(name: str, dob: str, contact: str):
    """
    Adds a new patient to the patients.csv file.
    Raises ValueError if inputs are invalid.
    """
    if not name or not name.strip():
        raise ValueError("Patient name cannot be empty.")
    if not dob or not dob.strip():
        raise ValueError("Date of birth cannot be empty.")
    if not contact or not contact.strip():
        raise ValueError("Contact information cannot be empty.")

    try:
        parts = dob.split('-')
        if len(parts) != 3:
            raise ValueError("Invalid DOB format. Please use YYYY-MM-DD.")
        year, month, day = parts
        if not (len(year) == 4 and len(month) == 2 and len(day) == 2 and \
                year.isdigit() and month.isdigit() and day.isdigit()):
            raise ValueError("Invalid DOB format. Year must be 4 digits, month and day must be 2 digits and all numeric (YYYY-MM-DD).")
        # Further validation like checking if month is 01-12, day is 01-31 could be added.
    except ValueError as e: # Catch specific error from split or re-raise custom ones
        raise ValueError(str(e)) # Re-raise to ensure it's a ValueError
    except Exception: # Catch any other errors during parsing, e.g. if parts are not convertible to int for further checks
        raise ValueError("Invalid DOB format. Ensure it is YYYY-MM-DD and numeric.")


    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        patient_id = generate_patient_id()
        patient_data = [patient_id, name.strip(), dob.strip(), contact.strip()]

        file_exists = os.path.exists(PATIENTS_FILE)
        is_empty = os.path.getsize(PATIENTS_FILE) == 0 if file_exists else True

        with open(PATIENTS_FILE, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if is_empty: # or not file_exists: # Ensure header is written if file was just created or found empty
                writer.writerow(['PatientID', 'Name', 'DateOfBirth', 'Contact'])
            writer.writerow(patient_data)
        # Success message will be handled by the CLI
    except Exception as e:
        # Log detailed error for server/dev, raise generic for CLI
        # For now, re-raising a more generic error or the specific one if appropriate
        raise Exception(f"An unexpected error occurred while adding the patient: {e}")


def list_patients():
    """
    Lists all patients from the patients.csv file.
    """
    try:
        if not os.path.exists(PATIENTS_FILE):
            print("No patients found.")
            return

        with open(PATIENTS_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None) # Skip header

            if not header:
                print("No patients found.") # File was empty or only had a header that was skipped
                return

            patient_found = False
            print("\n--- List of Patients ---")
            for row in reader:
                if row: # Ensure row is not empty
                    patient_found = True
                    print(f"ID: {row[0]}, Name: {row[1]}, DOB: {row[2]}, Contact: {row[3]}")

            if not patient_found:
                print("No patients found.") # Only header was present

    except FileNotFoundError:
        print("No patients found.")
    except Exception as e:
        print(f"Error listing patients: {e}")

print("Clinic Management System - patient_manager.py loaded")
