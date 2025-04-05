import pytest
from datetime import date
from unittest.mock import patch

# Assuming BillingCycle is accessible via this relative path
# Adjust if your structure is different or use absolute imports if configured
from src.models.subscription import BillingCycle
from utils.DateUtils import calculate_next_renewal_date

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


