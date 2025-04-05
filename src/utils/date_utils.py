"""
Date Utility Module

This module provides date-related utility functions for the SubTracker application.
It includes functionality for calculating subscription renewal dates based on
different billing cycles.
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional

from ..models.subscription import BillingCycle


def calculate_next_renewal_date(start_date: date, cycle: BillingCycle, last_renewal: Optional[date] = None) -> date:
    """
    Calculate the next renewal date based on the provided parameters.

    This function determines when a subscription will next renew based on its
    start date, billing cycle, and optionally the last renewal date. It ensures
    the returned date is in the future.

    Args:
        start_date: The initial start date of the subscription.
        cycle: The billing cycle (enum).
        last_renewal: The most recent renewal date, if known. Used as the base
                      for calculation if provided and later than start_date.
                      Defaults to None.

    Returns:
        The calculated next renewal date.

    Raises:
        ValueError: If the billing cycle is OTHER or unknown.
    """
    today = date.today()
    # Use the latest known date (start or last renewal) as the base for calculation
    base_date = start_date if last_renewal is None else max(start_date, last_renewal)

    # Cannot automatically calculate 'OTHER' billing cycle
    if cycle == BillingCycle.OTHER:
        raise ValueError("Cannot automatically calculate next renewal date for 'OTHER' billing cycle.")

    # Determine the appropriate timedelta based on billing cycle
    delta = _get_cycle_delta(cycle)

    # Calculate first potential renewal after the base date
    next_date = base_date + delta

    # Ensure the renewal date is in the future
    while next_date < today:
        next_date += delta

    return next_date


def _get_cycle_delta(cycle: BillingCycle) -> timedelta | relativedelta:
    """
    Get the appropriate time delta object for a given billing cycle.

    Args:
        cycle: The billing cycle to convert to a time delta

    Returns:
        Either a timedelta or relativedelta object representing the cycle

    Raises:
        ValueError: If the cycle is not recognized or is OTHER
    """
    if cycle == BillingCycle.WEEKLY:
        return timedelta(weeks=1)
    elif cycle == BillingCycle.MONTHLY:
        return relativedelta(months=1)
    elif cycle == BillingCycle.QUARTERLY:
        return relativedelta(months=3)
    elif cycle == BillingCycle.YEARLY:
        return relativedelta(years=1)
    elif cycle == BillingCycle.BI_ANNUALLY:
        return relativedelta(years=2)
    else:
        # Should not happen with proper Enum usage, but defensive handling
        raise ValueError(f"Unknown billing cycle: {cycle}")