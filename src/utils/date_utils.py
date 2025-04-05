from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional

from ..models.subscription import BillingCycle


def calculate_next_renewal_date(start_date: date, cycle: BillingCycle, last_renewal: Optional[date] = None) -> date:
    """Calculates the next renewal date based on the start date, billing cycle,
       and optionally the last renewal date.

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
    base_date = start_date
    if last_renewal and last_renewal > base_date:
        base_date = last_renewal

    next_date: Optional[date] = None

    # Calculate the first potential renewal *after* the base date
    if cycle == BillingCycle.WEEKLY:
        delta = timedelta(weeks=1)
        next_date = base_date + delta
    elif cycle == BillingCycle.MONTHLY:
        delta = relativedelta(months=1)
        next_date = base_date + delta
    elif cycle == BillingCycle.QUARTERLY:
        delta = relativedelta(months=3)
        next_date = base_date + delta
    elif cycle == BillingCycle.YEARLY:
        delta = relativedelta(years=1)
        next_date = base_date + delta
    elif cycle == BillingCycle.BI_ANNUALLY:
        delta = relativedelta(years=2)
        next_date = base_date + delta
    elif cycle == BillingCycle.OTHER:
        # Cannot automatically calculate 'OTHER'
        raise ValueError("Cannot automatically calculate next renewal date for 'OTHER' billing cycle.")
    else:
        # Should not happen with Enum, but defensively handle
        raise ValueError(f"Unknown billing cycle: {cycle}")

    # If the calculated next_date is still in the past relative to today,
    # keep adding the delta until it's in the future.
    # This handles cases where the subscription started long ago.
    while next_date < today:
        if cycle == BillingCycle.WEEKLY:
            next_date += timedelta(weeks=1)
        elif cycle == BillingCycle.MONTHLY:
            next_date += relativedelta(months=1)
        elif cycle == BillingCycle.QUARTERLY:
            next_date += relativedelta(months=3)
        elif cycle == BillingCycle.YEARLY:
            next_date += relativedelta(years=1)
        elif cycle == BillingCycle.BI_ANNUALLY:
            next_date += relativedelta(years=2)
        else:
             # Should be unreachable due to earlier check, but for safety:
            raise ValueError(f"Cannot advance date for cycle: {cycle}")

    return next_date