import openpyxl
from database import get_db_connection
import os
import datetime

def generate_excel_report(output_filename="student_data.xlsx"):
    """
    Generates an Excel file containing all student registration details and their best/latest quiz attempts.
    """
    wb = openpyxl.Workbook()
    
    # --- Sheet 1: Students ---
    ws_students = wb.active
    ws_students.title = "Registered Students"
    
    student_headers = ["ID", "Name", "Phone", "Father's Name", "Father's Phone", 
                       "College Location", "Inter College", "School", 
                       "EAMCET Reg", "Address", "Email"]
    ws_students.append(student_headers)
    
    conn = get_db_connection()
    students_data = conn.execute("SELECT * FROM students").fetchall()
    
    for row in students_data:
        ws_students.append([
            row['id'], row['name'], row['phone'], row['father_name'], row['father_phone'],
            row['college_location'], row['inter_college'], row['school'],
            row['eamcet_reg'], row['address'], row['email']
        ])
        
    # --- Sheet 2: Quiz Attempts ---
    ws_attempts = wb.create_sheet(title="Quiz Attempts")
    attempt_headers = ["Attempt ID", "Student Name", "Quiz Date", "Answer Text", "Time Taken (s)", "Attempt Date"]
    ws_attempts.append(attempt_headers)
    
    attempts_data = conn.execute('''
        SELECT a.id, s.name, q.date, a.answer_text, a.time_taken, a.date as attempt_date
        FROM attempts a
        JOIN students s ON a.student_id = s.id
        JOIN quizzes q ON a.quiz_id = q.id
        ORDER BY a.date DESC
    ''').fetchall()
    
    for row in attempts_data:
        ws_attempts.append([
            row['id'], row['name'], row['date'], row['answer_text'], row['time_taken'], row['attempt_date']
        ])
        
    conn.close()
    
    wb.save(output_filename)
    return output_filename

if __name__ == "__main__":
    generate_excel_report()
    print("Sample report generated.")
