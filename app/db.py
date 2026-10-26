import sqlite3
from pathlib import Path

DB_PATH=Path(__file__).resolve().parent.parent / "edu.db"

def get_conn():
    conn=sqlite3.connect(DB_PATH)
    conn.row_factory=sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")   # SQLite 默认不开外键，每个连接都要开
    return conn

def init_db():
    conn=get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stu_id TEXT UNIQUE NOT NULL,
        stu_name TEXT NOT NULL,
        class_name TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cs_name TEXT NOT NULL,
        credit REAL,
        teacher TEXT
    );
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        score REAL CHECK (score IS NULL OR (score >= 0 AND score <= 100)),
        term TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (course_id) REFERENCES courses(id),
        UNIQUE (student_id, course_id, term)
    );
    """)
    conn.commit()
    conn.close()
