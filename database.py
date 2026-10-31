
import sqlite3

DB_NAME = "learning_coach.db"


def get_connection():
    """Create a database connection with dictionary-like rows."""
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create tables and safely add the learner name to older databases."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS learners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                subject TEXT NOT NULL,
                goal TEXT NOT NULL,
                current_level TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                daily_minutes INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Upgrade an existing database without deleting saved records.
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(learners)"
            ).fetchall()
        }

        if "name" not in columns:
            connection.execute("""
                ALTER TABLE learners
                ADD COLUMN name TEXT NOT NULL DEFAULT ''
            """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS learning_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id INTEGER NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (learner_id)
                    REFERENCES learners(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                answers_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (learner_id)
                    REFERENCES learners(id)
                    ON DELETE CASCADE
            )
        """)


def save_learner(
    subject,
    goal,
    current_level,
    duration_days,
    daily_minutes,
    name="",
):
    """Create a learner profile and return its ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO learners (
                name,
                subject,
                goal,
                current_level,
                duration_days,
                daily_minutes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                subject,
                goal,
                current_level,
                duration_days,
                daily_minutes,
            ),
        )
        return cursor.lastrowid


def update_learner(
    learner_id,
    subject,
    goal,
    current_level,
    duration_days,
    daily_minutes,
    name=None,
):
    """Update an existing profile without creating a duplicate."""
    with get_connection() as connection:
        if name is None:
            cursor = connection.execute(
                """
                UPDATE learners
                SET subject = ?,
                    goal = ?,
                    current_level = ?,
                    duration_days = ?,
                    daily_minutes = ?
                WHERE id = ?
                """,
                (
                    subject,
                    goal,
                    current_level,
                    duration_days,
                    daily_minutes,
                    learner_id,
                ),
            )
        else:
            cursor = connection.execute(
                """
                UPDATE learners
                SET name = ?,
                    subject = ?,
                    goal = ?,
                    current_level = ?,
                    duration_days = ?,
                    daily_minutes = ?
                WHERE id = ?
                """,
                (
                    name.strip(),
                    subject,
                    goal,
                    current_level,
                    duration_days,
                    daily_minutes,
                    learner_id,
                ),
            )

        return cursor.rowcount > 0


def get_learner(learner_id):
    """Return one learner profile or None."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM learners WHERE id = ?",
            (learner_id,),
        ).fetchone()

        return dict(row) if row else None


def get_learners():
    """Return all learner profiles, newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM learners ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]


def save_learning_plan(learner_id, plan_json):
    """Save a learning plan and return its ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO learning_plans (learner_id, plan_json)
            VALUES (?, ?)
            """,
            (learner_id, plan_json),
        )
        return cursor.lastrowid


def get_learning_plans(learner_id):
    """Return a learner's saved plans, newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM learning_plans
            WHERE learner_id = ?
            ORDER BY id DESC
            """,
            (learner_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def save_quiz_attempt(
    learner_id,
    topic,
    score,
    total_questions,
    answers_json,
):
    """Save a quiz result and return its ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO quiz_attempts (
                learner_id,
                topic,
                score,
                total_questions,
                answers_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                learner_id,
                topic,
                score,
                total_questions,
                answers_json,
            ),
        )
        return cursor.lastrowid


def get_quiz_attempts(learner_id):
    """Return a learner's quiz attempts, newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM quiz_attempts
            WHERE learner_id = ?
            ORDER BY id DESC
            """,
            (learner_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_topic_attempts(learner_id, topic):
    """Return attempts for a topic, ignoring capitalization."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM quiz_attempts
            WHERE learner_id = ?
              AND LOWER(topic) = LOWER(?)
            ORDER BY id DESC
            """,
            (learner_id, topic),
        ).fetchall()

        return [dict(row) for row in rows]
