import sqlite3

conn = sqlite3.connect("students.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (

id INTEGER PRIMARY KEY AUTOINCREMENT,

name TEXT,

rollno TEXT,

department TEXT,

prediction TEXT,

riskscore INTEGER

)
""")

conn.commit()
conn.close()

print("Database Created")