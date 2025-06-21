# This file will handle appointment-related functions.
import csv
import os

DATA_DIR = 'data'
APPOINTMENTS_FILE = os.path.join(DATA_DIR, 'appointments.csv')
PATIENTS_FILE = os.path.join(DATA_DIR, 'patients.csv') # Added for patient_exists

def patient_exists(patient_id: str) -> bool:
    """
    Checks if a patient with the given ID exists in patients.csv.
    """
    try:
        if not os.path.exists(PATIENTS_FILE):
            return False # No patient file means no patients
        with open(PATIENTS_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)
            if not header:
                return False # Empty file or only header
            for row in reader:
                if row and row[0] == patient_id:
                    return True
        return False
    except FileNotFoundError:
        return False # Should be caught by os.path.exists, but good practice
    except Exception as e:
        print(f"Error checking if patient exists: {e}") # Log error, assume patient doesn't exist for safety
        return False

def generate_appointment_id():
    """
    Generates a new appointment ID.
    Reads appointments.csv, finds the highest existing Appointment ID, and returns the next integer.
    If the file doesn't exist or is empty, it starts with Appointment ID 1.
    """
    try:
        if not os.path.exists(APPOINTMENTS_FILE) or os.path.getsize(APPOINTMENTS_FILE) == 0:
            return 1

        highest_id = 0
        with open(APPOINTMENTS_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)
            if not header:
                return 1
            for row in reader:
                if row:
                    try:
                        appointment_id_val = int(row[0])
                        if appointment_id_val > highest_id:
                            highest_id = appointment_id_val
                    except ValueError:
                        continue
            return highest_id + 1
    except FileNotFoundError:
        return 1
    except Exception as e:
        print(f"Error generating appointment ID: {e}")
        return 1

def schedule_appointment(patient_id: str, date: str, time: str, reason: str):
    """
    Schedules a new appointment and saves it to appointments.csv.
    Raises ValueError if inputs are invalid or patient ID does not exist.
    """
    if not patient_id or not patient_id.strip():
        raise ValueError("Patient ID cannot be empty.")
    if not date or not date.strip():
        raise ValueError("Appointment date cannot be empty.")
    if not time or not time.strip():
        raise ValueError("Appointment time cannot be empty.")
    if not reason or not reason.strip():
        raise ValueError("Reason for appointment cannot be empty.")

    if not patient_exists(patient_id.strip()):
        raise ValueError(f"Patient ID '{patient_id.strip()}' not found.")

    try:
        parts = date.split('-')
        if len(parts) != 3:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
        year, month, day = parts
        if not (len(year) == 4 and len(month) == 2 and len(day) == 2 and \
                year.isdigit() and month.isdigit() and day.isdigit()):
            raise ValueError("Invalid date format. Year must be 4 digits, month and day must be 2 digits and all numeric (YYYY-MM-DD).")
        # Further validation for date parts could be added (e.g. month 01-12)
    except ValueError as e: # Catch specific error from split or re-raise custom ones
        raise ValueError(str(e))
    except Exception:
        raise ValueError("Invalid date format. Ensure it is YYYY-MM-DD and numeric.")

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        appointment_id = generate_appointment_id()
        appointment_data = [appointment_id, patient_id.strip(), date.strip(), time.strip(), reason.strip()]

        file_exists = os.path.exists(APPOINTMENTS_FILE)
        is_empty = os.path.getsize(APPOINTMENTS_FILE) == 0 if file_exists else True

        with open(APPOINTMENTS_FILE, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if is_empty:
                writer.writerow(['AppointmentID', 'PatientID', 'Date', 'Time', 'Reason'])
            writer.writerow(appointment_data)
        # Success message will be handled by the CLI
    except Exception as e:
        raise Exception(f"An unexpected error occurred while scheduling the appointment: {e}")


def list_appointments():
    """
    Lists all appointments from the appointments.csv file.
    """
    try:
        if not os.path.exists(APPOINTMENTS_FILE):
            print("No appointments found.")
            return

        with open(APPOINTMENTS_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)

            if not header:
                print("No appointments found.")
                return

            appointment_found = False
            print("\n--- List of Appointments ---")
            for row in reader:
                if row:
                    appointment_found = True
                    print(f"Appt ID: {row[0]}, Patient ID: {row[1]}, Date: {row[2]}, Time: {row[3]}, Reason: {row[4]}")

            if not appointment_found:
                print("No appointments found.")

    except FileNotFoundError:
        print("No appointments found.")
    except Exception as e:
        print(f"Error listing appointments: {e}")

# Original print statement removed for cleaner module loading in CLI context
# print("Clinic Management System - appointment_manager.py loaded")
