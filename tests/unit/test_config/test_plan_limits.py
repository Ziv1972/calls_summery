"""Tests for plan limits configuration."""

import pytest

from src.config.plan_limits import PLAN_LIMITS, PlanLimits, get_plan_limits
from src.models.user import UserPlan


class TestPlanLimits:
    """Test plan limits definitions."""

    def test_free_plan_limits(self):
        limits = get_plan_limits(UserPlan.FREE)
        assert limits.calls_per_month == 10
        assert limits.max_file_size_mb == 100

    def test_pro_plan_limits(self):
        limits = get_plan_limits(UserPlan.PRO)
        assert limits.calls_per_month == 100
        assert limits.max_file_size_mb == 500

    def test_business_plan_limits(self):
        limits = get_plan_limits(UserPlan.BUSINESS)
        assert limits.calls_per_month is None  # unlimited
        assert limits.max_file_size_mb == 500

    def test_plan_limits_is_immutable(self):
        limits = get_plan_limits(UserPlan.FREE)
        with pytest.raises(AttributeError):
            limits.calls_per_month = 999

    def test_get_plan_limits_returns_plan_limits(self):
        result = get_plan_limits(UserPlan.FREE)
        assert isinstance(result, PlanLimits)

    def test_all_plans_have_limits(self):
        for plan in UserPlan:
            limits = get_plan_limits(plan)
            assert isinstance(limits, PlanLimits)
            assert limits.max_file_size_mb > 0

    def test_plan_limits_dict_complete(self):
        assert set(PLAN_LIMITS.keys()) == {UserPlan.FREE, UserPlan.PRO, UserPlan.BUSINESS}
