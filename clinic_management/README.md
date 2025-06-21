# Clinic Management System
## Creating an Executable

You can create a standalone executable from this Python application using PyInstaller. This allows you to run the application without needing a Python interpreter installed on the target machine.

### 1. Install PyInstaller

If you don't have PyInstaller installed, you can install it using pip:

```bash
pip install pyinstaller
```

### 2. Build the Executable

Navigate to the `clinic_management` directory in your terminal. Then, run the following command:

```bash
pyinstaller --onefile --name ClinicManagementApp main.py
```

**Explanation of options:**
*   `--onefile`: Packages everything into a single executable file.
*   `--name ClinicManagementApp`: Sets the name of your executable file.
*   `main.py`: This is the entry point of your application.

### 3. Run the Executable

After PyInstaller finishes, you will find a `dist` directory inside your `clinic_management` directory. Your executable, `ClinicManagementApp` (or `ClinicManagementApp.exe` on Windows), will be located in this `dist` directory.

You can run it directly from your terminal:

```bash
./dist/ClinicManagementApp
```
(or `.\dist\ClinicManagementApp.exe` on Windows)

**Note:**
*   The `data` directory (containing `patients.csv` and `appointments.csv`) will still need to be present relative to where you run the executable for it to function correctly, as the application currently reads and writes CSV files to a `data` subdirectory in its current working directory. PyInstaller can bundle data files, but that requires modifications to the `--add-data` flag in the PyInstaller command and potentially code changes to correctly locate these files at runtime. For this basic version, ensure the `data` directory is alongside the executable or in the working directory from which the executable is run.
*   Building executables can sometimes have platform-specific issues. If you encounter problems, refer to the PyInstaller documentation.

## Running Tests

The application includes a suite of unit tests to ensure functionality.

### Setup

The tests are located in the `clinic_management/tests/` directory. They use Python's built-in `unittest` module.

### Running Individual Test Files

You can run tests for a specific manager module directly from the project's root directory (`/app` if in the standard development environment for this project, or the directory containing the `clinic_management` folder):

```bash
python -m unittest clinic_management/tests/test_patient_manager.py
python -m unittest clinic_management/tests/test_appointment_manager.py
```

### Running All Tests (Test Discovery)

To run all tests in the `clinic_management/tests` directory using test discovery (from the project's root directory):

```bash
python -m unittest discover clinic_management/tests/
```
Or, if you are in the `clinic_management` directory:
```bash
python -m unittest discover tests/
```

This will automatically find and run all files matching the `test*.py` pattern within the specified directory.

**Note:**
*   The tests create their own temporary data files (e.g., in `test_patient_data/` and `test_appt_data/`) and clean them up afterwards. They are designed to not interfere with the main `data/` directory used by the application.
*   The "Clinic Management System - patient_manager.py loaded" and "Clinic Management System - appointment_manager.py loaded" messages will appear at the start of the test output. This is due to the print statements at the end of those modules, confirming they are imported by the test files. These could be removed or made conditional for cleaner test output in a production setting.
