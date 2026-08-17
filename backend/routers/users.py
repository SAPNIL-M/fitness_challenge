import sqlite3

from fastapi import APIRouter, Depends, status

from controllers.user_controller import register_user, get_user_dashboard
from database import get_db
from models.schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    DashboardResponse,
    ErrorResponse,
)

router = APIRouter()


# ─── Registration ────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "User already exists"},
        400: {"model": ErrorResponse, "description": "Invalid request body"},
    },
    summary="Register a new user",
    description=(
        "Creates a new user account. "
        "Returns a unique userId on success. "
        "Rejects duplicate first and last name combinations with 409."
    ),
)
async def register_user_route(
    payload: UserRegisterRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> UserRegisterResponse:
    """
    POST /api/users/register

    Accepts a JSON body with firstName, lastName, and optional email.
    Delegates all business logic to the user controller.
    """
    return await register_user(payload, db)


# ─── Dashboard ───────────────────────────────────────────────

@router.get(
    "/{user_id}/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
    },
    summary="Get personal dashboard",
    description=(
        "Returns full dashboard data for a single user including "
        "activity history, sport breakdown, and points over time."
    ),
)
async def get_dashboard_route(
    user_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> DashboardResponse:
    """
    GET /api/users/{user_id}/dashboard

    Fetches and assembles all personal dashboard data for the given userId.
    Delegates all business logic to the user controller.
    """
    return await get_user_dashboard(user_id, db)