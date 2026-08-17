import sqlite3
from sqlite3 import IntegrityError

from fastapi import HTTPException, status

from models.schemas import (
    ActivityRequest,
    ActivityResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    TrendDirection,
)
from services.scoring_service import calculate_points


# ─── Activity Ingestion ──────────────────────────────────────

async def log_activity(
    payload: ActivityRequest,
    db: sqlite3.Connection,
) -> ActivityResponse:
    """
    Validate, score, and persist a new fitness activity.

    Workflow:
        1. Verify the userId exists in the database.
        2. Calculate points using the scoring service.
        3. Insert the activity with computed points into the database.
        4. Return the full activity response.

    Args:
        payload: Validated activity data from the request body.
        db:      Scoped database connection from FastAPI dependency.

    Returns:
        ActivityResponse with the assigned activityId and points awarded.

    Raises:
        HTTPException 404: If the userId does not exist.
        HTTPException 500: If the database insert fails unexpectedly.
    """
    user_exists = db.execute(
        "SELECT 1 FROM users WHERE id = ?",
        (payload.userId,),
    ).fetchone()

    if user_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User not found",
                "message": f"No user exists with id {payload.userId}.",
            },
        )

    points_awarded: int = calculate_points(
        sport=payload.sport,
        metric_value=payload.metricValue,
    )

    try:
        cursor = db.execute(
            """
            INSERT INTO activities (userId, sport, metricType, metricValue, points)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.userId,
                payload.sport.value,
                payload.metricType.value,
                payload.metricValue,
                points_awarded,
            ),
        )

        assert cursor.lastrowid is not None, "Insert succeeded but returned no row ID"
        new_activity_id: int = cursor.lastrowid

    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Database error",
                "message": "Failed to log activity. Please try again.",
            },
        ) from error

    logged_activity = db.execute(
        """
        SELECT id, sport, metricType, metricValue, points, loggedAt
        FROM   activities
        WHERE  id = ?
        """,
        (new_activity_id,),
    ).fetchone()

    return ActivityResponse(
        activityId=logged_activity["id"],
        pointsAwarded=logged_activity["points"],
        sport=logged_activity["sport"],
        metricType=logged_activity["metricType"],
        metricValue=logged_activity["metricValue"],
        loggedAt=logged_activity["loggedAt"],
    )


# ─── Leaderboard ─────────────────────────────────────────────

async def get_leaderboard(
    db: sqlite3.Connection,
) -> LeaderboardResponse:
    """
    Compute and return the current global leaderboard.

    Ranking is determined by total accumulated points across all
    activities. Tie-breaking uses earliest registration date —
    the user who reached that score first ranks higher.

    Trend is determined by comparing each user's current rank
    against their previously stored rank. The previous rank is
    updated in the database after every leaderboard fetch.

    Args:
        db: Scoped database connection from FastAPI dependency.

    Returns:
        LeaderboardResponse with ranked entries and total user count.
    """
    ranked_rows = db.execute(
        """
        SELECT
            u.id                                        AS userId,
            u.firstName || ' ' || u.lastName           AS name,
            u.previousRank                              AS previousRank,
            COALESCE(SUM(a.points), 0)                 AS totalPoints
        FROM       users u
        LEFT JOIN  activities a ON a.userId = u.id
        GROUP BY   u.id, u.firstName, u.lastName, u.previousRank
        HAVING     COALESCE(SUM(a.points), 0) > 0
        ORDER BY   totalPoints DESC, u.createdAt ASC
        """,
    ).fetchall()

    total_users: int = len(ranked_rows)
    entries: list[LeaderboardEntry] = []

    for current_rank, row in enumerate(ranked_rows, start=1):
        previous_rank: int | None = row["previousRank"]
        trend: TrendDirection = _calculate_trend(current_rank, previous_rank)

        entries.append(
            LeaderboardEntry(
                rank=current_rank,
                userId=row["userId"],
                name=row["name"],
                totalPoints=row["totalPoints"],
                trend=trend,
            )
        )

    _update_previous_ranks(db, entries)

    return LeaderboardResponse(
        leaderboard=entries,
        totalUsers=total_users,
    )


# ─── Private Helpers ─────────────────────────────────────────

def _calculate_trend(
    current_rank: int,
    previous_rank: int | None,
) -> TrendDirection:
    """
    Determine the rank trend direction for a leaderboard entry.

    A user with no previous rank (first time on leaderboard) is
    treated as SAME since there is no meaningful comparison yet.

    Args:
        current_rank:  The user's rank in the current fetch.
        previous_rank: The user's rank from the last fetch, or None
                       if this is their first appearance.

    Returns:
        TrendDirection enum value — UP, DOWN, or SAME.

    Examples:
        current=1, previous=3  → UP   (rank number decreased)
        current=3, previous=1  → DOWN (rank number increased)
        current=2, previous=2  → SAME
        current=1, previous=None → SAME (first appearance)
    """
    if previous_rank is None:
        return TrendDirection.SAME
    if current_rank < previous_rank:
        return TrendDirection.UP
    if current_rank > previous_rank:
        return TrendDirection.DOWN
    return TrendDirection.SAME


def _update_previous_ranks(
    db: sqlite3.Connection,
    entries: list[LeaderboardEntry],
) -> None:
    """
    Persist each user's current rank as their previousRank.

    Called at the end of every leaderboard fetch so the next
    fetch can calculate trend direction accurately.

    Args:
        db:      Scoped database connection.
        entries: The freshly computed leaderboard entries.
    """
    db.executemany(
        "UPDATE users SET previousRank = ? WHERE id = ?",
        [(entry.rank, entry.userId) for entry in entries],
    )