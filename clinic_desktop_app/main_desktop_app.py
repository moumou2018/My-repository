import tkinter as tk
from tkinter import ttk, messagebox, simpledialog # simpledialog not used currently but often useful
import requests # For making HTTP requests to the backend API
import json # For parsing JSON responses
from datetime import datetime # For handling and formatting dates and times

# --- Configuration ---
# Base URL for the backend API
BACKEND_API_URL = "http://127.0.0.1:5000/api"
# Default timeout for API requests in seconds
REQUEST_TIMEOUT = 10

# --- Login Dialog ---
class LoginDialog(tk.Toplevel):
    """Modal dialog for user login."""
    def __init__(self, parent, title="Login"):
        super().__init__(parent)
        self.transient(parent) # Make dialog transient to the parent window
        self.title(title)
        self.parent = parent
        self.result = None # Stores the authentication token if login is successful

        self.geometry("300x150")
        self.resizable(False, False) # Prevent resizing
        self.protocol("WM_DELETE_WINDOW", self._on_close) # Handle window close (X) button

        form_frame = ttk.Frame(self, padding="15")
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Username field
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(form_frame, width=25)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.username_entry.focus_set() # Set initial focus to username

        # Password field
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.password_entry = ttk.Entry(form_frame, width=25, show="*") # Show '*' for password
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        # Buttons frame
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.login_button = ttk.Button(btn_frame, text="Login", command=self._on_login)
        self.login_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(btn_frame, text="Cancel", command=self._on_close)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.bind("<Return>", self._on_login) # Allow login by pressing Enter

        self.grab_set() # Make the dialog modal (blocks interaction with parent)
        self.wait_window() # Wait until the dialog is destroyed

    def _on_login(self, event=None):
        """Handles the login attempt when the Login button or Enter key is pressed."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Login Failed", "Username and password are required.", parent=self)
            return

        try:
            # Make a POST request to the backend /api/login endpoint
            response = requests.post(
                f"{BACKEND_API_URL}/login",
                json={"username": username, "password": password},
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status() # Raise an HTTPError for bad status codes (4xx or 5xx)

            data = response.json()
            if data.get("token"):
                self.result = data["token"] # Store the received token
                self.destroy() # Close the login dialog
            else:
                # Should ideally not happen if backend guarantees token on 200 OK
                messagebox.showerror("Login Failed", data.get("message", "No token received from server."), parent=self)

        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors (e.g., 401 Unauthorized, 400 Bad Request)
            try:
                error_data = e.response.json() # Try to parse JSON error message from backend
                msg = error_data.get("message", str(e))
            except (json.JSONDecodeError, AttributeError): # Fallback if no JSON error message
                msg = str(e)
            messagebox.showerror("Login Failed", f"API Error: {msg}", parent=self)
        except requests.exceptions.RequestException as e:
            # Handle other request errors (e.g., connection refused)
            messagebox.showerror("Login Failed", f"Connection Error: {e}", parent=self)
        except json.JSONDecodeError:
             # Handle cases where server response is not valid JSON
             messagebox.showerror("Login Failed", "Invalid response received from server.", parent=self)

    def _on_close(self):
        """Handles closing the dialog via Cancel button or window X button."""
        self.result = None # Ensure no token is returned
        self.destroy()

# --- Main Application ---
class ClinicApp:
    """Main class for the Clinic Management Tkinter application."""
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # Hide the main window until login is successful
        self.auth_token = None # Stores the authentication token after successful login

        # Attempt login process
        if not self.attempt_login():
            self.root.destroy() # If login fails or is cancelled, destroy root window and exit
            return

        # If login is successful, show the main window and set up the UI
        self.root.deiconify()
        self.setup_main_ui()

    def attempt_login(self):
        """Manages the login process by displaying the LoginDialog."""
        login_dialog = LoginDialog(self.root) # Parent is the (hidden) root window
        if login_dialog.result: # Check if LoginDialog returned a token
            self.auth_token = login_dialog.result
            # Show info relative to root, parent=None if root is already destroyed (should not happen here)
            messagebox.showinfo("Login Successful", "Welcome!", parent=self.root if self.root.winfo_exists() else None)
            return True
        else:
            # If login dialog was closed or login failed
            if self.root.winfo_exists(): # Check if root still exists before showing final error
                 messagebox.showerror("Login Required", "Login failed or was cancelled. Application will exit.", parent=self.root if self.root.winfo_exists() else None)
            return False

    def setup_main_ui(self):
        """Sets up the main user interface of the application after successful login."""
        self.root.title("Clinic Management System")
        self.root.geometry("1200x800") # Set initial size of the main window

        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use('clam') # Using a modern theme for ttk widgets
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.style.configure("Bold.TLabel", font=("Arial", 10, "bold")) # Custom style for bold labels

        # Main frame to hold navigation and content areas
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Navigation panel (left side)
        nav_frame = ttk.Frame(main_frame, relief="solid", borderwidth=1)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)

        ttk.Label(nav_frame, text="Menu", font=("Arial", 16, "bold")).pack(pady=10, padx=10)
        # Navigation buttons
        self.btn_patients = ttk.Button(nav_frame, text="Patients", command=self.show_patient_view, width=15)
        self.btn_patients.pack(pady=5, padx=10, fill=tk.X)
        self.btn_appointments = ttk.Button(nav_frame, text="Appointments", command=self.show_appointment_view, width=15)
        self.btn_appointments.pack(pady=5, padx=10, fill=tk.X)

        # Content display area (right side)
        self.content_frame = ttk.Frame(main_frame, padding="10")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Placeholders for different view frames and treeviews
        self.patient_view_frame = None
        self.appointment_view_frame = None
        self.patient_tree = None
        self.appointment_tree = None
        self.medical_notes_tree = None

        # Data caches and state variables
        self.patients_list_for_appointments = [] # Cache for patient names/IDs for appointment forms
        self.current_selected_patient_id = None # ID of the currently selected patient in the patient view
        self.appointments_for_selected_patient = [] # Cache for appointments of the selected patient (for linking notes)

        self.show_welcome_message() # Display initial welcome message

    def clear_content_frame(self):
        """Clears all widgets from the content_frame and resets view-specific variables."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        # Reset references to view-specific frames and treeviews
        self.patient_view_frame = self.appointment_view_frame = None
        self.patient_tree = self.appointment_tree = self.medical_notes_tree = None
        self.current_selected_patient_id = None
        self.appointments_for_selected_patient = []

    def show_welcome_message(self):
        """Displays a welcome message in the content_frame."""
        self.clear_content_frame()
        ttk.Label(self.content_frame, text="Welcome!", font=("Arial", 18, "bold")).pack(pady=20)
        ttk.Label(self.content_frame, text="Select a module from the left menu.", font=("Arial", 12)).pack()

    # --- Patient Management UI ---
    def show_patient_view(self):
        """Displays the patient management view, including patient list and medical notes for selected patient."""
        self.clear_content_frame()
        # Use a PanedWindow to allow resizing of patient list and notes sections
        self.patient_view_frame = ttk.PanedWindow(self.content_frame, orient=tk.VERTICAL)
        self.patient_view_frame.pack(fill=tk.BOTH, expand=True)

        # Top pane for patient list and CRUD controls
        top_pane = ttk.Frame(self.patient_view_frame, padding=5)
        self.patient_view_frame.add(top_pane, weight=2) # Give more initial space to patient list

        ttk.Label(top_pane, text="Patient Management", font=("Arial", 16, "bold")).pack(pady=(0,10))
        patient_btn_frame = ttk.Frame(top_pane); patient_btn_frame.pack(fill=tk.X, pady=5)
        # Patient CRUD buttons
        ttk.Button(patient_btn_frame, text="Add Patient", command=self.add_patient_dialog).pack(side=tk.LEFT, padx=5)
        self.edit_patient_btn = ttk.Button(patient_btn_frame, text="Edit Patient", command=self.edit_patient_dialog, state=tk.DISABLED); self.edit_patient_btn.pack(side=tk.LEFT, padx=5)
        self.delete_patient_btn = ttk.Button(patient_btn_frame, text="Delete Patient", command=self.delete_patient, state=tk.DISABLED); self.delete_patient_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(patient_btn_frame, text="Refresh List", command=self.load_patients).pack(side=tk.LEFT, padx=5)

        # Treeview for displaying patients
        columns = ("id", "name", "dob", "phone", "history")
        self.patient_tree = ttk.Treeview(top_pane, columns=columns, show="headings", selectmode="browse")
        # Configure patient tree columns
        for col, width in [("id", 50), ("name", 200), ("dob", 100), ("phone", 120), ("history", 400)]:
            self.patient_tree.heading(col, text=col.replace("_", " ").title())
            self.patient_tree.column(col, width=width, anchor=(tk.CENTER if col in ["id", "dob"] else tk.W))
        self.patient_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        self.patient_tree.bind("<<TreeviewSelect>>", self.on_patient_select_for_notes) # Event binding for selection

        # Bottom pane for medical notes of the selected patient
        bottom_pane = ttk.Frame(self.patient_view_frame, padding=5)
        self.patient_view_frame.add(bottom_pane, weight=1)

        ttk.Label(bottom_pane, text="Medical Notes", font=("Arial", 14, "bold")).pack(pady=(10,5))
        notes_btn_frame = ttk.Frame(bottom_pane); notes_btn_frame.pack(fill=tk.X, pady=5)
        # Medical Notes CRUD buttons
        self.add_note_btn = ttk.Button(notes_btn_frame, text="Add Note", command=self.add_medical_note_dialog, state=tk.DISABLED); self.add_note_btn.pack(side=tk.LEFT, padx=5)
        self.edit_note_btn = ttk.Button(notes_btn_frame, text="View/Edit Note", command=self.edit_medical_note_dialog, state=tk.DISABLED); self.edit_note_btn.pack(side=tk.LEFT, padx=5)
        self.delete_note_btn = ttk.Button(notes_btn_frame, text="Delete Note", command=self.delete_medical_note, state=tk.DISABLED); self.delete_note_btn.pack(side=tk.LEFT, padx=5)

        # Treeview for displaying medical notes
        note_columns = ("id", "date", "doctor", "appt_id", "notes_preview", "diagnosis")
        self.medical_notes_tree = ttk.Treeview(bottom_pane, columns=note_columns, show="headings", selectmode="browse")
        # Configure medical notes tree columns
        note_col_map = {"id": "ID", "date": "Date", "doctor": "Doctor", "appt_id": "Appt ID", "notes_preview": "Notes Preview", "diagnosis": "Diagnosis"}
        note_col_widths = {"id": 40, "date": 120, "doctor": 150, "appt_id":60, "notes_preview": 300, "diagnosis": 200}
        for col_key in note_columns:
            self.medical_notes_tree.heading(col_key, text=note_col_map[col_key])
            self.medical_notes_tree.column(col_key, width=note_col_widths[col_key], anchor=tk.W)
        self.medical_notes_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        self.medical_notes_tree.bind("<<TreeviewSelect>>", self.on_medical_note_select) # Event binding

        self.load_patients() # Load initial patient list

    def on_patient_select_for_notes(self, event=None):
        """Handles selection of a patient in the patient_tree.
        Updates related UI elements and loads medical notes for the selected patient."""
        self.on_patient_select(event) # Call the general patient selection handler for edit/delete buttons

        selected_item = self.patient_tree.focus() if hasattr(self, 'patient_tree') and self.patient_tree else None
        if selected_item:
            self.current_selected_patient_id = self.patient_tree.item(selected_item)['values'][0]
            if hasattr(self, 'add_note_btn'): self.add_note_btn.config(state=tk.NORMAL)
            self.load_medical_notes_for_patient()
            self.fetch_appointments_for_selected_patient() # For linking notes
        else:
            self.current_selected_patient_id = None
            if hasattr(self, 'add_note_btn'): self.add_note_btn.config(state=tk.DISABLED)
            # Clear notes tree if no patient is selected
            if hasattr(self, 'medical_notes_tree') and self.medical_notes_tree:
                for item in self.medical_notes_tree.get_children(): self.medical_notes_tree.delete(item)
            self.appointments_for_selected_patient = []
        self.on_medical_note_select() # Update medical note button states

    def on_patient_select(self, event=None):
        """General handler for patient selection, enables/disables patient Edit/Delete buttons."""
        # Check if patient_tree exists and an item is focused (selected)
        if hasattr(self, 'patient_tree') and self.patient_tree and self.patient_tree.focus():
            if hasattr(self, 'edit_patient_btn'): self.edit_patient_btn.config(state=tk.NORMAL)
            if hasattr(self, 'delete_patient_btn'): self.delete_patient_btn.config(state=tk.NORMAL)
        else:
            if hasattr(self, 'edit_patient_btn'): self.edit_patient_btn.config(state=tk.DISABLED)
            if hasattr(self, 'delete_patient_btn'): self.delete_patient_btn.config(state=tk.DISABLED)

    def load_patients(self):
        """Loads patients from the backend and populates the patient_tree."""
        if not hasattr(self, 'patient_tree') or not self.patient_tree: return # Ensure treeview exists
        # Clear existing patient entries
        for item in self.patient_tree.get_children(): self.patient_tree.delete(item)

        data = self.api_get("patients") # Fetch patients via API
        if data and isinstance(data, list): # Check if data is a list (successful response)
            for patient in data:
                self.patient_tree.insert("", tk.END, values=(
                    patient.get('id'), patient.get('name'),
                    patient.get('date_of_birth', 'N/A'), patient.get('phone_number', 'N/A'),
                    patient.get('medical_history_summary', 'N/A')
                ))
        elif data and isinstance(data, dict) and 'message' in data and data.get('status_code', 200) >=400 :
             pass # Error message already shown by _handle_api_response
        self.on_patient_select_for_notes() # Update UI based on current (de)selection

    def add_patient_dialog(self):
        """Opens a dialog to add a new patient."""
        self.patient_form_dialog(title="Add New Patient")

    def edit_patient_dialog(self):
        """Opens a dialog to edit the selected patient."""
        if not hasattr(self, 'patient_tree') or not self.patient_tree: return
        selected_item_id = self.patient_tree.focus()
        if not selected_item_id:
            return messagebox.showwarning("Selection Error", "Please select a patient to edit.", parent=self.root)

        patient_id = self.patient_tree.item(selected_item_id)['values'][0]
        patient_details = self.api_get(f"patients/{patient_id}") # Fetch full details for editing
        # Check if fetch was successful before opening dialog
        if patient_details and not (isinstance(patient_details, dict) and 'message' in patient_details and patient_details.get('status_code', 200) >=400) :
             self.patient_form_dialog(title=f"Edit Patient ID: {patient_id}", patient_data=patient_details)

    def patient_form_dialog(self, title, patient_data=None):
        """Dialog for adding or editing patient information."""
        # Create a Toplevel window for the form
        dialog = tk.Toplevel(self.root); dialog.title(title); dialog.geometry("450x400")
        dialog.resizable(False, False); dialog.transient(self.root); dialog.grab_set()

        form_frame = ttk.Frame(dialog, padding="15"); form_frame.pack(fill=tk.BOTH, expand=True)

        # Define form fields and create corresponding entry widgets
        fields = {"Name:": "name", "Date of Birth (YYYY-MM-DD):": "date_of_birth", "Phone Number:": "phone_number"}
        entries = {} # To store entry widgets for easy access
        for i, (label_text, field_key) in enumerate(fields.items()):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
            if patient_data: entry.insert(0, patient_data.get(field_key, '')) # Populate if editing
            entries[field_key] = entry

        # Medical History (Text widget)
        ttk.Label(form_frame, text="Medical History:").grid(row=len(fields), column=0, padx=5, pady=5, sticky=tk.NW)
        history_text = tk.Text(form_frame, width=30, height=5, relief=tk.SOLID, borderwidth=1)
        history_text.grid(row=len(fields), column=1, padx=5, pady=5, sticky=tk.EW)
        # Add scrollbar to Text widget
        history_scrollbar = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=history_text.yview)
        history_scrollbar.grid(row=len(fields), column=2, sticky='nsw', pady=5)
        history_text['yscrollcommand'] = history_scrollbar.set
        if patient_data: history_text.insert(tk.END, patient_data.get('medical_history_summary', ''))
        entries['medical_history_summary'] = history_text

        def on_submit():
            """Handles submission of the patient form."""
            # Collect data from form fields
            payload = {k: (v.get("1.0", tk.END).strip() if isinstance(v, tk.Text) else v.get()) for k, v in entries.items()}
            if not payload["name"]: # Basic validation
                return messagebox.showerror("Validation Error", "Name is required.", parent=dialog)

            # Determine API call based on whether it's an add or edit operation
            if patient_data:
                response = self.api_put(f"patients/{patient_data['id']}", payload)
            else:
                response = self.api_post("patients", payload)

            # If API call was successful (and not an error dict from _handle_api_response)
            if response and not (isinstance(response, dict) and 'message' in response and response.get('status_code', 200) >= 400):
                messagebox.showinfo("Success", f"Patient {('updated' if patient_data else 'added')} successfully!", parent=dialog)
                self.load_patients() # Refresh patient list
                dialog.destroy() # Close form dialog

        submit_button = ttk.Button(form_frame, text="Save", command=on_submit)
        submit_button.grid(row=len(fields)+1, column=0, columnspan=3, pady=10) # Ensure button spans correctly
        form_frame.columnconfigure(1, weight=1) # Allow entry column to expand
        dialog.wait_window() # Wait for dialog to be closed

    def delete_patient(self):
        """Handles deletion of the selected patient after confirmation."""
        if not hasattr(self, 'patient_tree') or not self.patient_tree: return
        selected_item_id = self.patient_tree.focus()
        if not selected_item_id:
            return messagebox.showwarning("Selection Error", "Please select a patient to delete.", parent=self.root)

        values = self.patient_tree.item(selected_item_id)['values']
        patient_id, patient_name = values[0], values[1]

        # Confirmation dialog
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete patient {patient_name} (ID: {patient_id})?", parent=self.root):
            response = self.api_delete(f"patients/{patient_id}")
            if response and not (isinstance(response, dict) and 'message' in response and response.get('status_code', 200) >=400):
                 messagebox.showinfo("Success", f"Patient {patient_name} deleted successfully.", parent=self.root)
                 self.load_patients() # Refresh list

    # --- Medical Notes UI (within Patient View) ---
    def load_medical_notes_for_patient(self):
        """Loads and displays medical notes for the currently selected patient."""
        # Ensure treeview exists and a patient is selected
        if not hasattr(self, 'medical_notes_tree') or not self.medical_notes_tree or not self.current_selected_patient_id:
            if hasattr(self, 'medical_notes_tree') and self.medical_notes_tree:
                 for item in self.medical_notes_tree.get_children(): self.medical_notes_tree.delete(item) # Clear if no patient
            return

        for item in self.medical_notes_tree.get_children(): self.medical_notes_tree.delete(item) # Clear existing notes

        notes_data = self.api_get(f"patients/{self.current_selected_patient_id}/medical_notes")
        if notes_data and isinstance(notes_data, list):
            for note in notes_data:
                dt_str = note.get('record_date', '')
                if dt_str: # Format date for display
                    try: dt_obj = datetime.fromisoformat(dt_str); dt_str = dt_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError: dt_str = note.get('record_date', 'Invalid Date')

                # Create a short preview for notes
                notes_preview = note.get('notes', '')
                if len(notes_preview) > 50: notes_preview = notes_preview[:50] + "..."

                self.medical_notes_tree.insert("", tk.END, values=(
                    note.get('id'), dt_str, note.get('doctor_name', 'N/A'),
                    note.get('appointment_id', 'N/A'), notes_preview, note.get('diagnosis', 'N/A')
                ))
        elif notes_data and isinstance(notes_data, dict) and 'message' in notes_data and notes_data.get('status_code', 200) >=400:
            pass # Error handled by API helpers
        self.on_medical_note_select() # Update button states for notes

    def fetch_appointments_for_selected_patient(self):
        """Fetches appointments for the currently selected patient to populate 'Link to Appointment' combobox."""
        self.appointments_for_selected_patient = []
        if not self.current_selected_patient_id: return

        # TODO: Ideally, backend should provide an endpoint like /api/patients/<id>/appointments
        # For now, fetching all and filtering client-side.
        all_appointments_data = self.api_get("appointments")
        if all_appointments_data and isinstance(all_appointments_data, list):
            self.appointments_for_selected_patient = [
                appt for appt in all_appointments_data if appt.get('patient_id') == self.current_selected_patient_id
            ]

    def on_medical_note_select(self, event=None):
        """Handles selection of a medical note, enabling/disabling relevant buttons."""
        if hasattr(self, 'medical_notes_tree') and self.medical_notes_tree and self.medical_notes_tree.focus():
            if hasattr(self, 'edit_note_btn'): self.edit_note_btn.config(state=tk.NORMAL)
            if hasattr(self, 'delete_note_btn'): self.delete_note_btn.config(state=tk.NORMAL)
        else:
            if hasattr(self, 'edit_note_btn'): self.edit_note_btn.config(state=tk.DISABLED)
            if hasattr(self, 'delete_note_btn'): self.delete_note_btn.config(state=tk.DISABLED)

    def add_medical_note_dialog(self):
        """Opens a dialog to add a new medical note for the selected patient."""
        if not self.current_selected_patient_id:
            return messagebox.showerror("Error", "No patient selected to add a note for.", parent=self.root)
        self.medical_note_form_dialog(title="Add Medical Note")

    def edit_medical_note_dialog(self):
        """Opens a dialog to view/edit the selected medical note."""
        if not hasattr(self, 'medical_notes_tree') or not self.medical_notes_tree: return
        selected_item_id = self.medical_notes_tree.focus()
        if not selected_item_id:
            return messagebox.showwarning("Selection Error", "Please select a medical note to view/edit.", parent=self.root)

        note_id = self.medical_notes_tree.item(selected_item_id)['values'][0]
        note_details = self.api_get(f"medical_notes/{note_id}") # Fetch full note details

        if note_details and not (isinstance(note_details, dict) and 'message' in note_details and note_details.get('status_code',200)>=400):
            self.medical_note_form_dialog(title=f"View/Edit Medical Note ID: {note_id}", note_data=note_details)

    def medical_note_form_dialog(self, title, note_data=None):
        """Dialog for adding or editing a medical note."""
        dialog = tk.Toplevel(self.root); dialog.title(title); dialog.geometry("600x550")
        dialog.resizable(False, False); dialog.transient(self.root); dialog.grab_set()
        form_frame = ttk.Frame(dialog, padding="15"); form_frame.pack(fill=tk.BOTH, expand=True)

        entries = {}; row_idx = 0 # Store form entry widgets

        # Doctor Name
        ttk.Label(form_frame, text="Doctor Name:").grid(row=row_idx, column=0, padx=5, pady=5, sticky=tk.W)
        entries['doctor_name'] = ttk.Entry(form_frame, width=50)
        entries['doctor_name'].grid(row=row_idx, column=1, padx=5, pady=5, sticky=tk.EW); row_idx+=1

        # Record Date (defaults to now for new notes)
        ttk.Label(form_frame, text="Record Date (YYYY-MM-DD HH:MM):").grid(row=row_idx, column=0, padx=5, pady=5, sticky=tk.W)
        entries['record_date'] = ttk.Entry(form_frame, width=50)
        entries['record_date'].grid(row=row_idx, column=1, padx=5, pady=5, sticky=tk.EW); row_idx+=1
        if not note_data: # Default for new notes
            entries['record_date'].insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Link to Appointment (Combobox)
        ttk.Label(form_frame, text="Link to Appointment:").grid(row=row_idx, column=0, padx=5, pady=5, sticky=tk.W)
        # Create display strings for appointments, including "None" option
        appt_display_list = ["None"] + [
            f"ID: {a['id']} - {datetime.fromisoformat(a['appointment_datetime']).strftime('%Y-%m-%d %H:%M') if a.get('appointment_datetime') else 'No Date'}"
            for a in self.appointments_for_selected_patient
        ]
        entries['appointment_id_combo'] = ttk.Combobox(form_frame, values=appt_display_list, state="readonly", width=47)
        entries['appointment_id_combo'].grid(row=row_idx, column=1, padx=5, pady=5, sticky=tk.EW); row_idx+=1
        entries['appointment_id_combo'].set("None") # Default to "None"

        # Notes (Text widget with scrollbar)
        ttk.Label(form_frame, text="Notes:").grid(row=row_idx, column=0, padx=5, pady=5, sticky=tk.NW)
        entries['notes'] = tk.Text(form_frame, width=40, height=8, relief=tk.SOLID, borderwidth=1)
        entries['notes'].grid(row=row_idx, column=1, padx=5, pady=5, sticky=tk.EW)
        notes_scrollbar = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=entries['notes'].yview)
        notes_scrollbar.grid(row=row_idx, column=2, sticky='nsw', pady=5); entries['notes']['yscrollcommand'] = notes_scrollbar.set; row_idx+=1

        # Diagnosis (Text widget with scrollbar)
        ttk.Label(form_frame, text="Diagnosis:").grid(row=row_idx, column=0, padx=5, pady=5, sticky=tk.W) # Changed to Text from Entry
        entries['diagnosis'] = tk.Text(form_frame, width=40, height=3, relief=tk.SOLID, borderwidth=1)
        entries['diagnosis'].grid(row=row_idx, column=1, padx=5, pady=5, sticky=tk.EW)
        diag_scrollbar = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=entries['diagnosis'].yview)
        diag_scrollbar.grid(row=row_idx, column=2, sticky='nsw', pady=5); entries['diagnosis']['yscrollcommand'] = diag_scrollbar.set; row_idx+=1

        # Prescribed Medication (Text widget with scrollbar)
        ttk.Label(form_frame, text="Prescribed Medication:").grid(row=row_idx, column=0, padx=5, pady=5, sticky=tk.W)
        entries['prescribed_medication'] = tk.Text(form_frame, width=40, height=3, relief=tk.SOLID, borderwidth=1)
        entries['prescribed_medication'].grid(row=row_idx, column=1, padx=5, pady=5, sticky=tk.EW)
        med_scrollbar = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=entries['prescribed_medication'].yview)
        med_scrollbar.grid(row=row_idx, column=2, sticky='nsw', pady=5); entries['prescribed_medication']['yscrollcommand'] = med_scrollbar.set; row_idx+=1

        # Populate form if editing existing note_data
        if note_data:
            entries['doctor_name'].insert(0, note_data.get('doctor_name', ''))
            rec_date_iso = note_data.get('record_date')
            if rec_date_iso:
                try: entries['record_date'].insert(0, datetime.fromisoformat(rec_date_iso).strftime("%Y-%m-%d %H:%M"))
                except ValueError: pass # Keep blank if format is wrong

            linked_appt_id = note_data.get('appointment_id')
            if linked_appt_id: # Try to select the linked appointment in combobox
                for appt_str_val in appt_display_list:
                    if f"ID: {linked_appt_id}" in appt_str_val:
                        entries['appointment_id_combo'].set(appt_str_val)
                        break

            entries['notes'].insert(tk.END, note_data.get('notes', ''))
            entries['diagnosis'].insert(tk.END, note_data.get('diagnosis', '')) # Use insert for Text
            entries['prescribed_medication'].insert(tk.END, note_data.get('prescribed_medication', '')) # Use insert for Text

        def on_submit():
            """Handles submission of the medical note form."""
            payload = { # Collect data from form fields
                "doctor_name": entries['doctor_name'].get(),
                "notes": entries['notes'].get("1.0", tk.END).strip(), # Get all text from Text widget
                "diagnosis": entries['diagnosis'].get("1.0", tk.END).strip(),
                "prescribed_medication": entries['prescribed_medication'].get("1.0", tk.END).strip()
            }
            if not payload["notes"]: # Basic validation
                return messagebox.showerror("Validation Error", "Notes content is required.", parent=dialog)

            record_date_str = entries['record_date'].get()
            if record_date_str: # If date is provided, parse and convert to ISO format
                try:
                    payload['record_date'] = datetime.strptime(record_date_str, "%Y-%m-%d %H:%M").isoformat()
                except ValueError:
                    return messagebox.showerror("Validation Error", "Invalid Record Date format. Use YYYY-MM-DD HH:MM or leave blank for current time.", parent=dialog)

            # Get appointment_id from combobox selection
            selected_appt_str_val = entries['appointment_id_combo'].get()
            if selected_appt_str_val and selected_appt_str_val != "None":
                try:
                    # Extract ID from "ID: NNN - ..." string
                    payload['appointment_id'] = int(selected_appt_str_val.split("ID: ")[1].split(" - ")[0])
                except (IndexError, ValueError):
                    messagebox.showwarning("Warning", "Could not parse selected appointment ID. Note will not be linked.", parent=dialog)

            # API call for add or edit
            if note_data:
                response = self.api_put(f"medical_notes/{note_data['id']}", payload)
            else:
                response = self.api_post(f"patients/{self.current_selected_patient_id}/medical_notes", payload)

            if response and not (isinstance(response, dict) and 'message' in response and response.get('status_code', 200) >= 400):
                messagebox.showinfo("Success", f"Medical note {('updated' if note_data else 'added')} successfully!", parent=dialog)
                self.load_medical_notes_for_patient() # Refresh notes list
                dialog.destroy()

        submit_button = ttk.Button(form_frame, text="Save Note", command=on_submit)
        submit_button.grid(row=row_idx, column=0, columnspan=3, pady=10) # Span correctly
        form_frame.columnconfigure(1, weight=1) # Allow entry column to expand
        dialog.wait_window()

    def delete_medical_note(self):
        """Handles deletion of the selected medical note after confirmation."""
        if not hasattr(self, 'medical_notes_tree') or not self.medical_notes_tree: return
        selected_item_id = self.medical_notes_tree.focus()
        if not selected_item_id:
            return messagebox.showwarning("Selection Error", "Please select a medical note to delete.", parent=self.root)

        note_id = self.medical_notes_tree.item(selected_item_id)['values'][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete medical note ID {note_id}?", parent=self.root):
            response = self.api_delete(f"medical_notes/{note_id}")
            if response and not (isinstance(response, dict) and 'message' in response and response.get('status_code',200)>=400):
                 messagebox.showinfo("Success", f"Medical note ID {note_id} deleted successfully.", parent=self.root)
                 self.load_medical_notes_for_patient() # Refresh list

    # --- Appointment Scheduling UI (Summary - full implementation in previous steps) ---
    def show_appointment_view(self):
        """Displays the appointment scheduling view."""
        self.clear_content_frame()
        self.appointment_view_frame = ttk.Frame(self.content_frame)
        self.appointment_view_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.appointment_view_frame, text="Appointment Scheduling", font=("Arial", 16, "bold")).pack(pady=(0,10))

        btn_frame = ttk.Frame(self.appointment_view_frame); btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add Appointment", command=self.add_appointment_dialog).pack(side=tk.LEFT, padx=5)
        self.edit_appointment_btn = ttk.Button(btn_frame, text="Edit Appointment", command=self.edit_appointment_dialog, state=tk.DISABLED); self.edit_appointment_btn.pack(side=tk.LEFT, padx=5)
        self.delete_appointment_btn = ttk.Button(btn_frame, text="Delete Appointment", command=self.delete_appointment, state=tk.DISABLED); self.delete_appointment_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh List", command=self.load_appointments).pack(side=tk.LEFT, padx=5)

        columns = ("id", "patient_name", "doctor_name", "datetime", "reason", "status")
        self.appointment_tree = ttk.Treeview(self.appointment_view_frame, columns=columns, show="headings", selectmode="browse")
        col_map = {"id": "ID", "patient_name": "Patient", "doctor_name": "Doctor", "datetime": "Date/Time", "reason": "Reason", "status": "Status"}
        col_widths = {"id": 50, "patient_name": 150, "doctor_name": 150, "datetime": 150, "reason": 250, "status": 100}
        for col_key in columns:
            self.appointment_tree.heading(col_key, text=col_map[col_key])
            self.appointment_tree.column(col_key, width=col_widths[col_key], anchor=(tk.CENTER if col_key in ["id", "status"] else tk.W))
        self.appointment_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        self.appointment_tree.bind("<<TreeviewSelect>>", self.on_appointment_select)

        self.fetch_patients_for_appointments() # Load patient list for comboboxes
        self.load_appointments() # Load initial appointment list

    def fetch_patients_for_appointments(self):
        """Fetches all patients to populate comboboxes in appointment forms."""
        data = self.api_get("patients")
        if data and isinstance(data, list):
            self.patients_list_for_appointments = [{"id": p['id'], "name": p['name']} for p in data]
        else:
            self.patients_list_for_appointments = [] # Reset or handle error

    def on_appointment_select(self, event=None):
        """Handles selection of an appointment, enabling/disabling relevant buttons."""
        if hasattr(self, 'appointment_tree') and self.appointment_tree and self.appointment_tree.focus():
            if hasattr(self, 'edit_appointment_btn'): self.edit_appointment_btn.config(state=tk.NORMAL)
            if hasattr(self, 'delete_appointment_btn'): self.delete_appointment_btn.config(state=tk.NORMAL)
        else:
            if hasattr(self, 'edit_appointment_btn'): self.edit_appointment_btn.config(state=tk.DISABLED)
            if hasattr(self, 'delete_appointment_btn'): self.delete_appointment_btn.config(state=tk.DISABLED)

    def load_appointments(self):
        """Loads appointments from backend and populates the appointment_tree."""
        if not hasattr(self, 'appointment_tree') or not self.appointment_tree: return
        for item in self.appointment_tree.get_children(): self.appointment_tree.delete(item)

        data = self.api_get("appointments")
        if data and isinstance(data, list):
            for appt in data:
                dt_str = appt.get('appointment_datetime', '')
                if dt_str: # Format datetime for display
                    try:
                        dt_obj = datetime.fromisoformat(dt_str)
                        dt_str = dt_obj.strftime("%Y-%m-%d %I:%M %p") # e.g., 2023-10-26 02:30 PM
                    except ValueError:
                        dt_str = appt.get('appointment_datetime', 'Invalid Date')
                self.appointment_tree.insert("", tk.END, values=(
                    appt.get('id'), appt.get('patient_name', 'N/A'),
                    appt.get('doctor_name', 'N/A'), dt_str,
                    appt.get('reason_for_visit', 'N/A'), appt.get('status', 'N/A')
                ))
        elif data and isinstance(data, dict) and 'message' in data and data.get('status_code', 200) >=400:
            pass # Error handled by API helpers
        self.on_appointment_select()

    def add_appointment_dialog(self):
        """Opens a dialog to add a new appointment."""
        if not self.patients_list_for_appointments: self.fetch_patients_for_appointments() # Ensure patient list is loaded
        if not self.patients_list_for_appointments:
            return messagebox.showwarning("Data Missing", "Patient list could not be loaded. Please add patients or check API connection.", parent=self.root)
        self.appointment_form_dialog(title="Add New Appointment")

    def edit_appointment_dialog(self):
        """Opens a dialog to edit the selected appointment."""
        if not hasattr(self, 'appointment_tree') or not self.appointment_tree: return
        selected_item_id = self.appointment_tree.focus()
        if not selected_item_id:
            return messagebox.showwarning("Selection Error", "Please select an appointment to edit.", parent=self.root)

        appt_id = self.appointment_tree.item(selected_item_id)['values'][0]
        appt_details = self.api_get(f"appointments/{appt_id}")

        if appt_details and not (isinstance(appt_details, dict) and 'message' in appt_details and appt_details.get('status_code',200)>=400):
            if not self.patients_list_for_appointments: self.fetch_patients_for_appointments() # Ensure patients loaded for form
            self.appointment_form_dialog(title=f"Edit Appointment ID: {appt_id}", appointment_data=appt_details)

    def appointment_form_dialog(self, title, appointment_data=None):
        """Dialog for adding or editing appointment information."""
        dialog = tk.Toplevel(self.root); dialog.title(title); dialog.geometry("500x450")
        dialog.resizable(False, False); dialog.transient(self.root); dialog.grab_set()
        form_frame = ttk.Frame(dialog, padding="15"); form_frame.pack(fill=tk.BOTH, expand=True)

        entries = {} # Store form entry widgets
        # Patient Selection Combobox
        ttk.Label(form_frame, text="Patient:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        patient_names_for_combo = [p['name'] for p in self.patients_list_for_appointments] if self.patients_list_for_appointments else ["No patients available"]
        patient_combo = ttk.Combobox(form_frame, values=patient_names_for_combo, state="readonly", width=37)
        patient_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        if not self.patients_list_for_appointments : patient_combo.set("No patients available") # Default if empty
        entries['patient_id_combo'] = patient_combo

        # Other appointment fields
        field_labels = {"Doctor Name:": "doctor_name", "Date (YYYY-MM-DD):": "app_date", "Time (HH:MM e.g. 14:30):": "app_time", "Reason:": "reason_for_visit"}
        for i, (label_text, field_key) in enumerate(field_labels.items(), start=1):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            entry = ttk.Entry(form_frame, width=40); entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
            entries[field_key] = entry

        # Status Combobox
        ttk.Label(form_frame, text="Status:").grid(row=len(field_labels)+1, column=0, padx=5, pady=5, sticky=tk.W)
        status_combo = ttk.Combobox(form_frame, values=["Scheduled", "Completed", "Cancelled"], state="readonly", width=37)
        status_combo.grid(row=len(field_labels)+1, column=1, padx=5, pady=5, sticky=tk.EW)
        entries['status'] = status_combo

        # Populate form if editing
        if appointment_data:
            selected_patient_name_val = "" # Find and set patient name in combobox
            for p_data in self.patients_list_for_appointments:
                if p_data['id'] == appointment_data.get('patient_id'):
                    selected_patient_name_val = p_data['name']
                    break
            if selected_patient_name_val: patient_combo.set(selected_patient_name_val)
            elif self.patients_list_for_appointments: patient_combo.set("Original patient not found") # If patient list loaded but ID doesn't match
            else: patient_combo.set("No patients available") # If patient list is empty

            entries['doctor_name'].insert(0, appointment_data.get('doctor_name', ''))
            dt_str = appointment_data.get('appointment_datetime', '')
            if dt_str: # Parse and split datetime for form fields
                try:
                    dt_obj = datetime.fromisoformat(dt_str)
                    entries['app_date'].insert(0, dt_obj.strftime("%Y-%m-%d"))
                    entries['app_time'].insert(0, dt_obj.strftime("%H:%M"))
                except ValueError: pass # Keep fields empty if parse fails
            entries['reason_for_visit'].insert(0, appointment_data.get('reason_for_visit', ''))
            status_combo.set(appointment_data.get('status', 'Scheduled')) # Default to 'Scheduled' if not present

        def on_submit():
            """Handles submission of the appointment form."""
            selected_patient_name_val = entries['patient_id_combo'].get()
            # Find patient_id corresponding to the selected name
            patient_id_val = next((p['id'] for p in self.patients_list_for_appointments if p['name'] == selected_patient_name_val), None)
            if not patient_id_val:
                return messagebox.showerror("Validation Error", "Please select a valid patient.", parent=dialog)

            date_str, time_str = entries['app_date'].get(), entries['app_time'].get()
            if not (date_str and time_str):
                return messagebox.showerror("Validation Error", "Date and Time are required.", parent=dialog)

            try: # Combine date and time, convert to ISO format
                appointment_dt_iso = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").isoformat()
            except ValueError:
                return messagebox.showerror("Validation Error", "Invalid Date or Time format. Use YYYY-MM-DD and HH:MM.", parent=dialog)

            payload = {
                "patient_id": patient_id_val,
                "doctor_name": entries['doctor_name'].get(),
                "appointment_datetime": appointment_dt_iso,
                "reason_for_visit": entries['reason_for_visit'].get(),
                "status": entries['status'].get()
            }
            if not payload["doctor_name"]: # Basic validation
                return messagebox.showerror("Validation Error", "Doctor name is required.", parent=dialog)

            if appointment_data:
                response = self.api_put(f"appointments/{appointment_data['id']}", payload)
            else:
                response = self.api_post("appointments", payload)

            if response and not (isinstance(response, dict) and 'message' in response and response.get('status_code', 200) >= 400):
                messagebox.showinfo("Success", f"Appointment {('updated' if appointment_data else 'added')} successfully!", parent=dialog)
                self.load_appointments(); dialog.destroy()

        submit_button = ttk.Button(form_frame, text="Save", command=on_submit)
        submit_button.grid(row=len(field_labels)+2, column=0, columnspan=2, pady=10)
        form_frame.columnconfigure(1, weight=1); dialog.wait_window()

    def delete_appointment(self):
        """Handles deletion of the selected appointment after confirmation."""
        if not hasattr(self, 'appointment_tree') or not self.appointment_tree: return
        selected_item_id = self.appointment_tree.focus()
        if not selected_item_id:
            return messagebox.showwarning("Selection Error", "Please select an appointment to delete.", parent=self.root)

        values = self.appointment_tree.item(selected_item_id)['values']
        appt_id, pt_name = values[0], values[1] # Assuming these are the first two columns

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete appointment ID {appt_id} for {pt_name}?", parent=self.root):
            response = self.api_delete(f"appointments/{appt_id}")
            if response and not (isinstance(response, dict) and 'message' in response and response.get('status_code',200)>=400):
                 messagebox.showinfo("Success", f"Appointment ID {appt_id} deleted successfully.", parent=self.root)
                 self.load_appointments() # Refresh list

    # --- API Helper Functions (Modified to include auth token) ---
    def _get_auth_headers(self):
        """Returns authorization headers if a token is available."""
        if self.auth_token:
            return {'Authorization': f'Bearer {self.auth_token}'}
        return {} # Return empty dict if no token

    def _handle_api_response(self, response, operation="action"):
        """Centralized handler for API responses, including error checking and message display."""
        try:
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # Handle 204 No Content (common for DELETE)
            if response.status_code == 204:
                return {"message": f"{operation.capitalize()} successful (No Content)", "status_code": 204}
            # Handle empty response body even with 2xx status
            if not response.content:
                return {"message": f"{operation.capitalize()} successful (Empty Response Body)", "status_code": response.status_code}

            return response.json() # Attempt to parse JSON

        except requests.exceptions.HTTPError as e:
            # Try to get a more specific error message from the JSON response body
            try:
                msg = response.json().get("message", str(e))
            except json.JSONDecodeError: # If response body is not JSON
                msg = str(e) + (f" - Server Response: {response.text[:100]}" if response.text else "") # Include some server text

            parent_window = self.root if self.root.winfo_exists() else None # Ensure messagebox has a valid parent
            messagebox.showerror("API Error", f"Failed to {operation}: {msg} (Status: {response.status_code})", parent=parent_window)

            if response.status_code == 401: # Unauthorized - token might be expired or invalid
                if parent_window: # Check again before showing another messagebox
                     messagebox.showerror("Authentication Error", "Your session may have expired or your token is invalid. Please restart the application to log in again.", parent=parent_window)
                if self.root.winfo_exists(): self.root.quit() # Quit application on auth error
            return {"message": f"Failed: {msg}", "status_code": response.status_code if response is not None else 0} # Return error dict

        except requests.exceptions.RequestException as e: # Network errors (e.g., connection refused)
            parent_window = self.root if self.root.winfo_exists() else None
            messagebox.showerror("API Error", f"Connection Error during {operation}: {e}", parent=parent_window)
            return {"message": f"Connection Error: {e}", "status_code": 0} # Return error dict

        except json.JSONDecodeError: # If response was OK but not valid JSON
            parent_window = self.root if self.root.winfo_exists() else None
            messagebox.showerror("API Error", f"Failed to decode server response during {operation}. Content: {response.text[:100] if response.text else '(empty response)'}", parent=parent_window)
            return {"message": "Decode Error", "status_code": response.status_code if response is not None else 0} # Return error dict

    # Wrapper methods for different API request types (GET, POST, PUT, DELETE)
    def api_get(self, endpoint):
        try:
            response = requests.get(f"{BACKEND_API_URL}/{endpoint}", headers=self._get_auth_headers(), timeout=REQUEST_TIMEOUT)
            return self._handle_api_response(response, f"fetch {endpoint}")
        except requests.exceptions.Timeout:
            messagebox.showerror("API Error", f"Timeout occurred while fetching data from {endpoint}.", parent=self.root if self.root.winfo_exists() else None)
            return None
        except requests.exceptions.RequestException as e: # Catch other potential request errors early
            messagebox.showerror("API Error", f"Failed to connect or fetch data from {endpoint}: {e}", parent=self.root if self.root.winfo_exists() else None)
            return None

    def api_post(self, endpoint, data):
        try:
            response = requests.post(f"{BACKEND_API_URL}/{endpoint}", json=data, headers=self._get_auth_headers(), timeout=REQUEST_TIMEOUT)
            return self._handle_api_response(response, f"create item for {endpoint}")
        except requests.exceptions.Timeout:
            messagebox.showerror("API Error", f"Timeout occurred while posting data to {endpoint}.", parent=self.root if self.root.winfo_exists() else None)
            return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Failed to connect or post data to {endpoint}: {e}", parent=self.root if self.root.winfo_exists() else None)
            return None

    def api_put(self, endpoint, data):
        try:
            response = requests.put(f"{BACKEND_API_URL}/{endpoint}", json=data, headers=self._get_auth_headers(), timeout=REQUEST_TIMEOUT)
            return self._handle_api_response(response, f"update item at {endpoint}")
        except requests.exceptions.Timeout:
            messagebox.showerror("API Error", f"Timeout occurred while updating data at {endpoint}.", parent=self.root if self.root.winfo_exists() else None)
            return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Failed to connect or send data to {endpoint}: {e}", parent=self.root if self.root.winfo_exists() else None)
            return None

    def api_delete(self, endpoint):
        try:
            response = requests.delete(f"{BACKEND_API_URL}/{endpoint}", headers=self._get_auth_headers(), timeout=REQUEST_TIMEOUT)
            # Handle successful DELETE (often 204 No Content or 200 with simple message)
            if 200 <= response.status_code < 300 :
                if response.status_code == 204 or not response.content: # No content to parse
                    return {"message": "Deleted successfully", "status_code": response.status_code}
                try: # Try to parse JSON if content exists
                    return response.json()
                except json.JSONDecodeError: # If not JSON, but still success status
                    return {"message": "Deleted successfully (non-JSON response)", "status_code": response.status_code}
            else: # For non-2xx responses, use the standard handler
                return self._handle_api_response(response, f"delete item at {endpoint}")
        except requests.exceptions.Timeout:
            messagebox.showerror("API Error", f"Timeout occurred while deleting data from {endpoint}.", parent=self.root if self.root.winfo_exists() else None)
            return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Failed to connect or delete data from {endpoint}: {e}", parent=self.root if self.root.winfo_exists() else None)
            return None

# --- Main Application Execution ---
if __name__ == "__main__":
    # Important: The Flask backend (clinic_management/app/app.py) MUST be running
    # with the authentication changes BEFORE starting this desktop app.
    # A default user 'admin' with password 'password123' should be created by the backend on its first run.

    root = tk.Tk()
    app = ClinicApp(root) # This now handles login before showing main UI

    # Only run the Tkinter mainloop if login was successful and the app object was fully initialized.
    # hasattr check is a safeguard in case app initialization failed very early.
    if hasattr(app, 'auth_token') and app.auth_token:
        root.mainloop()
    else:
        # If app.auth_token is None, it means login failed or was cancelled.
        # ClinicApp.__init__ should have already called root.destroy().
        # This is an additional check to ensure the window is closed if not already.
        if root.winfo_exists():
            root.destroy()
