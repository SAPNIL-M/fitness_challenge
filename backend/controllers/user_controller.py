import sqlite3
from sqlite3 import IntegrityError

from fastapi import HTTPException, status

from models.schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    DashboardResponse,
    ActivityHistoryItem,
    SportBreakdown,
    PointsOverTime,
    SportType,
)
from services.auth_service import hash_password, verify_password, create_access_token


# ─── Registration ────────────────────────────────────────────

async def register_user(
    payload: UserRegisterRequest,
    db: sqlite3.Connection,
) -> UserRegisterResponse:
    """
    Register a new user in the database.

    Inserts a new row into the users table. The UNIQUE constraint
    on (firstName, lastName) in the database enforces duplicate
    prevention at the storage level — no separate lookup needed.
    The submitted password is hashed before it ever reaches the
    database; the plain-text version is never stored anywhere.

    Registration also immediately issues an access token, so the
    frontend can treat signing up as an automatic login — no separate
    login step required right after registering.

    Args:
        payload: Validated user registration data.
        db:      Scoped database connection from FastAPI dependency.

    Returns:
        UserRegisterResponse containing the new userId, a message,
        and a ready-to-use access token.

    Raises:
        HTTPException 409: If a user with the same first and last name
                           already exists.
        HTTPException 500: If any other database error occurs.
    """
    hashed_password: str = hash_password(payload.password)

    try:
        cursor = db.execute(
            """
            INSERT INTO users (firstName, lastName, email, password)
            VALUES (?, ?, ?, ?)
            """,
            (payload.firstName, payload.lastName, payload.email, hashed_password),
        )
        assert cursor.lastrowid is not None, "Insert succeeded but returned no row ID"
        new_user_id: int = cursor.lastrowid

        return UserRegisterResponse(
            userId=new_user_id,
            message=f"User '{payload.firstName} {payload.lastName}' registered successfully.",
            accessToken=create_access_token(new_user_id),
        )

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Duplicate user",
                "message": (
                    f"A user with the name '{payload.firstName} {payload.lastName}' "
                    "already exists."
                ),
            },
        )


# ─── Login ───────────────────────────────────────────────────

async def login_user(
    payload: UserLoginRequest,
    db: sqlite3.Connection,
) -> UserLoginResponse:
    """
    Verify a user's credentials and issue an access token.

    Looks the user up by firstName + lastName, then checks the
    submitted password against the stored bcrypt hash.

    Deliberately returns the exact same error, with the exact same
    message, whether the name doesn't exist at all or the password
    was wrong for a name that does exist. This prevents "username
    enumeration" — an attacker probing which names are registered by
    noticing a different error message for "no such user" versus
    "wrong password".

    Args:
        payload: Validated login credentials.
        db:      Scoped database connection from FastAPI dependency.

    Returns:
        UserLoginResponse containing the userId, name, and a fresh
        access token.

    Raises:
        HTTPException 401: If the name/password combination is invalid.
    """
    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "Invalid credentials",
            "message": "No account matches that name and password.",
        },
    )

    user_row = db.execute(
        "SELECT id, firstName, lastName, password FROM users WHERE firstName = ? AND lastName = ?",
        (payload.firstName, payload.lastName),
    ).fetchone()

    if user_row is None:
        raise invalid_credentials_error

    if not verify_password(payload.password, user_row["password"]):
        raise invalid_credentials_error

    full_name: str = f"{user_row['firstName']} {user_row['lastName']}"

    return UserLoginResponse(
        userId=user_row["id"],
        name=full_name,
        accessToken=create_access_token(user_row["id"]),
    )


# ─── Dashboard ───────────────────────────────────────────────

async def get_user_dashboard(
    user_id: int,
    db: sqlite3.Connection,
) -> DashboardResponse:
    """
    Retrieve all personal dashboard data for a single user.

    Fetches and assembles:
        - User identity (name)
        - Full activity history
        - Aggregate totals (total points, total activities)
        - Top sport by points contributed
        - Sport breakdown for the pie chart
        - Daily points aggregation for the line chart

    Args:
        user_id: The ID of the user whose dashboard is requested.
        db:      Scoped database connection from FastAPI dependency.

    Returns:
        DashboardResponse containing all dashboard data.

    Raises:
        HTTPException 404: If no user exists with the given user_id.
    """
    user_row = db.execute(
        "SELECT id, firstName, lastName FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User not found",
                "message": f"No user exists with id {user_id}.",
            },
        )

    full_name: str = f"{user_row['firstName']} {user_row['lastName']}"

    activity_rows = db.execute(
        """
        SELECT id, sport, metricType, metricValue, points, loggedAt
        FROM   activities
        WHERE  userId = ?
        ORDER  BY loggedAt DESC
        """,
        (user_id,),
    ).fetchall()

    activities: list[ActivityHistoryItem] = [
        ActivityHistoryItem(
            id=row["id"],
            sport=row["sport"],
            metricType=row["metricType"],
            metricValue=row["metricValue"],
            points=row["points"],
            loggedAt=row["loggedAt"],
        )
        for row in activity_rows
    ]

    total_points: int = sum(a.points for a in activities)
    total_activities: int = len(activities)

    sport_breakdown: list[SportBreakdown] = _build_sport_breakdown(
        activities,
        total_points,
    )

    top_sport: SportType | None = (
        sport_breakdown[0].sport if sport_breakdown else None
    )

    points_over_time: list[PointsOverTime] = _build_points_over_time(db, user_id)

    return DashboardResponse(
        userId=user_id,
        name=full_name,
        totalPoints=total_points,
        totalActivities=total_activities,
        topSport=top_sport,
        activities=activities,
        sportBreakdown=sport_breakdown,
        pointsOverTime=points_over_time,
    )


# ─── Private Helpers ─────────────────────────────────────────

def _build_sport_breakdown(
    activities: list[ActivityHistoryItem],
    total_points: int,
) -> list[SportBreakdown]:
    """
    Aggregate activity points by sport and calculate percentage share.

    Sorted by total points descending so the top sport is always first.
    Percentage is 0.0 if the user has no points to avoid division by zero.

    Args:
        activities:   Full list of the user's activity history items.
        total_points: The user's total accumulated points.

    Returns:
        List of SportBreakdown entries sorted by points descending.

    Example:
        activities with 550 running + 250 cycling out of 800 total:
        [
            SportBreakdown(sport="running",  totalPoints=550, percentage=68.75),
            SportBreakdown(sport="cycling",  totalPoints=250, percentage=31.25),
        ]
    """
    sport_totals: dict[str, int] = {}

    for activity in activities:
        sport_key = activity.sport.value
        sport_totals[sport_key] = sport_totals.get(sport_key, 0) + activity.points

    breakdown: list[SportBreakdown] = []

    for sport_key, points in sport_totals.items():
        percentage: float = (
            round((points / total_points) * 100, 2)
            if total_points > 0
            else 0.0
        )
        breakdown.append(
            SportBreakdown(
                sport=SportType(sport_key),
                totalPoints=points,
                percentage=percentage,
            )
        )

    breakdown.sort(key=lambda entry: entry.totalPoints, reverse=True)
    return breakdown


def _build_points_over_time(
    db: sqlite3.Connection,
    user_id: int,
) -> list[PointsOverTime]:
    """
    Aggregate a user's daily points for the line chart.

    Groups all activities by calendar date and sums points per day.
    Ordered chronologically so the line chart renders left-to-right.

    Uses SQLite's DATE() function to extract the date portion of
    the loggedAt timestamp, grouping multiple activities on the
    same day into a single data point.

    Args:
        db:      Scoped database connection.
        user_id: The user whose activity history is being aggregated.

    Returns:
        List of PointsOverTime entries ordered by date ascending.

    Example:
        [
            PointsOverTime(date="2024-01-15", points=550),
            PointsOverTime(date="2024-01-16", points=250),
            PointsOverTime(date="2024-01-17", points=225),
        ]
    """
    rows = db.execute(
        """
        SELECT   DATE(loggedAt) AS date,
                 SUM(points)    AS points
        FROM     activities
        WHERE    userId = ?
        GROUP BY DATE(loggedAt)
        ORDER BY DATE(loggedAt) ASC
        """,
        (user_id,),
    ).fetchall()

    return [
        PointsOverTime(
            date=row["date"],
            points=row["points"],
        )
        for row in rows
    ]