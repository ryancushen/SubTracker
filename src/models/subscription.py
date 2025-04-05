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
import logging
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
    TRIAL = "trial"


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
    url: Optional[str] = None
    username: Optional[str] = None
    category: str = "Uncategorized"
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    next_renewal_date: Optional[date] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    currency: str = "USD"
    notes: str = ""
    trial_end_date: Optional[date] = None
    service_provider: Optional[str] = None
    payment_method: Optional[str] = None

    def __post_init__(self):
        """
        Perform validation and consistency checks after initialization.

        This method ensures that:
        1. Required fields have valid values (name is provided, cost is non-negative)
        2. Status is consistent with trial_end_date (if one is specified, the other should match)

        It also automatically corrects certain issues to maintain data integrity.

        Raises:
            ValueError: If name is empty or cost is negative
        """
        # Validate required fields
        if not self.name:
            raise ValueError("Subscription name cannot be empty.")
        if self.cost is None or self.cost < 0:
            raise ValueError("Subscription cost cannot be negative.")

        # Enforce consistency between trial_end_date and status
        if self.trial_end_date and self.status != SubscriptionStatus.TRIAL:
            logging.warning(f"Setting status to TRIAL for '{self.name}' as trial_end_date is set.")
            self.status = SubscriptionStatus.TRIAL
        elif not self.trial_end_date and self.status == SubscriptionStatus.TRIAL:
            logging.warning(f"Status is TRIAL for '{self.name}' but no trial_end_date is set. Setting to ACTIVE.")
            self.status = SubscriptionStatus.ACTIVE

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

    def is_trial(self) -> bool:
        """
        Check if the subscription is in trial status.

        Returns:
            bool: True if the subscription status is TRIAL, False otherwise
        """
        return self.status == SubscriptionStatus.TRIAL

    def is_trial_ending_soon(self, days_threshold: int = 7) -> bool:
        """
        Check if this is a trial subscription ending within the specified number of days.

        Args:
            days_threshold: Number of days to consider as "ending soon"

        Returns:
            bool: True if trial is ending within the threshold, False otherwise
        """
        if not self.is_trial() or not self.trial_end_date:
            return False

        days_until_end = (self.trial_end_date - date.today()).days
        return 0 <= days_until_end <= days_threshold