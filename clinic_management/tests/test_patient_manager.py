import unittest
import os
import csv
import shutil
from io import StringIO
import sys

# Adjust path to import modules from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import patient_manager

class TestPatientManager(unittest.TestCase):
    TEST_DATA_DIR = "test_patient_data"
    ORIGINAL_DATA_DIR = None
    ORIGINAL_PATIENTS_FILE = None

    @classmethod
    def setUpClass(cls):
        # Store original values
        cls.ORIGINAL_DATA_DIR = patient_manager.DATA_DIR
        cls.ORIGINAL_PATIENTS_FILE = patient_manager.PATIENTS_FILE

    @classmethod
    def tearDownClass(cls):
        # Restore original values
        patient_manager.DATA_DIR = cls.ORIGINAL_DATA_DIR
        patient_manager.PATIENTS_FILE = cls.ORIGINAL_PATIENTS_FILE

    def setUp(self):
        # Override DATA_DIR and PATIENTS_FILE for tests
        patient_manager.DATA_DIR = self.TEST_DATA_DIR
        patient_manager.PATIENTS_FILE = os.path.join(self.TEST_DATA_DIR, "test_patients.csv")

        os.makedirs(patient_manager.DATA_DIR, exist_ok=True)
        # Ensure the specific test file is clean before each test
        if os.path.exists(patient_manager.PATIENTS_FILE):
            os.remove(patient_manager.PATIENTS_FILE)

    def tearDown(self):
        if os.path.exists(patient_manager.DATA_DIR):
            shutil.rmtree(patient_manager.DATA_DIR)

    def test_01_generate_patient_id_empty_file(self):
        self.assertEqual(patient_manager.generate_patient_id(), 1)

    def test_02_add_patient_success(self):
        patient_manager.add_patient("Test User", "2000-01-01", "123-4567")
        self.assertTrue(os.path.exists(patient_manager.PATIENTS_FILE))
        with open(patient_manager.PATIENTS_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ['PatientID', 'Name', 'DateOfBirth', 'Contact'])
            data = next(reader)
            self.assertEqual(data, ["1", "Test User", "2000-01-01", "123-4567"])
        self.assertEqual(patient_manager.generate_patient_id(), 2) # Next ID should be 2

    def test_03_add_patient_empty_name(self):
        # This test checks for the specific error message for an empty name.
        with self.assertRaisesRegex(ValueError, "Patient name cannot be empty."):
            patient_manager.add_patient("", "2000-01-01", "123-4567")

    def test_03a_add_patient_empty_dob(self):
        with self.assertRaisesRegex(ValueError, "Date of birth cannot be empty."):
            patient_manager.add_patient("Test User", "", "123-4567")

    def test_03b_add_patient_empty_contact(self):
        with self.assertRaisesRegex(ValueError, "Contact information cannot be empty."):
            patient_manager.add_patient("Test User", "2000-01-01", "")

    def test_04_add_patient_invalid_dob_year_format(self): # Renamed for clarity
        # This input ("01-01-2000") is invalid because year is not 4 digits at the start.
        # It will be caught by the specific part length/order check.
        with self.assertRaisesRegex(ValueError, "Invalid DOB format. Year must be 4 digits, month and day must be 2 digits and all numeric .*"):
            patient_manager.add_patient("Test User", "01-01-2000", "123-4567")

    def test_04a_add_patient_invalid_dob_separator_format(self):
        # This input ("2000/01/01") is invalid due to wrong separators.
        # It should be caught by the general format check.
        with self.assertRaisesRegex(ValueError, "Invalid DOB format. Please use YYYY-MM-DD."):
            patient_manager.add_patient("Test User", "2000/01/01", "123-4567")

    def test_05_add_patient_invalid_dob_parts(self):
        with self.assertRaisesRegex(ValueError, "Invalid DOB format. Year must be 4 digits, month and day must be 2 digits and all numeric .*"):
            patient_manager.add_patient("Test User", "2000-1-1", "123-4567")

    def test_06_list_patients_no_file(self):
        # Ensure file doesn't exist for this specific test
        if os.path.exists(patient_manager.PATIENTS_FILE):
            os.remove(patient_manager.PATIENTS_FILE)

        captured_output = StringIO()
        sys.stdout = captured_output
        patient_manager.list_patients()
        sys.stdout = sys.__stdout__  # Reset stdout
        self.assertIn("No patients found.", captured_output.getvalue())

    def test_07_list_patients_empty_file_with_header(self):
        # Create empty file with only header
        os.makedirs(patient_manager.DATA_DIR, exist_ok=True)
        with open(patient_manager.PATIENTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['PatientID', 'Name', 'DateOfBirth', 'Contact'])

        captured_output = StringIO()
        sys.stdout = captured_output
        patient_manager.list_patients()
        sys.stdout = sys.__stdout__
        self.assertIn("No patients found.", captured_output.getvalue())

    def test_08_list_patients_with_data(self):
        patient_manager.add_patient("First User", "1990-03-15", "555-0011")
        patient_manager.add_patient("Second User", "1992-07-20", "555-0022")

        captured_output = StringIO()
        sys.stdout = captured_output
        patient_manager.list_patients()
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        self.assertIn("ID: 1, Name: First User, DOB: 1990-03-15, Contact: 555-0011", output)
        self.assertIn("ID: 2, Name: Second User, DOB: 1992-07-20, Contact: 555-0022", output)

if __name__ == '__main__':
    unittest.main()
