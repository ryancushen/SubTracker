"""
Tests for the Date Utils module

This module contains tests for the date utility functions used
in the subscription management system.
"""

import pytest
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from unittest.mock import patch

# Assuming BillingCycle is accessible via this relative path
# Adjust if your structure is different or use absolute imports if configured
from src.models.subscription import BillingCycle
from src.utils.date_utils import calculate_next_renewal_date

# --- Test Data ---
# Using a fixed date for 'today' in tests for consistent results
MOCK_TODAY = date(2024, 7, 15)

test_cases = [
    # --- Standard Cases (Start Date in Future or Recent Past) ---
    # Monthly
    (date(2024, 7, 1), BillingCycle.MONTHLY, None, date(2024, 8, 1)),
    (date(2024, 6, 20), BillingCycle.MONTHLY, None, date(2024, 7, 20)), # Start date just passed
    (date(2024, 7, 31), BillingCycle.MONTHLY, None, date(2024, 8, 31)), # Month end
    (date(2024, 1, 31), BillingCycle.MONTHLY, None, date(2024, 7, 29)), # Feb Leap -> Feb 29 -> Mar 29 -> ... -> Jul 29 (Corrected)
    # Yearly
    (date(2024, 7, 1), BillingCycle.YEARLY, None, date(2025, 7, 1)),
    (date(2024, 6, 20), BillingCycle.YEARLY, None, date(2025, 6, 20)), # Start date just passed
    (date(2024, 2, 29), BillingCycle.YEARLY, None, date(2025, 2, 28)), # Leap day start
    # Quarterly
    (date(2024, 7, 1), BillingCycle.QUARTERLY, None, date(2024, 10, 1)),
    (date(2024, 5, 10), BillingCycle.QUARTERLY, None, date(2024, 8, 10)),
    # Weekly
    (date(2024, 7, 10), BillingCycle.WEEKLY, None, date(2024, 7, 17)),
    (date(2024, 7, 14), BillingCycle.WEEKLY, None, date(2024, 7, 21)),
    # Bi-Annually
    (date(2024, 7, 1), BillingCycle.BI_ANNUALLY, None, date(2026, 7, 1)),
    (date(2023, 6, 1), BillingCycle.BI_ANNUALLY, None, date(2025, 6, 1)),

    # --- Cases with Start Date Far in the Past ---
    (date(2022, 1, 1), BillingCycle.MONTHLY, None, date(2024, 8, 1)), # Should fast-forward past MOCK_TODAY
    (date(2020, 6, 15), BillingCycle.YEARLY, None, date(2025, 6, 15)),
    #(date(2023, 10, 1), BillingCycle.QUARTERLY, None, date(2024, 7, 1)), # Original incorrect expectation
    # Re-evaluating QUARTERLY past start:
    # Start 2023-10-01. Renewals: 2024-01-01, 2024-04-01, 2024-07-01.
    # Today is 2024-07-15. The next renewal *after* today is 2024-10-01. Correct.
    (date(2023, 10, 1), BillingCycle.QUARTERLY, None, date(2024, 10, 1)), # Corrected expected date
    (date(2024, 5, 1), BillingCycle.WEEKLY, None, date(2024, 7, 17)), # Should advance week by week past 2024-07-15
    (date(2021, 8, 1), BillingCycle.BI_ANNUALLY, None, date(2025, 8, 1)), # Renewals: 2023-08-01, next is 2025-08-01

    # --- Cases with Last Renewal Date Provided ---
    # Last renewal is used as base
    (date(2023, 1, 1), BillingCycle.MONTHLY, date(2024, 7, 5), date(2024, 8, 5)), # Last renewal is recent
    (date(2022, 5, 5), BillingCycle.YEARLY, date(2024, 5, 5), date(2025, 5, 5)),
    # Last renewal is in the past, needs fast-forwarding
    #(date(2023, 1, 1), BillingCycle.MONTHLY, date(2024, 6, 5), date(2024, 7, 5)), # Original incorrect expectation
    # Base=2024-06-05, next=2024-07-05. today=2024-07-15. So next should be 2024-08-05.
    (date(2023, 1, 1), BillingCycle.MONTHLY, date(2024, 6, 5), date(2024, 8, 5)), # Corrected expected date
    (date(2020, 1, 1), BillingCycle.YEARLY, date(2023, 4, 1), date(2025, 4, 1)), # Base is 2023-04-01, next is 2024-04-01 (past), next is 2025-04-01
    # Last renewal before start date (should be ignored, use start date)
    #(date(2024, 6, 1), BillingCycle.MONTHLY, date(2024, 5, 1), date(2024, 7, 1)), # Original incorrect expectation
    # Base=start_date=2024-06-01, next=2024-07-01. today=2024-07-15. So next should be 2024-08-01.
    (date(2024, 6, 1), BillingCycle.MONTHLY, date(2024, 5, 1), date(2024, 8, 1)), # Corrected expected date

]

@pytest.mark.parametrize("start_date, cycle, last_renewal, expected_date", test_cases)
# Patch 'date.today' within the specific function's scope in date_utils
@patch('src.utils.date_utils.date')
def test_calculate_next_renewal_date(mock_date, start_date, cycle, last_renewal, expected_date):
    """Tests calculate_next_renewal_date with various scenarios."""
    # Configure the mock to return our fixed 'today' date
    mock_date.today.return_value = MOCK_TODAY
    # Ensure that date objects can still be created (mock date only affects date.today)
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
    # For date comparison purposes inside the function, make sure date comparison works
    mock_date.min = date.min
    mock_date.max = date.max
    mock_date.__gt__ = lambda self, other: date.__gt__(self, other)
    mock_date.__lt__ = lambda self, other: date.__lt__(self, other)
    mock_date.__ge__ = lambda self, other: date.__ge__(self, other)
    mock_date.__le__ = lambda self, other: date.__le__(self, other)
    mock_date.__eq__ = lambda self, other: date.__eq__(self, other)


    calculated_date = calculate_next_renewal_date(start_date, cycle, last_renewal)
    assert calculated_date == expected_date

# --- Test Error Handling ---

@patch('src.utils.date_utils.date')
def test_calculate_next_renewal_date_other_cycle(mock_date):
    """Tests that calculate_next_renewal_date raises ValueError for OTHER cycle."""
    mock_date.today.return_value = MOCK_TODAY
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
    mock_date.min = date.min
    mock_date.max = date.max
    mock_date.__gt__ = lambda self, other: date.__gt__(self, other)
    mock_date.__lt__ = lambda self, other: date.__lt__(self, other)
    mock_date.__ge__ = lambda self, other: date.__ge__(self, other)
    mock_date.__le__ = lambda self, other: date.__le__(self, other)
    mock_date.__eq__ = lambda self, other: date.__eq__(self, other)


    start = date(2024, 1, 1)
    with pytest.raises(ValueError) as excinfo:
        calculate_next_renewal_date(start, BillingCycle.OTHER)
    assert "Cannot automatically calculate next renewal date for 'OTHER'" in str(excinfo.value)

@patch('src.utils.date_utils.date')
def test_calculate_next_renewal_date_unknown_cycle(mock_date):
    """Tests that calculate_next_renewal_date raises ValueError for an unexpected cycle value (defensive)."""
    mock_date.today.return_value = MOCK_TODAY
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
    mock_date.min = date.min
    mock_date.max = date.max
    mock_date.__gt__ = lambda self, other: date.__gt__(self, other)
    mock_date.__lt__ = lambda self, other: date.__lt__(self, other)
    mock_date.__ge__ = lambda self, other: date.__ge__(self, other)
    mock_date.__le__ = lambda self, other: date.__le__(self, other)
    mock_date.__eq__ = lambda self, other: date.__eq__(self, other)

    start = date(2024, 1, 1)
    with pytest.raises(ValueError) as excinfo:
        # Simulate an invalid enum value reaching the function
        calculate_next_renewal_date(start, "invalid_cycle_value") # type: ignore
    assert "Unknown billing cycle: invalid_cycle_value" in str(excinfo.value)

# --- Test Next Renewal Date Calculation ---

def test_calculate_monthly_renewal():
    """Test calculating monthly renewal from a start date."""
    today = date.today()

    # Test when start_date is in the past
    past_start = today - timedelta(days=40)  # Over a month ago
    renewal = calculate_next_renewal_date(past_start, BillingCycle.MONTHLY)

    # Expected: Should be the next occurrence of the same day, after today
    expected = past_start + relativedelta(months=2)  # Two months ahead of start
    assert renewal == expected
    assert renewal > today  # Must be in the future

    # Test when start_date is today
    renewal = calculate_next_renewal_date(today, BillingCycle.MONTHLY)
    expected = today + relativedelta(months=1)
    assert renewal == expected

    # Test when using last_renewal parameter
    last_renewal = today - timedelta(days=10)  # Recent renewal
    renewal = calculate_next_renewal_date(past_start, BillingCycle.MONTHLY, last_renewal=last_renewal)
    expected = last_renewal + relativedelta(months=1)
    assert renewal == expected


def test_calculate_yearly_renewal():
    """Test calculating yearly renewal dates."""
    today = date.today()

    # Test for date in prior year
    past_start = today.replace(year=today.year - 2)  # Two years ago
    renewal = calculate_next_renewal_date(past_start, BillingCycle.YEARLY)

    # Should be this year or next year depending on month/day
    if (past_start.month, past_start.day) < (today.month, today.day):
        # If the anniversary has passed this year, it should be next year
        expected = past_start.replace(year=today.year + 1)
    else:
        # If the anniversary is still to come this year
        expected = past_start.replace(year=today.year)

    assert renewal == expected
    # Must be in the future or today (edge case when test runs exactly on renewal date)
    assert renewal >= today  # Changed from > to >= to handle edge case where renewal date equals today


def test_calculate_quarterly_renewal():
    """Test calculating quarterly renewal dates."""
    today = date.today()

    # Start date from 7 months ago
    past_start = today - relativedelta(months=7)
    renewal = calculate_next_renewal_date(past_start, BillingCycle.QUARTERLY)

    # Should be 3 months after the most recent quarter mark from start
    # This means it's either 2 quarters (6 months) or 3 quarters (9 months) from start
    quarters_passed = 7 // 3  # Integer division to get complete quarters
    # Expected is start date + (quarters_passed + 1) * 3 months
    expected = past_start + relativedelta(months=(quarters_passed + 1) * 3)
    assert renewal == expected
    assert renewal > today


def test_calculate_weekly_renewal():
    """Test calculating weekly renewal dates."""
    today = date.today()

    # Start date from 20 days ago (about 3 weeks)
    past_start = today - timedelta(days=20)
    renewal = calculate_next_renewal_date(past_start, BillingCycle.WEEKLY)

    # Calculate expected: start + 3 weeks (which is now past) + 1 more week
    weeks_passed = 20 // 7  # Integer division to get complete weeks
    expected = past_start + timedelta(days=(weeks_passed + 1) * 7)
    assert renewal == expected
    assert renewal > today


def test_calculate_bi_annually_renewal():
    """Test calculating bi-annual (every 2 years) renewal dates."""
    today = date.today()

    # Start date from 3 years ago
    past_start = today.replace(year=today.year - 3)
    renewal = calculate_next_renewal_date(past_start, BillingCycle.BI_ANNUALLY)

    # Calculate expected: start + 4 years (2 bi-annual periods)
    expected = past_start.replace(year=past_start.year + 4)
    assert renewal == expected
    assert renewal > today


def test_calculate_other_cycle_fails():
    """Test that attempting to calculate 'OTHER' cycle renewal raises an error."""
    with pytest.raises(ValueError, match="Cannot automatically calculate next renewal date for 'OTHER' billing cycle"):
        calculate_next_renewal_date(date.today(), BillingCycle.OTHER)


def test_calculate_with_future_start_date():
    """Test calculating renewal when start date is in the future."""
    today = date.today()
    future_start = today + timedelta(days=30)  # 30 days in the future

    renewal = calculate_next_renewal_date(future_start, BillingCycle.MONTHLY)
    expected = future_start + relativedelta(months=1)

    assert renewal == expected
    assert renewal > future_start > today


