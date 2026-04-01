import os
import sqlite3
from urllib.parse import urlparse

try:
    import libsql as libsql
except ImportError:
    libsql = None
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "quiz_app.db")

# Prefer DATABASE_URL, fall back to legacy TURSO_DATABASE_URL or local SQLite
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TURSO_DATABASE_URL")
if not DATABASE_URL:
    database_path = os.getenv("DATABASE_PATH", DEFAULT_SQLITE_PATH)
    DATABASE_URL = f"sqlite:///{database_path}"

TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

class RowWrapper:
    def __init__(self, cols, row):
        self.row = row
        self.d = dict(zip(cols, row))
        
    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.row[key]
        return self.d[key]
        
    def keys(self):
        return self.d.keys()

class DictCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        
    def execute(self, *args, **kwargs):
        self.cursor.execute(*args, **kwargs)
        return self
        
    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None: return None
        cols = [col[0] for col in self.cursor.description]
        return RowWrapper(cols, row)
        
    def fetchall(self):
        rows = self.cursor.fetchall()
        cols = [col[0] for col in self.cursor.description]
        return [RowWrapper(cols, row) for row in rows]
        
    def close(self):
        pass

class DictConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn
        
    def execute(self, *args, **kwargs):
        cursor = DictCursorWrapper(self.conn.cursor())
        return cursor.execute(*args, **kwargs)
        
    def cursor(self):
        return DictCursorWrapper(self.conn.cursor())
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        self.conn.close()

def get_db_connection():
    """Connect to the configured database (libsql:// for Turso, sqlite:/// for local)."""
    if DATABASE_URL.startswith("libsql://"):
        if libsql is None:
            raise ImportError("libsql is not installed. Install libsql-experimental when using a Turso DATABASE_URL.")
        conn_kwargs = {}
        if TURSO_AUTH_TOKEN:
            conn_kwargs['auth_token'] = TURSO_AUTH_TOKEN
        conn = libsql.connect(DATABASE_URL, **conn_kwargs)
        return DictConnectionWrapper(conn)

    if DATABASE_URL.startswith("sqlite"):
        parsed = urlparse(DATABASE_URL)
        path = parsed.path or DEFAULT_SQLITE_PATH
        if path.startswith("//"):
            # urlparse keeps absolute paths as //absolute; drop one slash
            path = path[1:]
        if not path:
            path = DEFAULT_SQLITE_PATH
        if not os.path.isabs(path):
            path = os.path.join(BASE_DIR, path.lstrip('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

    raise ValueError(f"Unsupported DATABASE_URL scheme: {DATABASE_URL}")

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Students Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            father_name TEXT NOT NULL,
            father_phone TEXT NOT NULL,
            college_location TEXT NOT NULL,
            inter_college TEXT NOT NULL,
            school TEXT NOT NULL,
            eamcet_reg TEXT NOT NULL,
            address TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Quizzes Table (Daily AI Quizzes)
    c.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            questions_json TEXT NOT NULL
        )
    ''')

    # Attempts Table (Scores and Time)
    c.execute('''
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            quiz_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            time_taken INTEGER NOT NULL, -- structured as seconds
            date TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        )
    ''')

    # Winners Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS winners (
            date TEXT PRIMARY KEY,
            student_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            time_taken INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
