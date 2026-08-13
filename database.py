import sqlite3


def create_database():

    connection = sqlite3.connect("hospital.db")
    cursor = connection.cursor()

    # ==================================================
    # PATIENTS TABLE
    # ==================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # ==================================================
    # DEFAULT PATIENT
    # ==================================================

    cursor.execute("SELECT COUNT(*) FROM patients")
    patient_count = cursor.fetchone()[0]

    if patient_count == 0:

        cursor.execute("""
            INSERT INTO patients
            (name, age, gender, phone, email, password)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Test Patient",
            22,
            "Male",
            "9876543210",
            "patient@hospital.com",
            "patient123"
        ))

    # ==================================================
    # ADMINS TABLE
    # ==================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # ==================================================
    # DEFAULT ADMIN
    # ==================================================

    cursor.execute("SELECT COUNT(*) FROM admins")
    admin_count = cursor.fetchone()[0]

    if admin_count == 0:

        cursor.execute("""
            INSERT INTO admins
            (name, email, password)
            VALUES (?, ?, ?)
        """, (
            "Hospital Admin",
            "admin@hospital.com",
            "admin123"
        ))

    # ==================================================
    # DOCTORS TABLE
    # ==================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            phone TEXT,
            email TEXT UNIQUE,
            password TEXT,
            experience INTEGER DEFAULT 0
        )
    """)

    # ==================================================
    # ADD PASSWORD COLUMN IF OLD TABLE EXISTS
    # ==================================================

    try:
        cursor.execute("""
            ALTER TABLE doctors
            ADD COLUMN password TEXT
        """)
    except sqlite3.OperationalError:
        pass

    # ==================================================
    # APPOINTMENTS TABLE
    # ==================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER,
            doctor_name TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Pending',

            FOREIGN KEY (patient_id)
            REFERENCES patients(id)
        )
    """)

    # ==================================================
    # SAMPLE DOCTORS
    # ==================================================

    doctors = [
        (
            "Dr. Rajesh Kumar",
            "General Physician",
            "9876543210",
            "rajesh@hospital.com",
            "doctor123",
            10
        ),
        (
            "Dr. Priya Sharma",
            "Cardiologist",
            "9876543211",
            "priya@hospital.com",
            "doctor123",
            8
        ),
        (
            "Dr. Anil Reddy",
            "Orthopedic",
            "9876543212",
            "anil@hospital.com",
            "doctor123",
            12
        ),
        (
            "Dr. Sneha Rao",
            "Dermatologist",
            "9876543213",
            "sneha@hospital.com",
            "doctor123",
            7
        ),
        (
            "Dr. Kiran Kumar",
            "Neurologist",
            "9876543214",
            "kiran@hospital.com",
            "doctor123",
            15
        )
    ]

    cursor.execute("SELECT COUNT(*) FROM doctors")
    doctor_count = cursor.fetchone()[0]

    if doctor_count == 0:

        cursor.executemany("""
            INSERT INTO doctors
            (name, specialization, phone, email, password, experience)
            VALUES (?, ?, ?, ?, ?, ?)
        """, doctors)

    # ==================================================
    # PRESCRIPTIONS TABLE
    # ==================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            doctor_id INTEGER,

            doctor_name TEXT NOT NULL,

            medicine_name TEXT NOT NULL,

            dosage TEXT NOT NULL,

            frequency TEXT NOT NULL,

            duration TEXT NOT NULL,

            instructions TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (patient_id)
            REFERENCES patients(id)
        )
    """)

    # ==================================================
    # LAB REPORTS TABLE
    # ==================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lab_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            doctor_name TEXT,

            test_name TEXT NOT NULL,

            test_date TEXT NOT NULL,

            result TEXT,

            status TEXT DEFAULT 'Available',

            notes TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (patient_id)
            REFERENCES patients(id)
        )
    """)

    # ==================================================
    # SAVE DATABASE
    # ==================================================

    connection.commit()
    connection.close()

    print("Database created successfully!")


# ==================================================
# RUN DATABASE
# ==================================================

if __name__ == "__main__":
    create_database()
