import sqlite3

from fastapi import APIRouter, Depends, status

from controllers.activity_controller import log_activity, get_leaderboard
from database import get_db
from models.schemas import (
    ActivityRequest,
    ActivityResponse,
    LeaderboardResponse,
    ErrorResponse,
)

router = APIRouter()


# ─── Activity Logging ────────────────────────────────────────

@router.post(
    "/",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        400: {"model": ErrorResponse, "description": "Invalid request body or mismatched sport/metric combination"},
    },
    summary="Log a fitness activity",
    description=(
        "Ingests a new fitness activity for a registered user. "
        "Validates the sport and metric type combination, calculates "
        "points using the scoring engine, and persists the activity. "
        "Returns the awarded points immediately."
    ),
)
async def log_activity_route(
    payload: ActivityRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> ActivityResponse:
    """
    POST /api/activities

    Accepts a JSON body with userId, sport, metricType, and metricValue.
    Delegates all business logic to the activity controller.
    """
    return await log_activity(payload, db)


# ─── Leaderboard ─────────────────────────────────────────────

@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ErrorResponse, "description": "Database error"},
    },
    summary="Get global leaderboard",
    description=(
        "Returns the current global leaderboard ranked by total "
        "accumulated points. Tie-breaking uses earliest registration "
        "date. Only users with at least one logged activity appear. "
        "Rank trends are calculated against the previous fetch."
    ),
)
async def get_leaderboard_route(
    db: sqlite3.Connection = Depends(get_db),
) -> LeaderboardResponse:
    """
    GET /api/activities/leaderboard

    Returns ranked leaderboard entries with trend direction.
    Delegates all business logic to the activity controller.
    """
    return await get_leaderboard(db)