# AI Student Quiz Hub - Project Documentation

## 📌 1. Overview
The **AI Student Quiz Hub** is a dynamic web application built for the **Kakinada Institute of Technology and Engineering**. Its primary function is to host a daily AI-generated quiz, utilizing a local Large Language Model (Ollama), to challenge and assess students. 

The application features full student registration workflows, interactive timer-based quiz evaluations, an Administrator dashboard for tracking student metrics, Excel data exporting, and SMS notifications for daily winners.

## ⚙️ 2. Technology Stack
- **Frontend Layer:** HTML5, vanilla CSS3 (Premium Glassmorphism Aesthetic), vanilla JavaScript.
- **Backend Framework:** Python (Flask).
- **Database:** SQLite (Relational, embedded).
- **AI Engine:** Local `Ollama` running the `llama3` model.
- **Data Export:** Python `openpyxl`.
- **SMS Integration:** Twilio API.

## 📁 3. Project Structure
The source code is modularly separated to cleanly handle database I/O, AI prompting, and routing.

```text
/intermediate/
├── app.py                 # Core routing engine (Flask view functions)
├── database.py            # SQLite schema definitions & connection logic
├── ai_quiz.py             # Ollama interface & prompt tuning (creates logic riddles)
├── notifier.py            # Twilio SMS API initialization and broadcast logic
├── export_excel.py        # openpyxl engine to dump SQLite joins to Excel
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

## 🧠 5. AI Integration details (Ollama)
The application avoids generic multiple-choice questions. In `ai_quiz.py`, the AI Prompt is strictly tuned to demand:
- **Exactly 1 question**.
- **Tricky Logic Puzzles / Riddles** formatted identically to an example prompt.
- **JSON structured output**.

*Fallback safety measure:* If the local Ollama daemon is offline, the app defaults to supplying a hard-coded backup riddle so the server continues running uninterrupted.

## 📲 6. Third-Party Integrations
### Twilio (SMS Notifications)
Located in `notifier.py`. Administrators trigger the daily broadcast targeting the highest scorer. 
**Required Adjustments for Production:** Developer needs to configure their respective standard `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and Sender Phone directly within the module strings or environment variables.

### YouTube Background
Located in `templates/base.html`. The video operates using a mute/loop iframe bypass, acting as a dynamic background layer utilizing the `-100` CSS `z-index`.

## 🚀 7. Installation and Execution

1. **Pre-Requisite Check**: 
   Ensure `Python 3.10+` and `Ollama` are installed locally. In your terminal, run `ollama serve` and ensure you have pulled a base model using `ollama pull llama3`.
2. **First Run Setup / Launching**:
   Locate the root directory. Double-click the **`run.bat`** file.
   - The script creates a `.venv` (Virtual Environment).
   - Installs `requirements.txt`.
   - Starts the `app.py` server.
3. Access the portal at **`http://127.0.0.1:5000`**

### Administrative Access:
To access the metrics panel via `http://127.0.0.1:5000/admin_login`:
- **Admin System Passkey:** `address@2026`
