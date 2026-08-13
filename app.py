from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from database import create_database

app = Flask(__name__)

app.secret_key = "hospital-secret-key"

create_database()


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_database():
    connection = sqlite3.connect("hospital.db")
    connection.row_factory = sqlite3.Row
    return connection


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():
    return render_template("index.html")


# ==================================================
# PATIENT REGISTRATION
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check password
        if password != confirm_password:
            return "Passwords do not match!"

        connection = get_database()

        try:

            connection.execute(
                """
                INSERT INTO patients
                (name, age, gender, phone, email, password)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    age,
                    gender,
                    phone,
                    email,
                    password
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return "This email is already registered!"

        connection.close()

        return f"Registration successful for {name}!"

    return render_template("register.html")


# ==================================================
# PATIENT LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_database()

        patient = connection.execute(
            """
            SELECT *
            FROM patients
            WHERE email = ? AND password = ?
            """,
            (email, password)
        ).fetchone()

        connection.close()

        # Login successful
        if patient:

            session["patient_id"] = patient["id"]
            session["patient_name"] = patient["name"]

            return redirect(url_for("patient_dashboard"))

        # Login failed
        else:

            return "Invalid email or password!"

    return render_template("login.html")

# ==================================================
# PATIENT DASHBOARD
# ==================================================

@app.route("/patient-dashboard")
def patient_dashboard():

    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    # Get active appointments
    appointments = connection.execute(
        """
        SELECT *
        FROM appointments
        WHERE patient_id = ?
        AND status != 'Cancelled'
        ORDER BY appointment_date, appointment_time
        """,
        (session["patient_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "patient_dashboard.html",
        patient_name=session["patient_name"],
        appointments=appointments
    )
    
# ==================================================
# BOOK APPOINTMENT
# ==================================================

@app.route("/book-appointment", methods=["GET", "POST"])
def book_appointment():

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        doctor_name = request.form["doctor_name"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]
        reason = request.form["reason"]

        connection = get_database()

        connection.execute(
            """
            INSERT INTO appointments
            (
                patient_id,
                doctor_name,
                appointment_date,
                appointment_time,
                reason
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["patient_id"],
                doctor_name,
                appointment_date,
                appointment_time,
                reason
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("patient_dashboard"))

    return render_template("book_appointment.html")

# ==================================================
# MY APPOINTMENTS
# ==================================================

@app.route("/my-appointments")
def my_appointments():

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    appointments = connection.execute(
        """
        SELECT *
        FROM appointments
        WHERE patient_id = ?
        ORDER BY appointment_date, appointment_time
        """,
        (session["patient_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "my_appointments.html",
        appointments=appointments,
        patient_name=session["patient_name"]
    )
    
    # ==================================================
# PATIENT PROFILE
# ==================================================

@app.route("/my-profile")
def my_profile():

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    patient = connection.execute(
        """
        SELECT *
        FROM patients
        WHERE id = ?
        """,
        (session["patient_id"],)
    ).fetchone()

    connection.close()

    return render_template(
        "my_profile.html",
        patient=patient
    )
    
# ==================================================
# CANCEL APPOINTMENT
# ==================================================

@app.route("/cancel-appointment/<int:appointment_id>", methods=["POST"])
def cancel_appointment(appointment_id):

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    # Cancel only the appointment belonging to logged-in patient
    connection.execute(
        """
        UPDATE appointments
        SET status = 'Cancelled'
        WHERE id = ? AND patient_id = ?
        """,
        (
            appointment_id,
            session["patient_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("my_appointments"))

# ==================================================
# EDIT PATIENT PROFILE
# ==================================================

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    # GET → Existing patient details
    if request.method == "GET":

        patient = connection.execute(
            """
            SELECT *
            FROM patients
            WHERE id = ?
            """,
            (session["patient_id"],)
        ).fetchone()

        connection.close()

        return render_template(
            "edit_profile.html",
            patient=patient
        )

    # POST → Update patient details
    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    phone = request.form["phone"]
    email = request.form["email"]

    try:

        connection.execute(
            """
            UPDATE patients
            SET
                name = ?,
                age = ?,
                gender = ?,
                phone = ?,
                email = ?
            WHERE id = ?
            """,
            (
                name,
                age,
                gender,
                phone,
                email,
                session["patient_id"]
            )
        )

        connection.commit()

    except sqlite3.IntegrityError:

        connection.close()

        return "This email is already registered!"

    connection.close()

    # Update session name
    session["patient_name"] = name

    return redirect(url_for("my_profile"))

# ==================================================
# DOCTORS
# ==================================================

@app.route("/doctors")
def doctors():

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    doctors = connection.execute(
        """
        SELECT *
        FROM doctors
        ORDER BY name
        """
    ).fetchall()

    connection.close()

    return render_template(
        "doctors.html",
        doctors=doctors
    )
    
# ==================================================
# MY PRESCRIPTIONS
# ==================================================

@app.route("/prescriptions")
def prescriptions():

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    prescriptions = connection.execute(
        """
        SELECT *
        FROM prescriptions
        WHERE patient_id = ?
        ORDER BY created_at DESC
        """,
        (session["patient_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "prescriptions.html",
        prescriptions=prescriptions,
        patient_name=session["patient_name"]
    )
    
    # ==================================================
# ADD PRESCRIPTION
# ==================================================

@app.route("/add-prescription", methods=["GET", "POST"])
def add_prescription():

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        doctor_name = request.form["doctor_name"]
        medicine_name = request.form["medicine_name"]
        dosage = request.form["dosage"]
        frequency = request.form["frequency"]
        duration = request.form["duration"]
        instructions = request.form["instructions"]

        connection.execute(
            """
            INSERT INTO prescriptions
            (
                patient_id,
                doctor_name,
                medicine_name,
                dosage,
                frequency,
                duration,
                instructions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                doctor_name,
                medicine_name,
                dosage,
                frequency,
                duration,
                instructions
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("prescriptions"))

    patients = connection.execute(
        """
        SELECT id, name, email
        FROM patients
        ORDER BY name
        """
    ).fetchall()

    doctors = connection.execute(
        """
        SELECT name, specialization
        FROM doctors
        ORDER BY name
        """
    ).fetchall()

    connection.close()

    return render_template(
        "add_prescription.html",
        patients=patients,
        doctors=doctors
    )
    
    # ==================================================
# MY LAB REPORTS
# ==================================================

@app.route("/lab-reports")
def lab_reports():

    # Check patient login
    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    reports = connection.execute(
        """
        SELECT *
        FROM lab_reports
        WHERE patient_id = ?
        ORDER BY test_date DESC
        """,
        (session["patient_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "lab_reports.html",
        reports=reports,
        patient_name=session["patient_name"]
    )
    
# ==================================================
# ADD LAB REPORT
# ==================================================

@app.route("/add-lab-report", methods=["GET", "POST"])
def add_lab_report():

    if "patient_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        doctor_name = request.form["doctor_name"]
        test_name = request.form["test_name"]
        test_date = request.form["test_date"]
        result = request.form["result"]
        status = request.form["status"]
        notes = request.form["notes"]

        connection.execute(
            """
            INSERT INTO lab_reports
            (
                patient_id,
                doctor_name,
                test_name,
                test_date,
                result,
                status,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                doctor_name,
                test_name,
                test_date,
                result,
                status,
                notes
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("lab_reports"))

    patients = connection.execute(
        """
        SELECT id, name, email
        FROM patients
        ORDER BY name
        """
    ).fetchall()

    doctors = connection.execute(
        """
        SELECT name, specialization
        FROM doctors
        ORDER BY name
        """
    ).fetchall()

    connection.close()

    return render_template(
        "add_lab_report.html",
        patients=patients,
        doctors=doctors
    )
    
    # ==================================================
# ADMIN LOGIN
# ==================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_database()

        admin = connection.execute(
            """
            SELECT *
            FROM admins
            WHERE email = ? AND password = ?
            """,
            (email, password)
        ).fetchone()

        connection.close()

        if admin:

            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["name"]

            return redirect(url_for("admin_dashboard"))

        else:

            return "Invalid admin email or password!"

    return render_template("admin_login.html")

# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_database()

    total_patients = connection.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    total_doctors = connection.execute(
        "SELECT COUNT(*) FROM doctors"
    ).fetchone()[0]

    total_appointments = connection.execute(
        "SELECT COUNT(*) FROM appointments"
    ).fetchone()[0]

    total_lab_reports = connection.execute(
        "SELECT COUNT(*) FROM lab_reports"
    ).fetchone()[0]


    # ==============================
    # APPOINTMENT STATUS COUNTS
    # ==============================

    pending_appointments = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'Pending'
        """
    ).fetchone()[0]


    confirmed_appointments = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'Confirmed'
        """
    ).fetchone()[0]


    cancelled_appointments = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'Cancelled'
        """
    ).fetchone()[0]


    completed_appointments = connection.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'Completed'
        """
    ).fetchone()[0]


    # ==============================
    # RECENT PENDING APPOINTMENTS
    # ==============================

    pending_list = connection.execute(
        """
        SELECT
            appointments.*,
            patients.name AS patient_name
        FROM appointments
        LEFT JOIN patients
            ON appointments.patient_id = patients.id
        WHERE appointments.status = 'Pending'
        ORDER BY appointments.id DESC
        LIMIT 5
        """
    ).fetchall()


    connection.close()


    # ==============================
    # SEND DATA TO DASHBOARD
    # ==============================

    return render_template(
        "admin_dashboard.html",

        admin_name=session["admin_name"],

        total_patients=total_patients,

        total_doctors=total_doctors,

        total_appointments=total_appointments,

        total_lab_reports=total_lab_reports,

        pending_appointments=pending_appointments,

        confirmed_appointments=confirmed_appointments,

        cancelled_appointments=cancelled_appointments,

        completed_appointments=completed_appointments,

        pending_list=pending_list
    )
    
# ==================================================
# ADMIN - MANAGE PATIENTS
# ==================================================

@app.route("/admin-patients")
def admin_patients():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_database()

    patients = connection.execute(
        """
        SELECT id, name, age, gender, phone, email
        FROM patients
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_patients.html",
        patients=patients,
        admin_name=session["admin_name"]
    )
    
# ==================================================
# ADMIN - MANAGE DOCTORS
# ==================================================

@app.route("/admin-doctors")
def admin_doctors():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_database()

    doctors = connection.execute(
        """
        SELECT *
        FROM doctors
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_doctors.html",
        doctors=doctors,
        admin_name=session["admin_name"]
    )
    
# ==================================================
# ADMIN - MANAGE APPOINTMENTS
# ==================================================

@app.route("/admin-appointments")
def admin_appointments():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_database()

    appointments = connection.execute(
        """
        SELECT
            appointments.*,
            patients.name AS patient_name,
            patients.email AS patient_email
        FROM appointments

        LEFT JOIN patients
        ON appointments.patient_id = patients.id

        ORDER BY
            appointments.appointment_date DESC,
            appointments.appointment_time DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_appointments.html",
        appointments=appointments,
        admin_name=session["admin_name"]
    )
    
# ==================================================
# ADMIN - MANAGE PRESCRIPTIONS
# ==================================================

@app.route("/admin-prescriptions")
def admin_prescriptions():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_database()

    prescriptions = connection.execute(
        """
        SELECT
            prescriptions.*,
            patients.name AS patient_name,
            patients.email AS patient_email
        FROM prescriptions
        LEFT JOIN patients
            ON prescriptions.patient_id = patients.id
        ORDER BY prescriptions.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_prescriptions.html",
        prescriptions=prescriptions,
        admin_name=session["admin_name"]
    )
    
# ==================================================
# ADMIN - MANAGE LAB REPORTS
# ==================================================

@app.route("/admin-lab-reports")
def admin_lab_reports():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_database()

    lab_reports = connection.execute(
        """
        SELECT
            lab_reports.*,
            patients.name AS patient_name,
            patients.email AS patient_email
        FROM lab_reports

        LEFT JOIN patients
            ON lab_reports.patient_id = patients.id

        ORDER BY lab_reports.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_lab_reports.html",
        lab_reports=lab_reports,
        admin_name=session["admin_name"]
    )
    
    # ==================================================
# ADMIN - UPDATE APPOINTMENT STATUS
# ==================================================

@app.route(
    "/admin-appointment-status/<int:appointment_id>/<status>",
    methods=["POST"]
)
def admin_update_appointment_status(
    appointment_id,
    status
):

    # Check admin login
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    # Allow only valid statuses
    allowed_statuses = [
        "Pending",
        "Confirmed",
        "Cancelled",
        "Completed"
    ]

    if status not in allowed_statuses:
        return "Invalid appointment status!"

    connection = get_database()

    connection.execute(
        """
        UPDATE appointments
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            appointment_id
        )
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("admin_appointments")
    )
    
# ==================================================
# DOCTOR LOGIN
# ==================================================

@app.route("/doctor-login", methods=["GET", "POST"])
def doctor_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_database()

        doctor = connection.execute(
            """
            SELECT *
            FROM doctors
            WHERE email = ?
            AND password = ?
            """,
            (email, password)
        ).fetchone()

        connection.close()

        if doctor:

            session["doctor_id"] = doctor["id"]
            session["doctor_name"] = doctor["name"]

            return redirect(
                url_for("doctor_dashboard")
            )

        else:

            return "Invalid doctor email or password!"

    return render_template("doctor_login.html")

# ==================================================
# DOCTOR DASHBOARD
# ==================================================

# ==================================================
# DOCTOR DASHBOARD
# ==================================================

@app.route("/doctor-dashboard")
def doctor_dashboard():

    # ----------------------------------------------
    # CHECK DOCTOR LOGIN
    # ----------------------------------------------

    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))


    # ----------------------------------------------
    # DATABASE CONNECTION
    # ----------------------------------------------

    connection = get_database()

    doctor_id = session["doctor_id"]


    # ----------------------------------------------
    # GET LOGGED-IN DOCTOR
    # ----------------------------------------------

    doctor = connection.execute(
        """
        SELECT *
        FROM doctors
        WHERE id = ?
        """,
        (doctor_id,)
    ).fetchone()


    # ----------------------------------------------
    # IF DOCTOR NOT FOUND
    # ----------------------------------------------

    if doctor is None:

        connection.close()

        session.pop("doctor_id", None)
        session.pop("doctor_name", None)

        return redirect(url_for("doctor_login"))


    # ----------------------------------------------
    # GET DOCTOR APPOINTMENTS
    # ----------------------------------------------
    # Example:
    #
    # Doctor table:
    # Dr. Anil Reddy
    #
    # Appointment table:
    # Dr. Anil Reddy - Orthopedic
    #
    # LIKE allows both to match.
    # ----------------------------------------------

    appointments = connection.execute(
        """
        SELECT
            appointments.*,

            patients.name AS patient_name,
            patients.age AS patient_age,
            patients.gender AS patient_gender,
            patients.phone AS patient_phone,
            patients.email AS patient_email

        FROM appointments

        LEFT JOIN patients
            ON appointments.patient_id = patients.id

        WHERE appointments.doctor_name LIKE ?

        ORDER BY
            appointments.appointment_date DESC,
            appointments.appointment_time DESC
        """,
        (
            "%" + doctor["name"] + "%",
        )
    ).fetchall()


    # ----------------------------------------------
    # CLOSE DATABASE
    # ----------------------------------------------

    connection.close()


    # ----------------------------------------------
    # OPEN DOCTOR DASHBOARD
    # ----------------------------------------------

    return render_template(
        "doctor_dashboard.html",
        doctor=doctor,
        appointments=appointments
    )
    
# ==================================================
# DOCTOR - UPDATE APPOINTMENT STATUS
# ==================================================

@app.route("/doctor-update-appointment/<int:appointment_id>/<status>")
def doctor_update_appointment(appointment_id, status):

    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        return "Invalid appointment status!"

    connection = get_database()

    # Get logged-in doctor
    doctor = connection.execute(
        """
        SELECT *
        FROM doctors
        WHERE id = ?
        """,
        (session["doctor_id"],)
    ).fetchone()

    if doctor is None:
        connection.close()
        return redirect(url_for("doctor_login"))

    # Update only this doctor's appointment
    connection.execute(
        """
        UPDATE appointments
        SET status = ?
        WHERE id = ?
        AND doctor_name LIKE ?
        """,
        (
            status,
            appointment_id,
            "%" + doctor["name"] + "%"
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("doctor_dashboard"))

# ==================================================
# DOCTOR - ADD PRESCRIPTION
# ==================================================

@app.route("/doctor-add-prescription/<int:patient_id>", methods=["GET", "POST"])
def doctor_add_prescription(patient_id):

    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    connection = get_database()

    doctor = connection.execute(
        """
        SELECT *
        FROM doctors
        WHERE id = ?
        """,
        (session["doctor_id"],)
    ).fetchone()

    if doctor is None:
        connection.close()
        return redirect(url_for("doctor_login"))

    patient = connection.execute(
        """
        SELECT *
        FROM patients
        WHERE id = ?
        """,
        (patient_id,)
    ).fetchone()

    if patient is None:
        connection.close()
        return "Patient not found!"

    if request.method == "POST":

        medicine_name = request.form["medicine_name"]
        dosage = request.form["dosage"]
        frequency = request.form["frequency"]
        duration = request.form["duration"]
        instructions = request.form.get("instructions", "")

        connection.execute(
            """
            INSERT INTO prescriptions
            (
                patient_id,
                doctor_id,
                doctor_name,
                medicine_name,
                dosage,
                frequency,
                duration,
                instructions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                doctor["id"],
                doctor["name"],
                medicine_name,
                dosage,
                frequency,
                duration,
                instructions
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("doctor_dashboard"))

    connection.close()

    return render_template(
        "doctor_add_prescription.html",
        patient=patient,
        doctor=doctor
    )


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==================================================
# RUN FLASK APPLICATION
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)
