import pytest
from datetime import date, timedelta

from src.models.subscription import Subscription, BillingCycle, SubscriptionStatus
from src.services.subscription_service import SubscriptionService

class TestFilteringAndSorting:
    """Tests for filtering and sorting functionality in SubscriptionService."""

    @pytest.fixture
    def filtering_service(self, tmp_path):
        """Create a service populated with test data for filtering and sorting tests."""
        temp_data_path = tmp_path / "test_subscriptions.json"
        temp_settings_path = tmp_path / "test_settings.json"

        # Create a service
        service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))

        # Create test subscriptions with varied attributes
        today = date.today()

        # Different categories
        subs = [
            # Different costs
            Subscription(
                id="low_cost", name="Budget Service", cost=4.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=30),
                category="Budget", status=SubscriptionStatus.ACTIVE
            ),
            Subscription(
                id="mid_cost", name="Standard Service", cost=14.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=45),
                category="Standard", status=SubscriptionStatus.ACTIVE
            ),
            Subscription(
                id="high_cost", name="Premium Service", cost=29.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=15),
                category="Premium", status=SubscriptionStatus.ACTIVE
            ),

            # Different billing cycles
            Subscription(
                id="weekly", name="Weekly News", cost=1.99,
                billing_cycle=BillingCycle.WEEKLY, start_date=today - timedelta(days=10),
                category="News", status=SubscriptionStatus.ACTIVE
            ),
            Subscription(
                id="monthly", name="Monthly Magazine", cost=9.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=20),
                category="Entertainment", status=SubscriptionStatus.ACTIVE
            ),
            Subscription(
                id="yearly", name="Yearly Software", cost=99.99,
                billing_cycle=BillingCycle.YEARLY, start_date=today - timedelta(days=100),
                category="Software", status=SubscriptionStatus.ACTIVE
            ),

            # Different statuses
            Subscription(
                id="active1", name="Active Service 1", cost=5.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=25),
                category="Utilities", status=SubscriptionStatus.ACTIVE
            ),
            Subscription(
                id="inactive1", name="Inactive Service", cost=12.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=60),
                category="Entertainment", status=SubscriptionStatus.INACTIVE
            ),
            Subscription(
                id="trial1", name="Trial Service", cost=0.00,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=5),
                category="Software", status=SubscriptionStatus.TRIAL,
                trial_end_date=today + timedelta(days=25)
            ),

            # Different renewal dates
            Subscription(
                id="renew_soon", name="Renews Tomorrow", cost=7.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=29),
                category="Streaming", status=SubscriptionStatus.ACTIVE,
                next_renewal_date=today + timedelta(days=1)
            ),
            Subscription(
                id="renew_later", name="Renews Next Month", cost=17.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=5),
                category="Streaming", status=SubscriptionStatus.ACTIVE,
                next_renewal_date=today + timedelta(days=25)
            ),

            # With/without extras
            Subscription(
                id="with_notes", name="Service With Notes", cost=8.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=15),
                category="Misc", status=SubscriptionStatus.ACTIVE,
                notes="This is a test note"
            ),
            Subscription(
                id="with_url", name="Service With URL", cost=11.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=15),
                category="Web", status=SubscriptionStatus.ACTIVE,
                url="https://example.com"
            ),
            Subscription(
                id="with_provider", name="Provider Service", cost=13.99,
                billing_cycle=BillingCycle.MONTHLY, start_date=today - timedelta(days=15),
                category="Services", status=SubscriptionStatus.ACTIVE,
                service_provider="Example Provider Inc."
            )
        ]

        # Add subscriptions to service (bypassing save for speed)
        service._subscriptions = {sub.id: sub for sub in subs}

        return service

    def test_get_active_subscriptions(self, filtering_service):
        """Test filtering to get only active subscriptions."""
        service = filtering_service
        active_subs = service.get_subscriptions_by_status(SubscriptionStatus.ACTIVE)

        # Should include all subscriptions with status=ACTIVE
        assert len(active_subs) > 0
        assert all(sub.status == SubscriptionStatus.ACTIVE for sub in active_subs)

        # Check against known active subscriptions
        active_ids = [sub.id for sub in active_subs]
        assert "active1" in active_ids
        assert "low_cost" in active_ids
        assert "high_cost" in active_ids

        # Shouldn't include non-active
        assert "inactive1" not in active_ids
        assert "trial1" not in active_ids

    def test_get_inactive_subscriptions(self, filtering_service):
        """Test filtering to get only inactive subscriptions."""
        service = filtering_service
        inactive_subs = service.get_subscriptions_by_status(SubscriptionStatus.INACTIVE)

        # Should only include inactive subscriptions
        assert len(inactive_subs) == 1
        assert inactive_subs[0].id == "inactive1"
        assert inactive_subs[0].status == SubscriptionStatus.INACTIVE

    def test_get_trial_subscriptions(self, filtering_service):
        """Test filtering to get only trial subscriptions."""
        service = filtering_service
        trial_subs = service.get_subscriptions_by_status(SubscriptionStatus.TRIAL)

        # Should only include trial subscriptions
        assert len(trial_subs) == 1
        assert trial_subs[0].id == "trial1"
        assert trial_subs[0].status == SubscriptionStatus.TRIAL

    def test_get_by_category(self, filtering_service):
        """Test filtering subscriptions by category."""
        service = filtering_service

        # Test each defined category
        streaming_subs = service.get_subscriptions_by_category("Streaming")
        assert len(streaming_subs) == 2
        assert all(sub.category == "Streaming" for sub in streaming_subs)

        software_subs = service.get_subscriptions_by_category("Software")
        assert len(software_subs) == 2  # One active, one trial
        assert all(sub.category == "Software" for sub in software_subs)

        # Test unknown category
        nonexistent_subs = service.get_subscriptions_by_category("NonexistentCategory")
        assert len(nonexistent_subs) == 0

    def test_get_by_cost_range(self, filtering_service):
        """Test filtering subscriptions by cost range."""
        service = filtering_service

        # Low cost range (under $10)
        low_cost_subs = service.get_subscriptions_by_cost_range(0, 10)
        assert len(low_cost_subs) > 0
        assert all(sub.cost <= 10 for sub in low_cost_subs)
        assert "low_cost" in [sub.id for sub in low_cost_subs]

        # Mid cost range ($10-$20)
        mid_cost_subs = service.get_subscriptions_by_cost_range(10, 20)
        assert len(mid_cost_subs) > 0
        assert all(10 <= sub.cost <= 20 for sub in mid_cost_subs)
        assert "mid_cost" in [sub.id for sub in mid_cost_subs]

        # High cost range (over $20)
        high_cost_subs = service.get_subscriptions_by_cost_range(20, 100)
        assert len(high_cost_subs) > 0
        assert all(sub.cost >= 20 for sub in high_cost_subs)
        assert "high_cost" in [sub.id for sub in high_cost_subs]

        # Test empty range
        no_cost_subs = service.get_subscriptions_by_cost_range(200, 300)
        assert len(no_cost_subs) == 0

    def test_get_by_billing_cycle(self, filtering_service):
        """Test filtering subscriptions by billing cycle."""
        service = filtering_service

        # Test each defined billing cycle
        weekly_subs = service.get_subscriptions_by_billing_cycle(BillingCycle.WEEKLY)
        assert len(weekly_subs) == 1
        assert weekly_subs[0].id == "weekly"

        monthly_subs = service.get_subscriptions_by_billing_cycle(BillingCycle.MONTHLY)
        assert len(monthly_subs) > 0
        assert all(sub.billing_cycle == BillingCycle.MONTHLY for sub in monthly_subs)

        yearly_subs = service.get_subscriptions_by_billing_cycle(BillingCycle.YEARLY)
        assert len(yearly_subs) == 1
        assert yearly_subs[0].id == "yearly"

    def test_get_by_renewal_date_range(self, filtering_service):
        """Test filtering subscriptions by renewal date range."""
        service = filtering_service
        today = date.today()

        # Subscriptions renewing in the next 7 days
        upcoming_subs = service.get_subscriptions_by_renewal_range(
            today, today + timedelta(days=7)
        )
        assert len(upcoming_subs) > 0
        assert "renew_soon" in [sub.id for sub in upcoming_subs]
        assert all(
            sub.next_renewal_date and
            today <= sub.next_renewal_date <= today + timedelta(days=7)
            for sub in upcoming_subs
        )

        # Subscriptions renewing in a future month
        future_subs = service.get_subscriptions_by_renewal_range(
            today + timedelta(days=20), today + timedelta(days=30)
        )
        assert "renew_later" in [sub.id for sub in future_subs]

    def test_sort_by_cost_ascending(self, filtering_service):
        """Test sorting subscriptions by cost (low to high)."""
        service = filtering_service
        sorted_subs = service.get_all_subscriptions_sorted(
            sort_by="cost", ascending=True
        )

        # First should be the trial with cost 0
        assert sorted_subs[0].id == "trial1"
        assert sorted_subs[0].cost == 0.0

        # The rest should be in ascending order
        for i in range(1, len(sorted_subs) - 1):
            assert sorted_subs[i].cost <= sorted_subs[i+1].cost

    def test_sort_by_cost_descending(self, filtering_service):
        """Test sorting subscriptions by cost (high to low)."""
        service = filtering_service
        sorted_subs = service.get_all_subscriptions_sorted(
            sort_by="cost", ascending=False
        )

        # First should be the yearly software (highest cost)
        assert sorted_subs[0].id == "yearly"
        assert sorted_subs[0].cost == 99.99

        # The rest should be in descending order
        for i in range(0, len(sorted_subs) - 1):
            assert sorted_subs[i].cost >= sorted_subs[i+1].cost

    def test_sort_by_name(self, filtering_service):
        """Test sorting subscriptions by name."""
        service = filtering_service
        sorted_subs = service.get_all_subscriptions_sorted(
            sort_by="name", ascending=True
        )

        # Should be in alphabetical order
        for i in range(0, len(sorted_subs) - 1):
            assert sorted_subs[i].name <= sorted_subs[i+1].name

    def test_sort_by_renewal_date(self, filtering_service):
        """Test sorting subscriptions by renewal date."""
        service = filtering_service
        sorted_subs = service.get_all_subscriptions_sorted(
            sort_by="next_renewal_date", ascending=True
        )

        # Find subscriptions with renewal dates (filter out None values)
        subs_with_dates = [sub for sub in sorted_subs
                         if sub.next_renewal_date is not None]

        # These should be in chronological order
        for i in range(0, len(subs_with_dates) - 1):
            assert subs_with_dates[i].next_renewal_date <= subs_with_dates[i+1].next_renewal_date

        # Subscriptions without renewal dates should come last
        for sub in sorted_subs[-5:]:  # Check the last few
            if sub.next_renewal_date is None:
                # Found one without date, validate it's at the end
                assert sorted_subs.index(sub) > len(subs_with_dates)

    def test_combined_filtering_and_sorting(self, filtering_service):
        """Test combining filtering and sorting operations."""
        service = filtering_service

        # Get active subscriptions, sorted by cost (high to low)
        active_sorted = service.get_subscriptions_by_status(
            SubscriptionStatus.ACTIVE
        )
        active_sorted.sort(key=lambda sub: sub.cost, reverse=True)

        # First one should be most expensive active subscription
        assert active_sorted[0].status == SubscriptionStatus.ACTIVE
        assert active_sorted[0].cost == 99.99  # yearly software

        # All should be active and in descending cost order
        assert all(sub.status == SubscriptionStatus.ACTIVE for sub in active_sorted)
        for i in range(0, len(active_sorted) - 1):
            assert active_sorted[i].cost >= active_sorted[i+1].cost

    def test_get_distinct_categories(self, filtering_service):
        """Test getting a list of all unique categories."""
        service = filtering_service

        categories = service.get_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0

        # Check for known categories
        assert "Streaming" in categories
        assert "Software" in categories
        assert "Entertainment" in categories

        # Categories should be unique
        assert len(categories) == len(set(categories))

    def test_search_subscriptions(self, filtering_service):
        """Test searching subscriptions by text query."""
        service = filtering_service

        # Search by name
        results = service.search_subscriptions("premium")
        assert len(results) == 1
        assert results[0].id == "high_cost"
        assert "Premium" in results[0].name

        # Search by category
        results = service.search_subscriptions("software")
        assert len(results) == 2  # Active yearly and trial
        assert all("Software" in sub.category for sub in results)

        # Search by notes
        results = service.search_subscriptions("test note")
        assert len(results) == 1
        assert results[0].id == "with_notes"
        assert "test note" in results[0].notes.lower()

        # Search by service provider
        results = service.search_subscriptions("example provider")
        assert len(results) == 1
        assert results[0].id == "with_provider"

        # Search with no matches
        results = service.search_subscriptions("nonexistent query 12345")
        assert len(results) == 0