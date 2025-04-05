"""
Subscription Model Module

This module defines the core data models used throughout the SubTracker application,
specifically the Subscription class and related enumerations.

The models defined here establish the structure for subscription data, including
all fields, validation rules, and related utility methods.

Classes:
    BillingCycle: Enumeration of supported billing cycle types
    SubscriptionStatus: Enumeration of possible subscription statuses
    Subscription: Primary data class representing a subscription entry
"""

import uuid
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class BillingCycle(Enum):
    """
    Enumeration for subscription billing cycles.

    This enum defines the various billing cycle options available for subscriptions,
    allowing the application to calculate renewal dates and normalize costs across
    different time periods.

    Attributes:
        MONTHLY: Billing occurs once per month
        YEARLY: Billing occurs once per year
        QUARTERLY: Billing occurs once every three months
        BI_ANNUALLY: Billing occurs once every two years
        WEEKLY: Billing occurs once per week
        OTHER: Custom billing cycle not covered by standard options
    """
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    BI_ANNUALLY = "bi-annually"  # Every 2 years
    WEEKLY = "weekly"
    OTHER = "other"


class SubscriptionStatus(Enum):
    """
    Enumeration for subscription status.

    This enum defines the possible states a subscription can be in,
    which affects how it's treated in calculations and displays.

    Attributes:
        ACTIVE: The subscription is currently active and being charged
        INACTIVE: The subscription is temporarily paused but not cancelled
        CANCELLED: The subscription has been permanently cancelled
        TRIAL: The subscription is in a trial period
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    TRIAL = "trial"  # Added for clarity, can work with trial_end_date


@dataclass
class Subscription:
    """
    Represents a single subscription entry in the tracking system.

    This is the primary data model for the application, containing all information
    about a subscription including its cost, billing cycle, status, and metadata.
    The class includes validation logic in __post_init__ to ensure data consistency.

    Attributes:
        name (str): The name of the subscription service
        cost (float): The cost per billing cycle
        billing_cycle (BillingCycle): How frequently the subscription is billed
        start_date (date): When the subscription began
        url (Optional[str]): Website URL for the subscription service
        username (Optional[str]): Username used for this subscription
        category (str): Category of the subscription (e.g., "Streaming", "Software")
        status (SubscriptionStatus): Current status of the subscription
        next_renewal_date (Optional[date]): Date of the next expected charge
        id (str): Unique identifier for the subscription
        currency (str): Currency code for the cost (default: "USD")
        notes (str): Additional notes or information about the subscription
        trial_end_date (Optional[date]): When the trial period ends, if applicable
        service_provider (Optional[str]): The company providing the service
        payment_method (Optional[str]): Method used for payment
    """

    name: str
    cost: float
    billing_cycle: BillingCycle
    start_date: date
    url: Optional[str] = None # New field
    username: Optional[str] = None # New field
    category: str = "Uncategorized"
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    next_renewal_date: Optional[date] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    currency: str = "USD"  # Default currency
    notes: str = ""
    # New fields
    trial_end_date: Optional[date] = None
    service_provider: Optional[str] = None
    payment_method: Optional[str] = None

    def __post_init__(self):
        """
        Perform validation and consistency checks after initialization.

        This method ensures that:
        1. Required fields have valid values (name is provided, cost is non-negative)
        2. Status is consistent with trial_end_date (if one is specified, the other should match)

        It may also print warnings if inconsistencies are detected and automatically
        corrects certain issues to maintain data integrity.

        Raises:
            ValueError: If name is empty or cost is negative
        """
        if not self.name or self.cost is None or self.cost < 0:
            raise ValueError("Name, cost, or cost is negative.")
        # Note: Calculation of next_renewal_date might be handled externally
        # or potentially here if the logic is simple enough and doesn't require
        # external state/history.
        # If trial_end_date is set, maybe enforce status=TRIAL?
        if self.trial_end_date and self.status != SubscriptionStatus.TRIAL:
            # Optionally auto-set status or raise warning/error
            # For now, let's auto-set it for consistency
            print(f"Warning: Setting status to TRIAL for '{self.name}' as trial_end_date is set.")
            self.status = SubscriptionStatus.TRIAL
        elif not self.trial_end_date and self.status == SubscriptionStatus.TRIAL:
            # If status is TRIAL but no end date, maybe set to active or raise warning
            print(f"Warning: Status is TRIAL for '{self.name}' but no trial_end_date is set. Setting to ACTIVE.")
            self.status = SubscriptionStatus.ACTIVE
        # Calculate initial next_renewal_date if not provided

    def is_active(self) -> bool:
        """
        Check if the subscription status is active.

        This method provides a convenient way to determine if a subscription
        is currently in the active state, which affects calculations like
        monthly and yearly costs.

        Returns:
            bool: True if the subscription status is ACTIVE, False otherwise
        """
        return self.status == SubscriptionStatus.ACTIVE