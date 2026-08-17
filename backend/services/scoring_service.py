import math
from models.schemas import SportType, MetricType


# ─── Conversion Rate Constants ───────────────────────────────

POINTS_PER_KM_RUNNING:       int = 100
POINTS_PER_KM_WALKING:       int = 50
POINTS_PER_KM_CYCLING:       int = 25
POINTS_PER_MINUTE_SWIMMING:  int = 15
POINTS_PER_MINUTE_GYM:       int = 5
STEPS_PER_POINT:             int = 100

DISTANCE_SPORT_RATES: dict[SportType, int] = {
    SportType.RUNNING:  POINTS_PER_KM_RUNNING,
    SportType.WALKING:  POINTS_PER_KM_WALKING,
    SportType.CYCLING:  POINTS_PER_KM_CYCLING,
}

DURATION_SPORT_RATES: dict[SportType, int] = {
    SportType.SWIMMING: POINTS_PER_MINUTE_SWIMMING,
    SportType.GYM:      POINTS_PER_MINUTE_GYM,
}


# ─── Internal Helpers ────────────────────────────────────────

def _parse_duration(metric_value: str) -> tuple[int, int]:
    """
    Parse a duration string in MM:SS format into its components.

    Args:
        metric_value: A validated duration string e.g. "1:30", "45:00"

    Returns:
        A tuple of (minutes, seconds) as integers.

    Example:
        "1:55" → (1, 55)
        "45:00" → (45, 0)
    """
    parts        = metric_value.split(":")
    minutes: int = int(parts[0])
    seconds: int = int(parts[1])
    return minutes, seconds


def _calculate_distance_points(metric_value: str, rate: int) -> int:
    """
    Calculate points for distance-based sports.

    Flooring rule:
        Points are calculated first then floored to the nearest integer.
        The floor happens on the FINAL result, not on the distance.

    Args:
        metric_value: Distance as a string e.g. "5.5", "1.55"
        rate:         Points per km for this sport

    Returns:
        Floored integer points.

    Examples:
        "5.5" km running (rate=100) → floor(5.5 × 100) = floor(550.0) = 550
        "1.55" km walking (rate=50) → floor(1.55 × 50) = floor(77.5)  = 77
    """
    distance_km: float = float(metric_value)
    raw_points:  float = distance_km * rate
    return math.floor(raw_points)


def _calculate_duration_points(metric_value: str, rate: int) -> int:
    """
    Calculate points for duration-based sports.

    Flooring rule:
        Only fully completed minutes count.
        Seconds are discarded entirely before point calculation.
        The floor happens on the MINUTES, not on the final points.

    Args:
        metric_value: Duration as a string in MM:SS format e.g. "1:30"
        rate:         Points per whole minute for this sport

    Returns:
        Integer points based on whole minutes only.

    Examples:
        "1:55" gym (rate=5)      → 1 whole minute × 5  = 5  (55 seconds discarded)
        "45:00" gym (rate=5)     → 45 minutes × 5      = 225
        "1:30" swimming (rate=15)→ 1 whole minute × 15 = 15 (30 seconds discarded)
    """
    whole_minutes, _ = _parse_duration(metric_value)
    return whole_minutes * rate


def _calculate_steps_points(metric_value: str) -> int:
    """
    Calculate points for step count activities.

    Flooring rule:
        Points are awarded only for fully completed blocks of 100 steps.
        The step count is floored to the nearest 100 BEFORE calculating points.

    Args:
        metric_value: Step count as a string e.g. "8500", "399"

    Returns:
        Integer points based on complete 100-step blocks only.

    Examples:
        "399" steps  → floor(399 / 100) = 3 complete blocks → 3 points
        "8500" steps → floor(8500 / 100) = 85 complete blocks → 85 points
        "100" steps  → floor(100 / 100) = 1 complete block → 1 point
        "99" steps   → floor(99 / 100) = 0 complete blocks → 0 points
    """
    total_steps:      int = int(metric_value)
    complete_blocks:  int = math.floor(total_steps / STEPS_PER_POINT)
    return complete_blocks


# ─── Public API ──────────────────────────────────────────────

def calculate_points(sport: SportType, metric_value: str) -> int:
    """
    Calculate the points awarded for a fitness activity.

    This is the single public entry point for all point calculations.
    Routes to the correct internal calculation based on the sport type
    and applies the appropriate flooring rule for that metric category.

    Args:
        sport:        The sport type from SportType enum
        metric_value: The raw metric value string from the activity request

    Returns:
        Integer points awarded for the activity. Always >= 0.

    Raises:
        ValueError: If the sport type is unrecognised (should never happen
                    in practice since schemas validate sport before this runs)

    Examples:
        calculate_points(SportType.RUNNING,  "5.5")  → 550
        calculate_points(SportType.WALKING,  "1.55") → 77
        calculate_points(SportType.CYCLING,  "10.0") → 250
        calculate_points(SportType.GYM,      "1:55") → 5
        calculate_points(SportType.SWIMMING, "1:30") → 15
        calculate_points(SportType.STEPS,    "399")  → 3
    """
    if sport in DISTANCE_SPORT_RATES:
        return _calculate_distance_points(
            metric_value,
            DISTANCE_SPORT_RATES[sport]
        )

    if sport in DURATION_SPORT_RATES:
        return _calculate_duration_points(
            metric_value,
            DURATION_SPORT_RATES[sport]
        )

    if sport == SportType.STEPS:
        return _calculate_steps_points(metric_value)

    raise ValueError(f"Unrecognised sport type: {sport}")