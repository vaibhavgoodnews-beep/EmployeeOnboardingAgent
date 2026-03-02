from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

DB_PATH = Path(__file__).resolve().parent.parent / "onboarding.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_database() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS Employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        joining_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending'
    );

    CREATE TABLE IF NOT EXISTS Projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        client TEXT NOT NULL,
        description TEXT,
        tech_stack TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        status TEXT NOT NULL DEFAULT 'Active'
    );

    CREATE TABLE IF NOT EXISTS EmployeeProjects (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        assigned_on TEXT NOT NULL,
        role_on_project TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active',
        FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
        FOREIGN KEY (project_id) REFERENCES Projects(project_id)
    );

    CREATE TABLE IF NOT EXISTS Skills (
        skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        proficiency INTEGER NOT NULL CHECK (proficiency BETWEEN 1 AND 5),
        last_updated TEXT NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
    );

    CREATE TABLE IF NOT EXISTS Assessments (
        assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        summary TEXT,
        FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
        FOREIGN KEY (project_id) REFERENCES Projects(project_id)
    );

    CREATE TABLE IF NOT EXISTS AssessmentQuestions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        expected_topics TEXT,
        FOREIGN KEY (assessment_id) REFERENCES Assessments(assessment_id)
    );

    CREATE TABLE IF NOT EXISTS AssessmentAnswers (
        answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        answer_text TEXT NOT NULL,
        score REAL,
        evaluated_at TEXT,
        FOREIGN KEY (question_id) REFERENCES AssessmentQuestions(question_id),
        FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
    );

    CREATE TABLE IF NOT EXISTS Recommendations (
        recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        recommendation_text TEXT NOT NULL,
        certifications TEXT,
        courses TEXT,
        created_at TEXT NOT NULL,
        reflection_notes TEXT,
        FOREIGN KEY (assessment_id) REFERENCES Assessments(assessment_id),
        FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
        FOREIGN KEY (project_id) REFERENCES Projects(project_id)
    );

    CREATE TABLE IF NOT EXISTS AuditLogs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        action TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        employee_id INTEGER,
        project_id INTEGER,
        metadata TEXT
    );
    """
    with get_connection() as conn:
        conn.executescript(schema)
        conn.commit()


def execute_read(query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def execute_write(query: str, params: Iterable[Any] = (), many: bool = False) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        if many:
            cursor.executemany(query, params)  # type: ignore[arg-type]
            conn.commit()
            return cursor.rowcount

        cursor.execute(query, tuple(params))
        conn.commit()
        return int(cursor.lastrowid)
