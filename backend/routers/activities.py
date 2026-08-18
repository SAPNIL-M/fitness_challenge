import sqlite3

from fastapi import APIRouter, Depends, status

from controllers.activity_controller import log_activity, get_leaderboard
from database import get_db
from dependencies import get_current_user_id
from models.schemas import (
    ActivityRequest,
    ActivityResponse,
    LeaderboardResponse,
    ErrorResponse,
)

router = APIRouter()


# ─── Activity Logging ────────────────────────────────────────

@router.post(
    "",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid access token"},
        422: {"description": "Validation error — invalid request body"},
    },
    summary="Log a fitness activity",
    description=(
        "Ingests a new fitness activity for the authenticated user. "
        "Requires a valid Authorization: Bearer <token> header — the "
        "activity is always attributed to whichever user the token "
        "verifies as, never to a client-supplied id. Validates the "
        "sport and metric type combination, calculates points using "
        "the scoring engine, and persists the activity."
    ),
)
async def log_activity_route(
    payload: ActivityRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db),
) -> ActivityResponse:
    """
    POST /api/activities

    Accepts a JSON body with sport, metricType, and metricValue, plus
    a Bearer token identifying the caller. Delegates all business
    logic to the activity controller.
    """
    return await log_activity(payload, current_user_id, db)


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