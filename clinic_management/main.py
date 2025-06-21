# This file will contain the main CLI logic for the Clinic Management System.
from patient_manager import add_patient, list_patients
from appointment_manager import schedule_appointment, list_appointments

def show_menu():
    """Displays the main menu to the user."""
    print("\nClinic Management System")
    print("1. Add New Patient")
    print("2. Schedule Appointment")
    print("3. List Patients")
    print("4. List Appointments")
    print("5. Exit")

def main():
    """Runs the main command-line interface loop."""
    print("Welcome to the Clinic Management System!")

    while True:
        show_menu()
        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            print("\n--- Add New Patient ---")
            name = input("Enter patient name: ")
            dob = input("Enter patient date of birth (YYYY-MM-DD): ")
            contact = input("Enter patient contact number: ")
            try:
                add_patient(name, dob, contact)
                print("Patient added successfully!")
            except ValueError as e:
                print(f"Error: {e}")
            except Exception as e: # Catch any other unexpected errors from manager
                print(f"An unexpected error occurred: {e}")

        elif choice == '2':
            print("\n--- Schedule Appointment ---")
            patient_id = input("Enter patient ID for the appointment: ")
            date = input("Enter appointment date (YYYY-MM-DD): ")
            time = input("Enter appointment time (HH:MM): ")
            reason = input("Enter reason for appointment: ")
            try:
                schedule_appointment(patient_id, date, time, reason)
                print("Appointment scheduled successfully!")
            except ValueError as e:
                print(f"Error: {e}")
            except Exception as e: # Catch any other unexpected errors from manager
                print(f"An unexpected error occurred: {e}")

        elif choice == '3':
            list_patients()

        elif choice == '4':
            list_appointments()

        elif choice == '5':
            print("Exiting system. Goodbye!")
            break

        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    # The print statements from manager modules are for import confirmation, not part of CLI display.
    # To make the CLI cleaner, those could be removed or put behind a debug flag in a real application.
    main()

# Original print("Clinic Management System - main.py loaded") removed for cleaner CLI output.
# It's clear it's loaded when the menu shows.
