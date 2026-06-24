import os
import io
import csv
import sqlite3
import joblib
import pandas as pd
from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
from reportlab.pdfgen import canvas
from dashboard_charts import create_charts  # Imported chart generator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
app = Flask(__name__)
app.secret_key = "student_dropout_secret_key"

# Store latest report metrics
report_data = {}

# Load ML model and encoder safely
try:
    model = joblib.load("dropout_model.pkl")
    encoder = joblib.load("department_encoder.pkl")
except Exception as e:
    print(f"Error loading model files: {e}. Please ensure pickle files exist.")

DB_FILE = "students.db"

def init_db():
    """Ensures the table exists with your correct column names matching your layout."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            rollno TEXT UNIQUE,
            department TEXT,
            year INTEGER,
            attendance REAL,
            cgpa REAL,
            backlogs INTEGER,
            internal_marks REAL,
            fee_paid TEXT,
            prediction TEXT,
            riskscore INTEGER
        )
    """)

       
    conn.commit()
    conn.close()

# Initialize database safely on startup
init_db()

# ---------------- BULK DATA CSV UPLOAD ROUTE ----------------

@app.route('/upload-students', methods=['GET', 'POST'])
def upload_students():
    if not session.get('admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'student_file' not in request.files:
            flash("No file field detected.")
            return redirect(request.url)
            
        file = request.files['student_file']
        if file.filename == '':
            flash("No file selected.")
            return redirect(request.url)
            
        if file and file.filename.endswith('.csv'):
            try:
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                count = 0
                total_rows = 0

                for row in csv_reader:
                    total_rows += 1
                    # Extract variables from CSV matching your exact spreadsheet headers
                    department = row['Department'].strip()
                    year = int(row['Year'])
                    attendance = float(row['Attendance (%)'])
                    cgpa = float(row['CGPA'])
                    backlogs = int(row['Backlogs'])
                    internal_marks = float(row['Internal M']) if 'Internal M' in row else float(row['Internal Marks'])
                    fee_paid_str = row['Fee Paid'].strip()
                    
                    # Convert fee text to number (1 for Yes, 0 for No) to match ML model requirements
                    fee_numeric = 1 if fee_paid_str.lower() == 'yes' or fee_paid_str == '1' else 0

                    # --- RUN AUTOMATIC ML RISK CALCULATION FOR THIS ROW ---
                    risk_score = 0
                    if attendance < 75: risk_score += 30
                    if cgpa < 6: risk_score += 25
                    if backlogs > 2: risk_score += 25
                    if fee_numeric == 0: risk_score += 20
                    risk_percent = min(risk_score, 100)

                    if risk_percent >= 70:
                        result = "High Risk"
                    elif risk_percent >= 40:
                        result = "Medium Risk"
                    else:
                        result = "Low Risk"

                    # Insert directly into DB with the freshly calculated predictions
                    cursor.execute("""
                        INSERT INTO students (rollno, name, department, year, attendance, cgpa, backlogs, internal_marks, fee_paid, prediction, riskscore)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(rollno) DO UPDATE SET
                            name=excluded.name,
                            department=excluded.department,
                            year=excluded.year,
                            attendance=excluded.attendance,
                            cgpa=excluded.cgpa,
                            backlogs=excluded.backlogs,
                            internal_marks=excluded.internal_marks,
                            fee_paid=excluded.fee_paid,
                            prediction=excluded.prediction,
                            riskscore=excluded.riskscore
                    """, (
                        row['Roll Number'].strip(),
                        row.get('StudentName', '').strip(),
                        department,
                        year,
                        attendance,
                        cgpa,
                        backlogs,
                        internal_marks,
                        fee_paid_str,
                        result,        
                        risk_percent   
                    ))
                    count += 1
                
                conn.commit()
                print("CSV rows:", total_rows)
                print("Inserted rows:", count)
                
                # Print output to terminal safely outside the parsing loop
                print(pd.read_sql_query("SELECT name, rollno FROM students LIMIT 10", conn))
                conn.close()
                
                # Regenerate charts since data metrics changed
                create_charts()
                
                flash(f"Successfully processed, predicted, and imported {count} students!")
                return redirect(url_for('admin'))
                
            except Exception as e:
                flash(f"Error processing upload: {str(e)}")
                return redirect(request.url)

    return render_template('upload_students.html')



# ---------------- ADMIN LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect(url_for('admin'))
        elif username == "student" and password == "student123":
            return redirect(url_for('home'))
        else:
            return render_template("login.html", error="Invalid Login")

    return render_template("login.html")

# ---------------- ADMIN LOGOUT ----------------

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))


# ---------------- ADMIN DASHBOARD ----------------

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    try:
        create_charts() 
        
        if os.path.exists(DB_FILE):
            conn = sqlite3.connect(DB_FILE)
            data = pd.read_sql_query("""
                SELECT name, rollno, department, prediction, riskscore
                FROM students
                WHERE name IS NOT NULL AND name != ''
                ORDER BY id DESC
            """, conn)
            conn.close()
            
            data['riskscore'] = pd.to_numeric(data['riskscore'], errors='coerce').fillna(0)
            
            total_students = len(data)
            high_risk = len(data[data["riskscore"] >= 70])
            medium_risk = len(data[(data["riskscore"] >= 40) & (data["riskscore"] < 70)])
            low_risk = len(data[data["riskscore"] < 40])
            
            departments = data["department"].value_counts().to_dict()
            recent_students = data.head(10).to_dict("records")
        else:
            total_students, high_risk, medium_risk, low_risk = 0, 0, 0, 0
            departments, recent_students = {}, []

    except Exception as e:
        print("Dashboard Error:", e)
        total_students, high_risk, medium_risk, low_risk = 0, 0, 0, 0
        departments, recent_students = {}, []

    return render_template(
        "admin.html",
        total_students=total_students,
        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,
        departments=departments,
        recent_students=recent_students
    )

from flask import send_file

#---------------downloading full students data------------------
@app.route('/download-history')
def download_history():

    if not session.get('admin'):
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect(DB_FILE)

        df = pd.read_sql_query("""
            SELECT
                rollno AS RollNo,
                name AS Name,
                department AS Department,
                year AS Year,
                attendance AS Attendance,
                cgpa AS CGPA,
                backlogs AS Backlogs,
                internal_marks AS InternalMarks,
                fee_paid AS FeePaid,
                prediction AS Prediction,
                riskscore AS RiskScore
            FROM students
            ORDER BY id DESC
        """, conn)

        conn.close()

        export_file = "student_report.csv"

        df.to_csv(export_file, index=False)

        return send_file(
            export_file,
            as_attachment=True,
            download_name="Student_Report.csv"
        )

    except Exception as e:
        return f"Export Error: {str(e)}"

#---------------Filter risk------------------------
@app.route('/filter-risk', methods=['POST'])
def filter_risk():

    risk = request.form['risk']

    conn = sqlite3.connect(DB_FILE)

    students = pd.read_sql_query(
        """
        SELECT 
            rollno,
            department,
            name,
            prediction,
            riskscore
        FROM students
        WHERE prediction = ?
        ORDER BY department, rollno
        """,
        conn,
        params=(risk,)
    )

    conn.close()

    return render_template(
        "risk_students.html",
        students=students.to_dict("records"),
        risk=risk
    )

#--------------risk report download------------

@app.route('/download_risk_report')
def download_risk_report():

    import sqlite3
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from flask import send_file

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT rollno, department, prediction
        FROM students
        WHERE prediction IN ('High Risk','Medium Risk')
        """)

    data = cursor.fetchall()

    conn.close()

    filename = "High_Medium_Risk_Report.pdf"

    pdf = SimpleDocTemplate(filename)

    table_data = [
        ["Roll No", "Department", "Prediction"]
    ]

    for row in data:
        table_data.append([
            str(row[0]),
            str(row[1]),
            str(row[2])
        ])

    table = Table(table_data)

    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),1,None)
    ]))

    pdf.build([table])


    return send_file(
        filename,
        as_attachment=True,
        mimetype="application/pdf"
    )

#----------------edit student details--------------
@app.route("/edit/<rollno>", methods=["GET", "POST"])
def edit_student(rollno):

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":

        new_rollno = request.form["rollno"]
        name = request.form["name"]
        department = request.form["department"]
        year = int(request.form["year"])
        attendance = float(request.form["attendance"])
        cgpa = float(request.form["cgpa"])
        backlogs = int(request.form["backlogs"])
        internal_marks = float(request.form["internal_marks"])
        fee_paid = request.form["fee_paid"]

        # Recalculate Risk
        risk_score = 0

        if attendance < 75:
            risk_score += 30

        if cgpa < 6:
            risk_score += 25

        if backlogs > 2:
            risk_score += 25

        if fee_paid.lower() == "no":
            risk_score += 20

        risk_percent = min(risk_score, 100)

        if risk_percent >= 70:
            prediction = "High Risk"
        elif risk_percent >= 40:
            prediction = "Medium Risk"
        else:
            prediction = "Low Risk"

        cursor.execute("""
        UPDATE students
        SET
            rollno=?,
            name=?,
            department=?,
            year=?,
            attendance=?,
            cgpa=?,
            backlogs=?,
            internal_marks=?,
            fee_paid=?,
            prediction=?,
            riskscore=?
        WHERE rollno=?
        """,
        (
            new_rollno,
            name,
            department,
            year,
            attendance,
            cgpa,
            backlogs,
            internal_marks,
            fee_paid,
            prediction,
            risk_percent,
            rollno
        ))

        conn.commit()
        conn.close()

        create_charts()

        return redirect("/admin")

    cursor.execute(
        "SELECT * FROM students WHERE rollno=?",
        (rollno,)
    )

    student = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_student.html",
        student=student
    )

#------------delete student data----------------
@app.route("/delete/<rollno>")
def delete_student(rollno):

    if not session.get('admin'):
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM students WHERE rollno=?",
        (rollno,)
    )

    conn.commit()
    conn.close()

    create_charts()

    return redirect("/admin")
# ---------------- HOME PAGE ----------------

@app.route('/')
def home():
    return render_template("index.html")

#-------------------------- Student Search Feature ---------------------------

@app.route('/search', methods=['GET', 'POST'])
def search():

    rollno = ""

    if request.method == 'POST':
        rollno = request.form.get('rollno', '').strip()
    else:
        rollno = request.args.get('rollno', '').strip()

    if not rollno:
        flash("Please enter a valid Roll Number.")
        return redirect(url_for('admin'))

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE rollno=?",
        (rollno,)
    )

    student = cursor.fetchone()

    conn.close()

    if not student:
        return f"<h3>Student with Roll Number '{rollno}' not found.</h3><a href='/admin'>Go Back</a>"

    warnings = []
    recommendations = []

    if student["attendance"] < 75:
        warnings.append("Attendance below 75%")
        recommendations.append("Improve attendance to at least 75%")

    if student["cgpa"] < 6:
        warnings.append("CGPA below 6.0")
        recommendations.append("Focus on academics to improve CGPA")

    if student["backlogs"] > 2:
        warnings.append("More than 2 backlogs")
        recommendations.append("Clear backlog subjects immediately")

    if student["fee_paid"] == "No":
        warnings.append("Fee payment pending")
        recommendations.append("Complete pending fee payment")

    return render_template(
        "search.html",
        student=student,
        warnings=warnings,
        recommendations=recommendations
    )

# ---------------- PREDICTION ----------------

@app.route('/predict', methods=['POST'])
def predict():
    global report_data

    try:
        name = request.form['name'].strip()
        rollno = request.form['rollno'].strip()
        department = request.form['department'].strip()
        year = int(request.form['year'])
        attendance = float(request.form['attendance'])
        cgpa = float(request.form['cgpa'])
        backlogs = int(request.form['backlogs'])
        marks = float(request.form['marks'])
        fee = int(request.form['fee'])

        # ML Prediction
        department_encoded = encoder.transform([department])[0]
        input_data = [[
            department_encoded,
            year,
            attendance,
            max(0.0, min(10.0, cgpa)),  
            backlogs,
            marks,
            fee
        ]]

        ml_prediction = model.predict(input_data)[0]

        # Risk Calculation
        risk_score = 0
        warnings = []  

        if attendance < 75:
            risk_score += 30
            warnings.append("Attendance below 75%")

        if cgpa < 6:
            risk_score += 25
            warnings.append("CGPA below 6.0")

        if backlogs > 2:
            risk_score += 25
            warnings.append("More than 2 backlogs")

        if fee == 0:
            risk_score += 20
            warnings.append("Fee Payment Pending")

        risk_percent = min(risk_score, 100)

        if risk_percent >= 70:
            result = "High Risk"
        elif risk_percent >= 40:
            result = "Medium Risk"
        else:
            result = "Low Risk"

        placement_score = (cgpa * 8) + (attendance * 0.2) - (backlogs * 5)
        placement_score = round(max(0, min(100, placement_score)), 2)

        # Save History (CSV Backup)
        csv_file = "student_history.csv"
        history = pd.DataFrame({
            "Name": [name],
            "RollNo": [rollno],
            "Department": [department],
            "ML_Prediction": [ml_prediction],
            "Final_Result": [result],
            "RiskScore": [risk_percent],
            "PlacementScore": [placement_score]
        })
        file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
        history.to_csv(csv_file, mode="a", header=not file_exists, index=False)

        # Update or Insert Student record directly using raw SQLite
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (rollno, name, department, year, attendance, cgpa, backlogs, internal_marks, fee_paid, prediction, riskscore)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rollno) DO UPDATE SET
                name=excluded.name,
                department=excluded.department,
                year=excluded.year,
                attendance=excluded.attendance,
                cgpa=excluded.cgpa,
                backlogs=excluded.backlogs,
                internal_marks=excluded.internal_marks,
                fee_paid=excluded.fee_paid,
                prediction=excluded.prediction,
                riskscore=excluded.riskscore
        """, (rollno, name, department, year, attendance, cgpa, backlogs, marks, "Yes" if fee == 1 else "No", result, risk_percent))
        conn.commit()
        conn.close()

        # Store PDF Data Structure
        report_data = {
            "rollno": rollno,
            "department": department,
            "prediction": result,
            "risk": risk_percent,
            "placement": placement_score,
            "recommendations": warnings  
        }
        
        create_charts()

        return render_template(
            "index.html",
            name=name,
            prediction=result,
            risk=risk_percent,
            rollno=rollno,
            placement_score=placement_score,
            warnings=warnings  
        )

    except Exception as e:
        print("Prediction processing error:", e)
        return f"An error occurred during prediction processing: {str(e)}"


# ---------------- PDF REPORT ----------------

@app.route('/generate_report')
def generate_report():
    if not report_data:
        return "Please predict a student first before generating report"

    filename = "Student_Report.pdf"
    pdf = canvas.Canvas(filename)
    y = 750

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, y, "Student Dropout Report")
    
    y -= 50
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, y, f"Roll Number : {report_data['rollno']}")
    
    y -= 30
    pdf.drawString(100, y, f"Department : {report_data['department']}")
    
    y -= 30
    pdf.drawString(100, y, f"Risk Level : {report_data['prediction']}")
    
    y -= 30
    pdf.drawString(100, y, f"Risk Percentage : {report_data['risk']}%")
    
    y -= 30
    pdf.drawString(100, y, f"Placement Score : {report_data['placement']}%")
    
    y -= 50
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(100, y, "Recommendations:")
    
    y -= 30
    pdf.setFont("Helvetica", 12)
    if not report_data["recommendations"]:
        pdf.drawString(120, y, "- Keep up the excellent academic standing.")
    else:
        for item in report_data["recommendations"]:
            pdf.drawString(120, y, f"- {item}")
            y -= 25

    pdf.save()
    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)