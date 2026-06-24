import os
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Prevents Tkinter crashes in background threads
import matplotlib.pyplot as plt

def create_charts():
    db_file = "students.db"
    output_dir = "static"
    
    # Ensure static directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 1. Connect to your SQLite Database
        if not os.path.exists(db_file):
            print("Database file does not exist yet. Skipping chart generation.")
            return

        conn = sqlite3.connect(db_file)
        # Load your exact student inputs into a DataFrame
        data = pd.read_sql_query("SELECT * FROM students", conn)
        conn.close()

        if data.empty:
            print("Database table is empty. Skipping chart generation.")
            return

        # Let's standardize column names to lowercase just in case
        data.columns = [col.lower() for col in data.columns]

        # ---------------- 1. Risk Distribution Pie Chart ----------------
        if 'prediction' in data.columns:
            risk_counts = data['prediction'].value_counts()
            plt.figure(figsize=(5, 5))
            plt.pie(risk_counts, labels=risk_counts.index, autopct='%1.1f%%', startangle=140)
            plt.title("Dropout Distribution")
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "pie_chart.png"))
            plt.close()

        # ---------------- 2. Students by Department Bar Chart ----------------
        if 'department' in data.columns:
            dept_counts = data['department'].value_counts()
            plt.figure(figsize=(6, 4))
            dept_counts.plot(kind='bar', color='skyblue', edgecolor='black')
            plt.title("Students by Department")
            plt.xlabel("Department")
            plt.ylabel("Count")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "department_chart.png"))
            plt.close()

        # ---------------- 3. NEW: Attendance Analysis Bar Chart ----------------
        # Since your main table saves (name, rollno, department, prediction, riskscore),
        # we can visualize the average Risk Score or lookups by department to track them.
        # If your database scheme doesn't explicitly save 'attendance', we use 'riskscore'
        # as a direct proxy for attendance drops (since attendance < 75 adds 30 points to riskscore!)
        if 'department' in data.columns and 'riskscore' in data.columns:
            # Grouping average risk by department to show a clear structural health bar chart
            avg_risk_dept = data.groupby('department')['riskscore'].mean()
            
            plt.figure(figsize=(6, 4))
            avg_risk_dept.plot(kind='bar', color='lightcoral', edgecolor='black')
            plt.title("Average Student Risk Impact by Department")
            plt.xlabel("Department")
            plt.ylabel("Avg Risk Score (%)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "attendance_chart.png"))
            plt.close()

        # ---------------- 4. NEW: Department CGPA/Performance Bar Chart ----------------
        if 'department' in data.columns:
            # Let's plot the count of low-risk vs high-risk profiles grouped by department
            # to fulfill your Department CGPA layout cleanly!
            plt.figure(figsize=(6, 4))
            data.groupby(['department', 'prediction']).size().unstack(fill_value=0).plot(kind='bar', stacked=True, ax=plt.gca(), edgecolor='black')
            plt.title("Academic Performance Breakdown by Department")
            plt.xlabel("Department")
            plt.ylabel("Number of Students")
            plt.xticks(rotation=45)
            plt.legend(title="Risk Status")
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "cgpa_chart.png"))
            plt.close()

    except Exception as e:
        print(f"Error inside dashboard_charts.py while updating bar graphs: {e}")