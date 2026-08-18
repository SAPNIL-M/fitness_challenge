import sys
import sqlite3
from datetime import datetime, timedelta

from database import get_connection, init_db
from services.scoring_service import calculate_points
from services.auth_service import hash_password
from models.schemas import SportType

# Every seed user gets this same password, purely for local demo/testing
# convenience — e.g. login as Alice Johnson with this password to see
# the "Add Activity" button and full authenticated experience.
SEED_PASSWORD: str = "Password123!"


# ─── Seed Data ───────────────────────────────────────────────

USERS: list[dict] = [
    {"firstName": "Alice",   "lastName": "Johnson",   "email": "alice@email.com"},
    {"firstName": "Bob",     "lastName": "Smith",     "email": "bob@email.com"},
    {"firstName": "Carol",   "lastName": "Williams",  "email": "carol@email.com"},
    {"firstName": "David",   "lastName": "Brown",     "email": "david@email.com"},
    {"firstName": "Emma",    "lastName": "Davis",     "email": "emma@email.com"},
    {"firstName": "Frank",   "lastName": "Miller",    "email": "frank@email.com"},
    {"firstName": "Grace",   "lastName": "Wilson",    "email": "grace@email.com"},
    {"firstName": "Henry",   "lastName": "Moore",     "email": "henry@email.com"},
]

ACTIVITIES: list[dict] = [
    # Alice — competitive runner and cyclist, clear rank 1
    {"userId": 1, "sport": "running",  "metricType": "distance", "metricValue": "10.0",  "daysAgo": 14},
    {"userId": 1, "sport": "running",  "metricType": "distance", "metricValue": "5.5",   "daysAgo": 12},
    {"userId": 1, "sport": "cycling",  "metricType": "distance", "metricValue": "25.0",  "daysAgo": 10},
    {"userId": 1, "sport": "running",  "metricType": "distance", "metricValue": "8.0",   "daysAgo": 7},
    {"userId": 1, "sport": "cycling",  "metricType": "distance", "metricValue": "15.0",  "daysAgo": 5},
    {"userId": 1, "sport": "steps",    "metricType": "count",    "metricValue": "12000", "daysAgo": 3},
    {"userId": 1, "sport": "running",  "metricType": "distance", "metricValue": "6.0",   "daysAgo": 1},

    # Bob — gym enthusiast, good volume
    {"userId": 2, "sport": "gym",      "metricType": "duration", "metricValue": "60:00", "daysAgo": 13},
    {"userId": 2, "sport": "gym",      "metricType": "duration", "metricValue": "45:00", "daysAgo": 11},
    {"userId": 2, "sport": "walking",  "metricType": "distance", "metricValue": "5.0",   "daysAgo": 9},
    {"userId": 2, "sport": "gym",      "metricType": "duration", "metricValue": "75:00", "daysAgo": 7},
    {"userId": 2, "sport": "steps",    "metricType": "count",    "metricValue": "9500",  "daysAgo": 5},
    {"userId": 2, "sport": "gym",      "metricType": "duration", "metricValue": "60:00", "daysAgo": 3},
    {"userId": 2, "sport": "walking",  "metricType": "distance", "metricValue": "3.0",   "daysAgo": 1},

    # Carol — swimmer and runner mix
    {"userId": 3, "sport": "swimming", "metricType": "duration", "metricValue": "30:00", "daysAgo": 14},
    {"userId": 3, "sport": "running",  "metricType": "distance", "metricValue": "5.0",   "daysAgo": 12},
    {"userId": 3, "sport": "swimming", "metricType": "duration", "metricValue": "45:00", "daysAgo": 10},
    {"userId": 3, "sport": "running",  "metricType": "distance", "metricValue": "7.0",   "daysAgo": 8},
    {"userId": 3, "sport": "swimming", "metricType": "duration", "metricValue": "60:00", "daysAgo": 6},
    {"userId": 3, "sport": "steps",    "metricType": "count",    "metricValue": "8000",  "daysAgo": 4},
    {"userId": 3, "sport": "running",  "metricType": "distance", "metricValue": "4.0",   "daysAgo": 2},

    # David — heavy cyclist
    {"userId": 4, "sport": "cycling",  "metricType": "distance", "metricValue": "30.0",  "daysAgo": 13},
    {"userId": 4, "sport": "cycling",  "metricType": "distance", "metricValue": "20.0",  "daysAgo": 10},
    {"userId": 4, "sport": "walking",  "metricType": "distance", "metricValue": "4.0",   "daysAgo": 8},
    {"userId": 4, "sport": "cycling",  "metricType": "distance", "metricValue": "35.0",  "daysAgo": 5},
    {"userId": 4, "sport": "steps",    "metricType": "count",    "metricValue": "7500",  "daysAgo": 3},
    {"userId": 4, "sport": "cycling",  "metricType": "distance", "metricValue": "25.0",  "daysAgo": 1},

    # Emma — all rounder
    {"userId": 5, "sport": "running",  "metricType": "distance", "metricValue": "4.0",   "daysAgo": 14},
    {"userId": 5, "sport": "swimming", "metricType": "duration", "metricValue": "30:00", "daysAgo": 12},
    {"userId": 5, "sport": "gym",      "metricType": "duration", "metricValue": "45:00", "daysAgo": 10},
    {"userId": 5, "sport": "cycling",  "metricType": "distance", "metricValue": "10.0",  "daysAgo": 8},
    {"userId": 5, "sport": "walking",  "metricType": "distance", "metricValue": "3.0",   "daysAgo": 6},
    {"userId": 5, "sport": "steps",    "metricType": "count",    "metricValue": "6000",  "daysAgo": 4},
    {"userId": 5, "sport": "running",  "metricType": "distance", "metricValue": "3.0",   "daysAgo": 2},

    # Frank — walker and steps focused
    {"userId": 6, "sport": "walking",  "metricType": "distance", "metricValue": "6.0",   "daysAgo": 13},
    {"userId": 6, "sport": "steps",    "metricType": "count",    "metricValue": "11000", "daysAgo": 11},
    {"userId": 6, "sport": "walking",  "metricType": "distance", "metricValue": "4.5",   "daysAgo": 9},
    {"userId": 6, "sport": "steps",    "metricType": "count",    "metricValue": "9000",  "daysAgo": 7},
    {"userId": 6, "sport": "walking",  "metricType": "distance", "metricValue": "5.0",   "daysAgo": 5},
    {"userId": 6, "sport": "gym",      "metricType": "duration", "metricValue": "30:00", "daysAgo": 3},
    {"userId": 6, "sport": "steps",    "metricType": "count",    "metricValue": "8500",  "daysAgo": 1},

    # Grace — occasional user, lower on leaderboard
    {"userId": 7, "sport": "running",  "metricType": "distance", "metricValue": "3.0",   "daysAgo": 10},
    {"userId": 7, "sport": "walking",  "metricType": "distance", "metricValue": "2.0",   "daysAgo": 7},
    {"userId": 7, "sport": "steps",    "metricType": "count",    "metricValue": "5000",  "daysAgo": 4},
    {"userId": 7, "sport": "gym",      "metricType": "duration", "metricValue": "20:00", "daysAgo": 2},

    # Henry — just started, lowest on leaderboard
    {"userId": 8, "sport": "walking",  "metricType": "distance", "metricValue": "2.0",   "daysAgo": 5},
    {"userId": 8, "sport": "steps",    "metricType": "count",    "metricValue": "4000",  "daysAgo": 3},
    {"userId": 8, "sport": "gym",      "metricType": "duration", "metricValue": "15:00", "daysAgo": 1},
]


# ─── Helpers ─────────────────────────────────────────────────

def _clear_existing_data(conn: sqlite3.Connection) -> None:
    """
    Wipe all existing data before seeding.

    Deletes in the correct order to respect foreign key constraints —
    activities must be deleted before users since activities reference users.
    Resets the auto-increment sequence so IDs start from 1.
    """
    conn.execute("DELETE FROM activities")
    conn.execute("DELETE FROM users")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'activities')")
    conn.commit()
    print("  Cleared existing data")


def _seed_users(conn: sqlite3.Connection) -> None:
    """
    Insert all seed users into the database.

    Every seed user is given the same hashed SEED_PASSWORD so they can
    all be logged into locally for testing — hashed the same way real
    registrations are, via the same auth_service used by the API.
    """
    hashed_password: str = hash_password(SEED_PASSWORD)

    conn.executemany(
        "INSERT INTO users (firstName, lastName, email, password) VALUES (?, ?, ?, ?)",
        [(u["firstName"], u["lastName"], u["email"], hashed_password) for u in USERS],
    )
    conn.commit()
    print(f"  Inserted {len(USERS)} users (password for all: '{SEED_PASSWORD}')")


def _seed_activities(conn: sqlite3.Connection) -> None:
    """
    Insert all seed activities with computed points and realistic timestamps.

    Each activity's loggedAt is calculated by subtracting daysAgo
    from the current date, giving the leaderboard a realistic time spread
    for the points-over-time line chart.
    """
    now = datetime.now()
    inserted_count: int = 0

    for activity in ACTIVITIES:
        points: int = calculate_points(
            sport=SportType(activity["sport"]),
            metric_value=activity["metricValue"],
        )

        logged_at = now - timedelta(days=activity["daysAgo"])

        conn.execute(
            """
            INSERT INTO activities
                (userId, sport, metricType, metricValue, points, loggedAt)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                activity["userId"],
                activity["sport"],
                activity["metricType"],
                activity["metricValue"],
                points,
                logged_at.strftime("%Y-%m-%dT%H:%M:%S"),
            ),
        )
        inserted_count += 1

    conn.commit()
    print(f"  Inserted {inserted_count} activities")


def _print_leaderboard_preview(conn: sqlite3.Connection) -> None:
    """
    Print a preview of the leaderboard after seeding so we can
    visually verify the data looks correct in the terminal.
    """
    rows = conn.execute(
        """
        SELECT
            u.firstName || ' ' || u.lastName AS name,
            COALESCE(SUM(a.points), 0)        AS totalPoints,
            COUNT(a.id)                       AS totalActivities
        FROM      users u
        LEFT JOIN activities a ON a.userId = u.id
        GROUP BY  u.id
        ORDER BY  totalPoints DESC
        """
    ).fetchall()

    print()
    print("  Leaderboard preview:")
    print("  " + "─" * 45)
    print(f"  {'Rank':<6} {'Name':<20} {'Points':>8} {'Activities':>10}")
    print("  " + "─" * 45)

    for rank, row in enumerate(rows, start=1):
        print(
            f"  {rank:<6} "
            f"{row['name']:<20} "
            f"{row['totalPoints']:>8} "
            f"{row['totalActivities']:>10}"
        )

    print("  " + "─" * 45)


# ─── Entry Point ─────────────────────────────────────────────

def run_seed() -> None:
    """
    Main seed function — initializes the database and populates
    it with realistic sample data.

    Safe to run multiple times — clears existing data first.
    """
    print()
    print("Starting database seed...")
    print()

    init_db()
    conn = get_connection()

    try:
        _clear_existing_data(conn)
        _seed_users(conn)
        _seed_activities(conn)
        _print_leaderboard_preview(conn)

        print()
        print("Seed completed successfully.")
        print("You can now start the server with: python main.py")
        print()

    except Exception as error:
        conn.rollback()
        print(f"Seed failed: {error}")
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    run_seed()