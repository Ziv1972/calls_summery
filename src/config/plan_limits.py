"""Plan limits configuration - defines quotas per user plan."""

from dataclasses import dataclass

from src.models.user import UserPlan


@dataclass(frozen=True)
class PlanLimits:
    """Immutable plan limit definition."""

    calls_per_month: int | None  # None = unlimited
    max_file_size_mb: int


PLAN_LIMITS: dict[UserPlan, PlanLimits] = {
    UserPlan.FREE: PlanLimits(calls_per_month=10, max_file_size_mb=100),
    UserPlan.PRO: PlanLimits(calls_per_month=100, max_file_size_mb=500),
    UserPlan.BUSINESS: PlanLimits(calls_per_month=None, max_file_size_mb=500),
}


def get_plan_limits(plan: UserPlan) -> PlanLimits:
    """Return the limits for a given plan."""
    return PLAN_LIMITS[plan]
