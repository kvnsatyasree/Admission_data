from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import datetime
import json
import os
import atexit
import qrcode
import io
import base64
import socket
from dotenv import load_dotenv
import webbrowser
from threading import Timer

# Load environment variables (like Twilio secrets)
load_dotenv()

def get_local_ip():
    """Retrieves the local IPv4 address connected to the given wifi network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't have to be reachable, just forces the OS to figure out the route
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

from apscheduler.schedulers.background import BackgroundScheduler
# from database import init_db, get_db_connection
# from ai_quiz import generate_daily_quiz, evaluate_winner
# from notifier import send_winner_notification, send_participation_email
# from export_excel import generate_excel_report
from intermediate.database import init_db, get_db_connection
from intermediate.ai_quiz import generate_daily_quiz, evaluate_winner
from intermediate.notifier import send_winner_notification, send_participation_email
from intermediate.export_excel import generate_excel_report

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize DB on start (safe to run repeatedly because CREATE TABLE uses IF NOT EXISTS)
init_db()

# --- Automated Background Tasks ---
def select_daily_winner_job():
    """ Runs exactly at 10 PM daily to ask Ollama to evaluate answers and send sms """
    today = datetime.date.today().isoformat()
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE date = ?', (today,)).fetchone()
    
    if quiz:
        attempts_raw = conn.execute('SELECT * FROM attempts WHERE quiz_id = ? AND date = ?', (quiz['id'], today)).fetchall()
        
        if attempts_raw:
            attempts = []
            for a in attempts_raw:
                attempts.append({
                    'id': a['id'],
                    'student_id': a['student_id'],
                    'answer_text': a['answer_text'],
                    'time_taken': a['time_taken']
                })
                
            quiz_data = json.loads(quiz['questions_json'])[0]
            
            # AI Evaluates the text submissions
            winning_student_id = evaluate_winner(quiz_data, attempts)
            
            if winning_student_id:
                existing_winner = conn.execute('SELECT * FROM winners WHERE date = ?', (today,)).fetchone()
                if not existing_winner:
                    student = conn.execute('SELECT * FROM students WHERE id = ?', (winning_student_id,)).fetchone()
                    winning_attempt = next((x for x in attempts if x['student_id'] == winning_student_id), None)
                    
                    conn.execute('INSERT INTO winners (date, student_id, answer_text, time_taken) VALUES (?, ?, ?, ?)',
                                 (today, winning_student_id, winning_attempt['answer_text'], winning_attempt['time_taken']))
                    conn.commit()
                    
                    # Notify
                    send_winner_notification(student['name'], student['email'], winning_attempt['time_taken'], winning_attempt['answer_text'])
                    print(f"AUTOMATED 10PM TASK: AI selected winner {student['name']}. Email notification dispatched!")
                    
    conn.close()

# Start Scheduler
scheduler = BackgroundScheduler()
# trigger="cron" lets us specific a time to run every day. 22 = 10 PM.
scheduler.add_job(func=select_daily_winner_job, trigger="cron", hour=22, minute=0)
scheduler.start()

# Stop scheduler securely when destroying the app
atexit.register(lambda: scheduler.shutdown())


# --- Routes ---
@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/qr')
def generate_qr():
    # Dynamic portal URL Generation using Local Network IP
    local_ip = get_local_ip()
    port = 5000
    url = f"http://{local_ip}:{port}/"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return render_template('qr_display.html', qr_image=b64, portal_url=url)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            phone = request.form['phone']
            father_name = request.form['father_name']
            father_phone = request.form['father_phone']
            college_location = request.form['college_location']
            inter_college = request.form['inter_college']
            school = request.form['school']
            eamcet_reg = request.form['eamcet_reg']
            address = request.form['address']
            email = request.form['email']
            password = request.form['password']

            conn = get_db_connection()
            conn.execute('''
                INSERT INTO students 
                (name, phone, father_name, father_phone, college_location, inter_college, school, eamcet_reg, address, email, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, phone, father_name, father_phone, college_location, inter_college, school, eamcet_reg, address, email, password))
            conn.commit()
            conn.close()
            
            flash('Registration Successful. Please Login.')
            return redirect(url_for('student_login'))
        except Exception as e:
            flash(f'An error occurred: Email might already be registered.')
            print(f"Error during registration: {e}")
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        student = conn.execute('SELECT * FROM students WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()
        
        if student:
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('student_id', None)
    session.pop('student_name', None)
    session.pop('admin_logged_in', None)
    return redirect(url_for('landing_page'))

@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE id = ?', (session['student_id'],)).fetchone()
    
    today = datetime.date.today().isoformat()
    quiz = conn.execute('SELECT id FROM quizzes WHERE date = ?', (today,)).fetchone()
    attempted_today = False
    if quiz:
         attempt = conn.execute('SELECT * FROM attempts WHERE student_id = ? AND quiz_id = ?', 
                               (session['student_id'], quiz['id'])).fetchone()
         if attempt:
             attempted_today = True

    conn.close()
    
    return render_template('dashboard.html', student=student, attempted_today=attempted_today)

@app.route('/quiz', methods=['GET', 'POST'])
def take_quiz():
    if 'student_id' not in session:
         return redirect(url_for('student_login'))
         
    today = datetime.date.today().isoformat()
    conn = get_db_connection()
    
    quiz = conn.execute('SELECT * FROM quizzes WHERE date = ?', (today,)).fetchone()
    
    if not quiz:
        questions = generate_daily_quiz()
        conn.execute('INSERT INTO quizzes (date, questions_json) VALUES (?, ?)', (today, json.dumps(questions)))
        conn.commit()
        quiz = conn.execute('SELECT * FROM quizzes WHERE date = ?', (today,)).fetchone()
        
    attempt = conn.execute('SELECT * FROM attempts WHERE student_id = ? AND quiz_id = ?', 
                           (session['student_id'], quiz['id'])).fetchone()
    
    if attempt:
        conn.close()
        flash("You have already submitted your answer for today!")
        return redirect(url_for('dashboard'))
        
    questions = json.loads(quiz['questions_json'])
    
    if request.method == 'POST':
        time_taken = int(request.form.get('time_taken', 300))
        answer_text = request.form.get('answer_text', '').strip()
                
        conn.execute('INSERT INTO attempts (student_id, quiz_id, answer_text, time_taken, date) VALUES (?, ?, ?, ?, ?)',
                    (session['student_id'], quiz['id'], answer_text, time_taken, today))
        student = conn.execute('SELECT email FROM students WHERE id = ?', (session['student_id'],)).fetchone()
        conn.commit()
        conn.close()
        
        if student:
            send_participation_email(student['email'], session['student_name'])
        
        flash(f"Submission recorded in {time_taken} seconds. The AI will announce the winner at 10 PM!")
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('quiz.html', questions=questions)

# --- Admin Routes ---
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        passkey = request.form['passkey']
        if passkey == 'address@2026':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin passkey.')
    return render_template('admin_login.html')
    
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
        
    conn = get_db_connection()
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_attempts = conn.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]
    
    today = datetime.date.today().isoformat()
    # Check if the automated 10PM job already logged a winner
    winner = conn.execute('''
        SELECT s.name, s.phone, s.father_phone, w.answer_text, w.time_taken 
        FROM winners w 
        JOIN students s ON w.student_id = s.id 
        WHERE w.date = ? 
    ''', (today,)).fetchone()
    
    conn.close()
    return render_template('admin_dashboard.html', total_students=total_students, 
                           total_attempts=total_attempts, winner=winner,
                           sms_status=None, sms_success=False)

@app.route('/send_test_notifications', methods=['POST'])
def send_test_notifications():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    test_name  = request.form.get('test_name', 'Test Student').strip()
    test_email = request.form.get('test_email', '').strip()
    
    # Pass dummy performance metrics for the test email
    success = send_winner_notification(test_name, test_email, time_taken=42, answer_text="The bus driver's name is the same as the narrator's name!")
    
    conn = get_db_connection()
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_attempts = conn.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]
    today = datetime.date.today().isoformat()
    winner = conn.execute('''
        SELECT s.name, s.phone, s.father_phone, w.answer_text, w.time_taken 
        FROM winners w JOIN students s ON w.student_id = s.id WHERE w.date = ?
    ''', (today,)).fetchone()
    conn.close()

    sms_status = f"Congratulations Email dispatched to {test_email}! Check your inbox." if success else f"Email notification failed. Please check your .env settings (SMTP credentials)."
    return render_template('admin_dashboard.html', total_students=total_students,
                           total_attempts=total_attempts, winner=winner,
                           sms_status=sms_status, sms_success=success)

@app.route('/download_excel')
def download_excel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
        
    filename = generate_excel_report()
    return send_file(filename, as_attachment=True)

@app.route('/view_data')
def view_data():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students ORDER BY id DESC').fetchall()
    attempts = conn.execute('''
        SELECT a.id, s.name, q.date, a.answer_text, a.time_taken, a.date as attempt_date
        FROM attempts a
        JOIN students s ON a.student_id = s.id
        JOIN quizzes q ON a.quiz_id = q.id
        ORDER BY a.date DESC
    ''').fetchall()
    conn.close()
    return render_template('view_data.html', students=students, attempts=attempts)
    
@app.route('/trigger_eval_manual', methods=['POST'])
def trigger_eval_manual():
    # Admin manual bypass
    if not session.get('admin_logged_in'):
        return {}, 403
    
    select_daily_winner_job()
    flash("Manual AI evaluation triggered!")
    return redirect(url_for('admin_dashboard'))

def open_browser():
    """Automatically opens the QR display page in the default browser."""
    webbrowser.open_new("http://127.0.0.1:5000/qr")

if __name__ == '__main__':
    # Start a timer to open the browser after the server is up (1.5s delay)
    Timer(1.5, open_browser).start()
    
    # Host on 0.0.0.0 to securely expose port 5000 to the Local Area Network (Wi-Fi)
    app.run(host='0.0.0.0', debug=True, port=5000, use_reloader=False) # Important: Turn off reloader when using APScheduler to prevent double-firing jobs
