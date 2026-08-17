import re
from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ─── Enums ──────────────────────────────────────────────────

class SportType(str, Enum):
    """
    Supported sport types for activity logging.
    Inherits from str so values serialize as plain strings in JSON.
    """
    RUNNING  = "running"
    WALKING  = "walking"
    CYCLING  = "cycling"
    GYM      = "gym"
    SWIMMING = "swimming"
    STEPS    = "steps"


class MetricType(str, Enum):
    """
    Supported metric types that correspond to each sport category.
    """
    DISTANCE = "distance"
    DURATION = "duration"
    COUNT    = "count"


class TrendDirection(str, Enum):
    """
    Direction of rank movement on the leaderboard since last fetch.
    """
    UP   = "up"
    DOWN = "down"
    SAME = "same"


# ─── Constants ──────────────────────────────────────────────

VALID_SPORT_METRIC_MAP: dict[SportType, MetricType] = {
    SportType.RUNNING:  MetricType.DISTANCE,
    SportType.WALKING:  MetricType.DISTANCE,
    SportType.CYCLING:  MetricType.DISTANCE,
    SportType.GYM:      MetricType.DURATION,
    SportType.SWIMMING: MetricType.DURATION,
    SportType.STEPS:    MetricType.COUNT,
}

DURATION_PATTERN: re.Pattern = re.compile(r"^\d+:[0-5]\d$")


# ─── User Schemas ────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    """
    Payload for registering a new user.

    Fields:
        firstName: User's first name. Stripped of whitespace.
        lastName:  User's last name. Stripped of whitespace.
        email:     Optional valid email address.
    """
    firstName: str      = Field(..., min_length=1, max_length=50)
    lastName:  str      = Field(..., min_length=1, max_length=50)
    email:     Optional[EmailStr] = Field(default=None)

    @field_validator("firstName", "lastName")
    @classmethod
    def strip_and_validate_name(cls, value: str) -> str:
        """
        Strip surrounding whitespace and reject blank names.
        Prevents names like '   ' from passing min_length=1.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name cannot be empty or whitespace only")
        return stripped


class UserRegisterResponse(BaseModel):
    """
    Response returned after successful user registration.
    """
    userId:  int
    message: str


# ─── Activity Schemas ────────────────────────────────────────

class ActivityRequest(BaseModel):
    """
    Payload for logging a new fitness activity.

    metricValue is accepted as a string to support all three formats:
        - Distance:  "5.5"   (km as a decimal string)
        - Duration:  "1:30"  (minutes:seconds)
        - Count:     "8500"  (raw step count)

    Validation ensures:
        1. The sport and metricType combination is valid.
        2. The metricValue format matches the metricType.
        3. All numeric values are positive.
    """
    userId:      int        = Field(..., gt=0)
    sport:       SportType
    metricType:  MetricType
    metricValue: str        = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_sport_metric_and_value(self) -> "ActivityRequest":
        """
        Cross-field validation that runs after individual field validation.

        Checks:
            1. Sport and metricType are a valid combination.
            2. metricValue format is correct for the metricType.
        """
        expected_metric = VALID_SPORT_METRIC_MAP[self.sport]
        if expected_metric != self.metricType:
            raise ValueError(
                f"Sport '{self.sport.value}' requires metricType "
                f"'{expected_metric.value}', got '{self.metricType.value}'"
            )

        if self.metricType == MetricType.DISTANCE:
            try:
                value = float(self.metricValue)
                if value <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    f"Distance metricValue must be a positive number, "
                    f"got '{self.metricValue}'"
                )

        elif self.metricType == MetricType.DURATION:
            if not DURATION_PATTERN.match(self.metricValue):
                raise ValueError(
                    f"Duration metricValue must be in MM:SS format "
                    f"(e.g. '1:30'), got '{self.metricValue}'"
                )

        elif self.metricType == MetricType.COUNT:
            try:
                value = int(self.metricValue)
                if value <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    f"Step count metricValue must be a positive integer, "
                    f"got '{self.metricValue}'"
                )

        return self


class ActivityResponse(BaseModel):
    """
    Response returned after successfully logging an activity.
    """
    activityId:    int
    pointsAwarded: int
    sport:         SportType
    metricType:    MetricType
    metricValue:   str
    loggedAt:      datetime


# ─── Leaderboard Schemas ─────────────────────────────────────

class LeaderboardEntry(BaseModel):
    """
    A single entry on the global leaderboard.
    """
    rank:        int
    userId:      int
    name:        str
    totalPoints: int
    trend:       TrendDirection


class LeaderboardResponse(BaseModel):
    """
    Full leaderboard response with metadata.
    """
    leaderboard: list[LeaderboardEntry]
    totalUsers:  int


# ─── Dashboard Schemas ───────────────────────────────────────

class ActivityHistoryItem(BaseModel):
    """
    A single activity entry in the user's personal history.
    """
    id:          int
    sport:       SportType
    metricType:  MetricType
    metricValue: str
    points:      int
    loggedAt:    datetime


class SportBreakdown(BaseModel):
    """
    Points contribution and percentage share for a single sport.
    """
    sport:       SportType
    totalPoints: int
    percentage:  float


class PointsOverTime(BaseModel):
    """
    Aggregated points for a single day — used for the line chart.
    """
    date:   str
    points: int


class DashboardResponse(BaseModel):
    """
    Full personal dashboard data for a single user.
    """
    userId:          int
    name:            str
    totalPoints:     int
    totalActivities: int
    topSport:        Optional[SportType]
    activities:      list[ActivityHistoryItem]
    sportBreakdown:  list[SportBreakdown]
    pointsOverTime:  list[PointsOverTime]


# ─── Error Schema ────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """
    Standardised error response returned for all API errors.
    """
    error:   str
    message: str