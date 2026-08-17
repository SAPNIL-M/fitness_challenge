import sqlite3
import os
from typing import Generator
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH: str = os.getenv("DATABASE_NAME", "fitness.db")


def get_connection() -> sqlite3.Connection:
    """
    Create and return a configured SQLite database connection.

    Configures:
        - Row factory for dict-like column access
        - Foreign key constraint enforcement
        - WAL journal mode for better concurrent read performance
        - check_same_thread disabled for FastAPI's async threading model
    """
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency that yields a scoped database connection per request.

    Automatically commits the transaction on success and rolls back on
    any exception. Always closes the connection when the request completes.

    Usage:
        async def endpoint(db: sqlite3.Connection = Depends(get_db)):
            ...
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize the database schema on application startup.

    Creates all required tables if they do not already exist.
    Safe to call on every server startup — existing data is never affected.

    Raises:
        RuntimeError: If table creation fails for any reason.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                firstName   TEXT NOT NULL,
                lastName    TEXT NOT NULL,
                email       TEXT,
                previousRank  INTEGER DEFAULT NULL,
                createdAt   DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(firstName, lastName)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                userId      INTEGER NOT NULL,
                sport       TEXT NOT NULL,
                metricType  TEXT NOT NULL,
                metricValue TEXT NOT NULL,
                points      INTEGER NOT NULL,
                loggedAt    DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userId) REFERENCES users(id)
            )
        """)

        conn.commit()

    except Exception as error:
        conn.rollback()
        raise RuntimeError(f"Failed to initialize database: {error}") from error

    finally:
        conn.close()

# if __name__ == "__main__":
#     print("Initializing database...")
#     init_db()
#     print("Success. Verifying tables...")

#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
#     tables = cursor.fetchall()
#     conn.close()

#     for table in tables:
#         print(f"  Table found: {table['name']}")