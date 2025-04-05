import pytest
from datetime import date, timedelta

from src.models.subscription import Subscription, BillingCycle, SubscriptionStatus

class TestSubscription:
    """Tests for the Subscription model."""

    def test_initialization_minimal(self):
        """Test creating a Subscription with minimal required parameters."""
        sub = Subscription(
            id="test1",
            name="Test Subscription",
            cost=9.99,
            billing_cycle=BillingCycle.MONTHLY,
            start_date=date.today()
        )

        assert sub.id == "test1"
        assert sub.name == "Test Subscription"
        assert sub.cost == 9.99
        assert sub.billing_cycle == BillingCycle.MONTHLY
        assert sub.start_date == date.today()
        # Check defaults
        assert sub.currency == "USD"  # Default currency
        assert sub.status == SubscriptionStatus.ACTIVE  # Default status
        assert sub.category == ""  # Default empty category
        assert sub.notes == ""  # Default empty notes
        assert sub.next_renewal_date is None  # No default renewal date

    def test_initialization_full(self):
        """Test creating a Subscription with all optional parameters."""
        trial_end = date.today() + timedelta(days=14)
        sub = Subscription(
            id="test2",
            name="Premium Service",
            cost=29.99,
            billing_cycle=BillingCycle.YEARLY,
            start_date=date(2023, 1, 1),
            currency="EUR",
            category="Entertainment",
            notes="Family plan",
            status=SubscriptionStatus.TRIAL,
            next_renewal_date=date(2024, 1, 1),
            trial_end_date=trial_end,
            service_provider="Example Corp",
            payment_method="Credit Card",
            url="https://example.com"
        )

        assert sub.id == "test2"
        assert sub.name == "Premium Service"
        assert sub.cost == 29.99
        assert sub.billing_cycle == BillingCycle.YEARLY
        assert sub.start_date == date(2023, 1, 1)
        assert sub.currency == "EUR"
        assert sub.category == "Entertainment"
        assert sub.notes == "Family plan"
        assert sub.status == SubscriptionStatus.TRIAL
        assert sub.next_renewal_date == date(2024, 1, 1)
        assert sub.trial_end_date == trial_end
        assert sub.service_provider == "Example Corp"
        assert sub.payment_method == "Credit Card"
        assert sub.url == "https://example.com"

    def test_post_init_trial_status(self):
        """Test that trial_end_date sets status to TRIAL in __post_init__"""
        # Create with ACTIVE status but provide trial_end_date
        sub = Subscription(
            id="test3",
            name="Trial Service",
            cost=0.00,
            billing_cycle=BillingCycle.MONTHLY,
            start_date=date.today(),
            status=SubscriptionStatus.ACTIVE,  # This should be overridden
            trial_end_date=date.today() + timedelta(days=30)
        )

        # Status should be automatically set to TRIAL
        assert sub.status == SubscriptionStatus.TRIAL

    def test_trial_without_end_date(self):
        """Test explicitly setting TRIAL status without a trial_end_date (valid case)"""
        sub = Subscription(
            id="test4",
            name="Manual Trial",
            cost=0.00,
            billing_cycle=BillingCycle.MONTHLY,
            start_date=date.today(),
            status=SubscriptionStatus.TRIAL  # Explicitly set TRIAL
            # No trial_end_date - this is allowed
        )

        assert sub.status == SubscriptionStatus.TRIAL
        assert sub.trial_end_date is None

    def test_invalid_id_raises_error(self):
        """Test that empty ID raises a ValueError"""
        with pytest.raises(ValueError, match="Subscription ID cannot be empty"):
            Subscription(
                id="",  # Empty ID
                name="Invalid Sub",
                cost=9.99,
                billing_cycle=BillingCycle.MONTHLY,
                start_date=date.today()
            )

    def test_negative_cost_raises_error(self):
        """Test that negative cost raises a ValueError"""
        with pytest.raises(ValueError, match="Cost cannot be negative"):
            Subscription(
                id="test5",
                name="Negative Cost",
                cost=-5.99,  # Negative cost
                billing_cycle=BillingCycle.MONTHLY,
                start_date=date.today()
            )

    def test_cost_zero_is_valid(self):
        """Test that zero cost is valid (for free trials)"""
        sub = Subscription(
            id="test6",
            name="Free Service",
            cost=0.0,
            billing_cycle=BillingCycle.MONTHLY,
            start_date=date.today()
        )

        assert sub.cost == 0.0

    def test_str_representation(self):
        """Test the string representation of a Subscription"""
        sub = Subscription(
            id="test7",
            name="String Test",
            cost=19.99,
            currency="USD",
            billing_cycle=BillingCycle.MONTHLY,
            start_date=date.today()
        )

        # The exact string format may vary depending on implementation
        # Just check that id and name are included
        str_rep = str(sub)
        assert "test7" in str_rep
        assert "String Test" in str_rep
        assert "19.99" in str_rep  # Cost should be included
