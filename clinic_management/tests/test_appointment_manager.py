import unittest
import os
import csv
import shutil
from io import StringIO
import sys

# Adjust path to import modules from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import appointment_manager
import patient_manager # Needed to create dummy patient data and for its path variables

class TestAppointmentManager(unittest.TestCase):
    TEST_DATA_DIR_APPT = "test_appt_data"
    TEST_DATA_DIR_PATIENT = "test_appt_patient_data" # Separate dir for patient data for these tests

    ORIGINAL_APPT_DATA_DIR = None
    ORIGINAL_APPT_FILE = None
    ORIGINAL_PATIENT_DATA_DIR = None # From patient_manager perspective
    ORIGINAL_PATIENT_FILE_IN_APPT_MGR = None # For appointment_manager.PATIENTS_FILE (path to patient data)
    ORIGINAL_PATIENT_FILE_IN_PATIENT_MGR = None # For patient_manager.PATIENTS_FILE (actual patient data file)

    @classmethod
    def setUpClass(cls):
        # Store original values from appointment_manager
        cls.ORIGINAL_APPT_DATA_DIR = appointment_manager.DATA_DIR
        cls.ORIGINAL_APPT_FILE = appointment_manager.APPOINTMENTS_FILE
        cls.ORIGINAL_PATIENT_FILE_IN_APPT_MGR = appointment_manager.PATIENTS_FILE # This is appointment_manager's path to patients.csv

        # Store original values from patient_manager
        cls.ORIGINAL_PATIENT_DATA_DIR = patient_manager.DATA_DIR # This is patient_manager's DATA_DIR
        cls.ORIGINAL_PATIENT_FILE_IN_PATIENT_MGR = patient_manager.PATIENTS_FILE # This is patient_manager's path to its own patients.csv

    @classmethod
    def tearDownClass(cls):
        # Restore original values
        appointment_manager.DATA_DIR = cls.ORIGINAL_APPT_DATA_DIR
        appointment_manager.APPOINTMENTS_FILE = cls.ORIGINAL_APPT_FILE
        appointment_manager.PATIENTS_FILE = cls.ORIGINAL_PATIENT_FILE_IN_APPT_MGR

        patient_manager.DATA_DIR = cls.ORIGINAL_PATIENT_DATA_DIR
        patient_manager.PATIENTS_FILE = cls.ORIGINAL_PATIENT_FILE_IN_PATIENT_MGR

    def setUp(self):
        # Setup for appointment_manager (where its own CSV files will go)
        appointment_manager.DATA_DIR = self.TEST_DATA_DIR_APPT
        appointment_manager.APPOINTMENTS_FILE = os.path.join(self.TEST_DATA_DIR_APPT, "test_appointments.csv")
        os.makedirs(appointment_manager.DATA_DIR, exist_ok=True)
        if os.path.exists(appointment_manager.APPOINTMENTS_FILE):
            os.remove(appointment_manager.APPOINTMENTS_FILE)

        # Setup for patient data that appointment_manager will reference
        # 1. Configure where appointment_manager will LOOK FOR patient data
        appointment_manager.PATIENTS_FILE = os.path.join(self.TEST_DATA_DIR_PATIENT, "test_patients_for_appt.csv")

        # 2. Configure patient_manager itself to USE this specific directory and file for CREATING dummy patient data
        patient_manager.DATA_DIR = self.TEST_DATA_DIR_PATIENT
        patient_manager.PATIENTS_FILE = appointment_manager.PATIENTS_FILE # Ensure they point to the same file for consistency in this test setup

        os.makedirs(patient_manager.DATA_DIR, exist_ok=True) # Create TEST_DATA_DIR_PATIENT
        if os.path.exists(patient_manager.PATIENTS_FILE): # Clean up any old patient data file
            os.remove(patient_manager.PATIENTS_FILE)

        # Create dummy patient data using patient_manager
        try:
            # patient_manager.add_patient will use its configured PATIENTS_FILE which we've set to the test one
            patient_manager.add_patient("Test Patient One", "1990-01-01", "111-1111") # ID will be 1
            patient_manager.add_patient("Test Patient Two", "1992-02-02", "222-2222") # ID will be 2
        except Exception as e:
            # Fallback for safety, though add_patient should be robust from previous tests.
            # This ensures tests for appointment_manager can run even if add_patient has an unexpected issue.
            print(f"Warning during setUp: Could not add patient using patient_manager.add_patient: {e}. Using fallback.")
            with open(patient_manager.PATIENTS_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['PatientID', 'Name', 'DateOfBirth', 'Contact'])
                writer.writerow(["1", "Test Patient One", "1990-01-01", "111-1111"])
                writer.writerow(["2", "Test Patient Two", "1992-02-02", "222-2222"])


    def tearDown(self):
        # Remove test-specific directories
        if os.path.exists(self.TEST_DATA_DIR_APPT): # appointment_manager.DATA_DIR points here
            shutil.rmtree(self.TEST_DATA_DIR_APPT)
        if os.path.exists(self.TEST_DATA_DIR_PATIENT): # patient_manager.DATA_DIR points here
            shutil.rmtree(self.TEST_DATA_DIR_PATIENT)

    def test_01_generate_appointment_id_empty_file(self):
        self.assertEqual(appointment_manager.generate_appointment_id(), 1)

    def test_02_patient_exists_true(self):
        self.assertTrue(appointment_manager.patient_exists("1"))

    def test_03_patient_exists_false(self):
        self.assertFalse(appointment_manager.patient_exists("99"))

    def test_04_patient_exists_no_patient_file(self):
        # appointment_manager.PATIENTS_FILE points to the specific file for patient data
        if os.path.exists(appointment_manager.PATIENTS_FILE):
            os.remove(appointment_manager.PATIENTS_FILE)
        self.assertFalse(appointment_manager.patient_exists("1"))

    def test_05_schedule_appointment_success(self):
        appointment_manager.schedule_appointment("1", "2024-09-15", "10:00", "Checkup")
        self.assertTrue(os.path.exists(appointment_manager.APPOINTMENTS_FILE))
        with open(appointment_manager.APPOINTMENTS_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ['AppointmentID', 'PatientID', 'Date', 'Time', 'Reason'])
            data = next(reader)
            self.assertEqual(data, ["1", "1", "2024-09-15", "10:00", "Checkup"])
        self.assertEqual(appointment_manager.generate_appointment_id(), 2)

    def test_06_schedule_appointment_patient_not_exists(self):
        with self.assertRaisesRegex(ValueError, "Patient ID '99' not found."): # Adjusted to match actual error
            appointment_manager.schedule_appointment("99", "2024-09-15", "11:00", "Follow-up")

    def test_07_schedule_appointment_invalid_date_format(self):
        # This input ("15-09-2024") is invalid because year is not 4 digits at the start.
        # It will be caught by the specific part length/order check.
        with self.assertRaisesRegex(ValueError, "Invalid date format. Year must be 4 digits, month and day must be 2 digits and all numeric .*"):
            appointment_manager.schedule_appointment("1", "15-09-2024", "12:00", "Consultation")

    def test_07a_schedule_appointment_invalid_date_separator(self):
        # This input ("2024/09/15") is invalid due to wrong separators.
        # It should be caught by the general format check.
        with self.assertRaisesRegex(ValueError, "Invalid date format. Please use YYYY-MM-DD."):
            appointment_manager.schedule_appointment("1", "2024/09/15", "12:30", "Consultation General")


    def test_08_schedule_appointment_empty_reason(self):
        with self.assertRaisesRegex(ValueError, "Reason for appointment cannot be empty."): # Adjusted
            appointment_manager.schedule_appointment("1", "2024-09-15", "13:00", " ") # Whitespace only

    def test_09_list_appointments_no_file(self):
        if os.path.exists(appointment_manager.APPOINTMENTS_FILE):
            os.remove(appointment_manager.APPOINTMENTS_FILE)
        captured_output = StringIO()
        sys.stdout = captured_output
        appointment_manager.list_appointments()
        sys.stdout = sys.__stdout__
        self.assertIn("No appointments found.", captured_output.getvalue())

    def test_10_list_appointments_with_data(self):
        appointment_manager.schedule_appointment("1", "2024-09-15", "10:00", "Checkup")
        appointment_manager.schedule_appointment("2", "2024-09-16", "14:00", "Scan results")

        captured_output = StringIO()
        sys.stdout = captured_output
        appointment_manager.list_appointments()
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        self.assertIn("Appt ID: 1, Patient ID: 1, Date: 2024-09-15, Time: 10:00, Reason: Checkup", output)
        self.assertIn("Appt ID: 2, Patient ID: 2, Date: 2024-09-16, Time: 14:00, Reason: Scan results", output)

if __name__ == '__main__':
    unittest.main()
