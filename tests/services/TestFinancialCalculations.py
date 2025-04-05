import pytest
from datetime import date, timedelta
import logging
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json
from collections import defaultdict

from src.models.subscription import Subscription, BillingCycle, SubscriptionStatus
from src.services.subscription_service import SubscriptionService

class TestFinancialCalculations:
    """Tests for the financial calculation methods in SubscriptionService."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary directory for test data."""
        return tmp_path

    @pytest.fixture
    def temp_data_path(self, temp_data_dir):
        """Path for the temporary subscriptions JSON file."""
        return temp_data_dir / "test_subscriptions.json"

    @pytest.fixture
    def temp_settings_path(self, temp_data_dir):
        """Path for the temporary settings JSON file."""
        return temp_data_dir / "test_settings.json"

    @pytest.fixture
    def financial_service(self, temp_data_path, temp_settings_path):
        """Provides a SubscriptionService instance with subscriptions for financial testing."""
        today = date.today()

        # Create test subscriptions
        sub1 = Subscription(
            id="monthly1",
            name="Monthly Streaming",
            cost=15.99,
            currency="USD",
            billing_cycle=BillingCycle.MONTHLY,
            start_date=today - timedelta(days=30),
            category="Streaming",
            status=SubscriptionStatus.ACTIVE
        )

        sub2 = Subscription(
            id="yearly1",
            name="Annual Software",
            cost=119.88,  # $9.99/month equivalent
            currency="USD",
            billing_cycle=BillingCycle.YEARLY,
            start_date=today - timedelta(days=60),
            category="Software",
            status=SubscriptionStatus.ACTIVE
        )

        sub3 = Subscription(
            id="quarterly1",
            name="Quarterly Magazine",
            cost=29.97,  # $9.99/month equivalent
            currency="USD",
            billing_cycle=BillingCycle.QUARTERLY,
            start_date=today - timedelta(days=45),
            category="Entertainment",
            status=SubscriptionStatus.ACTIVE
        )

        sub4 = Subscription(
            id="inactive1",
            name="Inactive Service",
            cost=24.99,
            currency="USD",
            billing_cycle=BillingCycle.MONTHLY,
            start_date=today - timedelta(days=90),
            category="Utilities",
            status=SubscriptionStatus.INACTIVE
        )

        sub5 = Subscription(
            id="trial1",
            name="Trial Software",
            cost=0.0,
            currency="USD",
            billing_cycle=BillingCycle.MONTHLY,
            start_date=today - timedelta(days=10),
            trial_end_date=today + timedelta(days=20),
            category="Software",
            status=SubscriptionStatus.TRIAL
        )

        sub6 = Subscription(
            id="uncategorized1",
            name="No Category Service",
            cost=5.99,
            currency="USD",
            billing_cycle=BillingCycle.MONTHLY,
            start_date=today - timedelta(days=15),
            category="",  # No category
            status=SubscriptionStatus.ACTIVE
        )

        # Create service with these subscriptions
        service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))

        # Add subscriptions (bypassing save to file for speed)
        service._subscriptions = {
            sub.id: sub for sub in [sub1, sub2, sub3, sub4, sub5, sub6]
        }

        return service

    def test_normalize_cost_to_period_monthly(self, financial_service):
        """Test normalizing costs to monthly period."""
        service = financial_service

        # Test each billing cycle conversion to monthly
        assert service._normalize_cost_to_period(12.0, BillingCycle.MONTHLY, 'monthly') == 12.0
        assert service._normalize_cost_to_period(120.0, BillingCycle.YEARLY, 'monthly') == 10.0
        assert service._normalize_cost_to_period(30.0, BillingCycle.QUARTERLY, 'monthly') == 10.0
        assert service._normalize_cost_to_period(4.0, BillingCycle.WEEKLY, 'monthly') == pytest.approx(17.33, abs=0.1)
        assert service._normalize_cost_to_period(60.0, BillingCycle.BI_ANNUALLY, 'monthly') == 10.0

        # OTHER should return 0 for recurring calculations
        assert service._normalize_cost_to_period(50.0, BillingCycle.OTHER, 'monthly') == 0.0

    def test_normalize_cost_to_period_annually(self, financial_service):
        """Test normalizing costs to annual period."""
        service = financial_service

        # Test each billing cycle conversion to annual
        assert service._normalize_cost_to_period(10.0, BillingCycle.MONTHLY, 'annually') == 120.0
        assert service._normalize_cost_to_period(100.0, BillingCycle.YEARLY, 'annually') == 100.0
        assert service._normalize_cost_to_period(25.0, BillingCycle.QUARTERLY, 'annually') == 100.0
        assert service._normalize_cost_to_period(2.0, BillingCycle.WEEKLY, 'annually') == pytest.approx(104.0, abs=0.1)
        assert service._normalize_cost_to_period(50.0, BillingCycle.BI_ANNUALLY, 'annually') == 100.0

        # OTHER should return 0 for recurring calculations
        assert service._normalize_cost_to_period(50.0, BillingCycle.OTHER, 'annually') == 0.0

    def test_normalize_cost_invalid_period(self, financial_service):
        """Test that an invalid period raises ValueError."""
        service = financial_service

        with pytest.raises(ValueError, match="Unsupported target period"):
            service._normalize_cost_to_period(10.0, BillingCycle.MONTHLY, 'quarterly')

    def test_calculate_cost_per_category_monthly(self, financial_service):
        """Test calculating cost per category for monthly period."""
        service = financial_service

        # Calculate monthly costs per category
        costs = service.calculate_cost_per_category(period='monthly')

        # Expected values (approximately)
        # Monthly streaming: $15.99
        # Annual software ($119.88/year): $9.99/month
        # Quarterly magazine ($29.97/quarter): $9.99/month
        # Uncategorized ($5.99/month): $5.99/month
        # Note: Inactive and trial subscriptions should not be included

        assert len(costs) >= 4  # At least our 4 categories should exist
        assert costs["Streaming"] == pytest.approx(15.99)
        assert costs["Software"] == pytest.approx(9.99)
        assert costs["Entertainment"] == pytest.approx(9.99)
        assert costs["Uncategorized"] == pytest.approx(5.99)
        assert "Utilities" in costs  # Should exist but be zero (inactive subscription)
        assert costs["Utilities"] == 0.0

    def test_calculate_cost_per_category_annually(self, financial_service):
        """Test calculating cost per category for annual period."""
        service = financial_service

        # Calculate annual costs per category
        costs = service.calculate_cost_per_category(period='annually')

        # Expected values
        # Monthly streaming ($15.99/month): $191.88/year
        # Annual software: $119.88/year
        # Quarterly magazine ($29.97/quarter): $119.88/year
        # Uncategorized ($5.99/month): $71.88/year

        assert len(costs) >= 4
        assert costs["Streaming"] == pytest.approx(191.88)
        assert costs["Software"] == pytest.approx(119.88)
        assert costs["Entertainment"] == pytest.approx(119.88)
        assert costs["Uncategorized"] == pytest.approx(71.88)
        assert costs["Utilities"] == 0.0

    def test_calculate_cost_per_category_invalid_period(self, financial_service):
        """Test that invalid period raises ValueError."""
        service = financial_service

        with pytest.raises(ValueError, match="Period must be 'monthly' or 'annually'"):
            service.calculate_cost_per_category(period='weekly')

    def test_calculate_cost_per_period_monthly(self, financial_service):
        """Test calculating total cost for monthly period."""
        service = financial_service

        # Calculate total monthly cost
        monthly_cost = service.calculate_cost_per_period(period='monthly')

        # Expected: Sum of all active subscriptions normalized to monthly
        # $15.99 + $9.99 + $9.99 + $5.99 = $41.96
        assert monthly_cost == pytest.approx(41.96)

    def test_calculate_cost_per_period_annually(self, financial_service):
        """Test calculating total cost for annual period."""
        service = financial_service

        # Calculate total annual cost
        annual_cost = service.calculate_cost_per_period(period='annually')

        # Expected: Sum of all active subscriptions normalized to yearly
        # $191.88 + $119.88 + $119.88 + $71.88 = $503.52
        assert annual_cost == pytest.approx(503.52)

    def test_calculate_spending_forecast(self, financial_service):
        """Test calculating spending forecast for the next year."""
        service = financial_service

        # Use actual date objects
        today = date.today()
        end_date = today + timedelta(days=365)  # One year forecast

        # Create test subscriptions
        subs = [
            Subscription(name="Monthly Sub", cost=10.0, billing_cycle=BillingCycle.MONTHLY,
                         status=SubscriptionStatus.ACTIVE, start_date=today - timedelta(days=30)),
            Subscription(name="Annual Sub", cost=120.0, billing_cycle=BillingCycle.YEARLY,
                         status=SubscriptionStatus.ACTIVE, start_date=today - timedelta(days=30)),
            Subscription(name="Quarterly Sub", cost=25.0, billing_cycle=BillingCycle.QUARTERLY,
                         status=SubscriptionStatus.ACTIVE, start_date=today - timedelta(days=30)),
            Subscription(name="Canceled Sub", cost=10.0, billing_cycle=BillingCycle.MONTHLY,
                         status=SubscriptionStatus.CANCELLED, start_date=today - timedelta(days=30)),
            Subscription(name="Other Sub", cost=50.0, billing_cycle=BillingCycle.OTHER,
                         status=SubscriptionStatus.ACTIVE, start_date=today - timedelta(days=30))
        ]

        # Monkey patch the service to return our test subscriptions
        original_get_all = service.get_all_subscriptions
        service.get_all_subscriptions = lambda: subs

        try:
            # Calculate the forecast
            forecast = service.calculate_spending_forecast(today, end_date)

            # Expected values:
            # Monthly: ~12 renewals in a year: 10.0 * 12 = 120.0
            # Annual: 1 renewal in a year: 120.0
            # Quarterly: ~4 renewals in a year: 25.0 * 4 = 100.0
            # Canceled: Won't be counted as it's not active
            # Other: Won't be counted as it's excluded in the method
            expected = 120.0 + 120.0 + 100.0

            assert forecast == pytest.approx(expected, abs=0.1)
        finally:
            # Restore the original method
            service.get_all_subscriptions = original_get_all

    def test_forecast_invalid_date_order(self, financial_service):
        """Test that end_date before start_date raises ValueError."""
        service = financial_service
        today = date.today()

        with pytest.raises(ValueError, match="start_date cannot be after end_date"):
            service.calculate_spending_forecast(
                today + timedelta(days=10),  # Start after end
                today
            )

    def test_forecast_invalid_date_types(self, financial_service):
        """Test that non-date objects raise TypeError."""
        service = financial_service
        today = date.today()

        with pytest.raises(TypeError, match="must be date objects"):
            service.calculate_spending_forecast(
                "2023-01-01",  # String instead of date
                today
            )

        with pytest.raises(TypeError, match="must be date objects"):
            service.calculate_spending_forecast(
                today,
                "2023-12-31"  # String instead of date
            )

    def test_check_budget_alerts_no_budget(self, financial_service):
        """Test budget alerts when no budget is set."""
        service = financial_service

        # Mock the get_budget method to return empty dict (no budget set)
        with patch.object(service, 'get_budget', return_value={}):
            alerts = service.check_budget_alerts()
            assert len(alerts) == 0  # No alerts when no budget

    def test_check_budget_alerts_under_budget(self, financial_service):
        """Test budget alerts when spending is under budget."""
        service = financial_service

        # Total monthly spending is around $41.96
        # Set budget to $50 (above spending)
        mock_budget = {
            "monthly": {
                "global": 50.0  # Above our ~$41.96 spending
            }
        }

        with patch.object(service, 'get_budget', return_value=mock_budget):
            alerts = service.check_budget_alerts()
            assert len(alerts) == 0  # No alerts when under budget

    def test_check_budget_alerts_over_budget(self, financial_service):
        """Test budget alerts when spending exceeds budget."""
        service = financial_service

        # Total monthly spending is around $41.96
        # Set budget to $30 (below spending)
        mock_budget = {
            "monthly": {
                "global": 30.0  # Below our ~$41.96 spending
            }
        }

        with patch.object(service, 'get_budget', return_value=mock_budget):
            alerts = service.check_budget_alerts()
            assert len(alerts) == 1  # Should have one alert
            assert "exceeds" in alerts[0].lower()  # Alert should mention exceeding budget