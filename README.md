# AI Student Quiz Hub - Project Documentation

## 📌 1. Overview
The **AI Student Quiz Hub** is a Flask web application built for the **Kakinada Institute of Technology and Engineering**. It hosts a daily AI-generated logic quiz, captures student submissions, and lets admins export results and announce winners.

Key production changes:
- Secrets now come from environment variables (`SECRET_KEY`, `ADMIN_PASSKEY`, `DATABASE_URL`, SMTP, Hugging Face token).
- Passwords are hashed using Werkzeug; admin passkey is no longer hard-coded.
- CSRF protection is enabled via Flask-WTF on all POST forms.
- Database supports Turso (libsql) or local SQLite fallback via `DATABASE_URL`.

## ⚙️ 2. Technology Stack
- **Frontend:** HTML5, vanilla CSS, vanilla JS.
- **Backend:** Python Flask.
- **Database:** Turso (libsql) or SQLite (default for local/dev).
- **AI Engine:** Hugging Face Inference (`HuggingFaceH4/zephyr-7b-beta`).
- **Data Export:** Python `openpyxl`.
- **Email:** SMTP (Twilio/WhatsApp optional, not wired by default).

## 📁 3. Project Structure
The source code is modularly separated to cleanly handle database I/O, AI prompting, and routing.

```text
/intermediate/
├── app.py                 # Core routing engine (Flask view functions, CSRF, auth)
├── database.py            # DB schema + connection (Turso libsql or SQLite fallback)
├── ai_quiz.py             # Hugging Face API prompt to create logic riddles
├── notifier.py            # SMTP email helpers (optional Twilio/WhatsApp placeholders)
├── export_excel.py        # openpyxl engine to dump DB joins to Excel
├── requirements.txt       # Python dependency list
├── run.bat                # Automated Windows startup and venv script
├── static/
│   └── css/
│       └── styles.css     # Universal stylesheet (handles Video Background sizing)
└── templates/
    ├── base.html          # Jinja2 Layout template (houses YouTube iframe)
    ├── index.html         # Landing page
    ├── register.html      # Secure student data input form
    ├── login.html         # Student authentication portal
    ├── dashboard.html     # Secure portal with evaluation stats & external links
    ├── quiz.html          # Interactive puzzle UI with JS Countdown Timer
    ├── admin_login.html   # Faculty login portal
    └── admin_dashboard.html # Admin Control Panel (Export & Winner SMS triggers)
```

## 🗄️ 4. Database Schema (`quiz_app.db`)
The schema consists of 4 main tables interconnected by standard foreign keys:

- **`students`**: Stores identity (id, name, phone, father_name, father_phone, college_location, inter_college, school, eamcet_reg, address, email, password).
- **`quizzes`**: Caches the AI-generated JSON per day (id, date, questions_json). Ensures identical questions across all users on the same calendar date.
- **`attempts`**: Records student quiz actions (id, student_id, quiz_id, score, time_taken, date).
- **`winners`**: Tracks daily leaderboard top scores.

## 🧠 5. AI Integration details (Hugging Face)
`ai_quiz.py` calls the Hugging Face Inference API (`HuggingFaceH4/zephyr-7b-beta`) via `HUGGINGFACE_API_KEY` to generate exactly one logic riddle and to adjudicate winners. If the API fails, a hard-coded fallback riddle is used.

## 📲 6. Third-Party Integrations
- **SMTP Email** (`notifier.py`): set `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_FROM`.
- **WhatsApp / Twilio**: placeholders only; wire up credentials before use.
- **YouTube Background**: configured in `templates/base.html`.

## 🚀 7. Configuration
Create `.env` in `intermediate/` (see `.example.env` for placeholders):

```env
SECRET_KEY=change-me
ADMIN_PASSKEY=change-me-too
DATABASE_URL=sqlite:///quiz_app.db  # or libsql://your-turso-host.turso.io
HUGGINGFACE_API_KEY=your-hf-token
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@example.com
EMAIL_PASS=your-app-password
EMAIL_FROM="KIET AI Quiz Hub"
RUN_SCHEDULER=1
```

## ▶️ 8. Local Development
1) `cd intermediate`
2) `python -m venv .venv && .venv\Scripts\activate`
3) `pip install -r requirements.txt`
4) `python app.py`

Access the portal at `http://127.0.0.1:5000`. Admin login uses `ADMIN_PASSKEY` from env (no hard-coded default).

## ☁️ 9. Deployment Notes
- **Gunicorn**: Container/Render/Fly run `gunicorn --bind 0.0.0.0:$PORT app:app`. Keep `RUN_SCHEDULER=1` in single-worker setups only.
- **Database**: For SQLite, point `DATABASE_URL` to a persistent volume path (e.g., `sqlite:////data/quiz_app.db`). For Turso, set `DATABASE_URL=libsql://...` and `TURSO_AUTH_TOKEN`.
- **Env files**: Never commit real secrets; `.gitignore` excludes `.env` and generated data.
