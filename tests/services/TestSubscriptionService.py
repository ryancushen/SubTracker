import pytest
import os
import json
from datetime import date, timedelta
from typing import Dict, Any

from src.models.subscription import Subscription, BillingCycle, SubscriptionStatus
from src.services.subscription_service import SubscriptionService, DEFAULT_DATA_PATH, DEFAULT_SETTINGS_PATH, SubscriptionEncoder, subscription_decoder
from src.utils.date_utils import calculate_next_renewal_date

# Sample Data
SAMPLE_SUB_1 = Subscription(
    id="sub1",
    name="Streaming Service",
    cost=15.99,
    currency="USD",
    billing_cycle=BillingCycle.MONTHLY,
    start_date=date(2024, 1, 15),
    category="Entertainment",
    notes="Standard plan",
    status=SubscriptionStatus.ACTIVE
)

SAMPLE_SUB_2 = Subscription(
    id="sub2",
    name="Yearly Software",
    cost=99.00,
    currency="USD",
    billing_cycle=BillingCycle.YEARLY,
    start_date=date(2023, 3, 1),
    category="Software",
    notes="Auto-renews",
    status=SubscriptionStatus.ACTIVE
)
# Expected next renewal after adding: 2025-03-01 (since 2024-03-01 is past)

SAMPLE_SUB_OTHER_CYCLE = Subscription(
    id="sub3",
    name="Gym Membership",
    cost=50.00,
    currency="GBP",
    billing_cycle=BillingCycle.OTHER, # Cannot auto-calculate renewal
    start_date=date(2024, 5, 20),
    category="Health",
    status=SubscriptionStatus.ACTIVE
)

# Sample Trial Subscriptions
SAMPLE_TRIAL_SUB_ENDING_SOON = Subscription(
    id="trial1",
    name="Software Trial A",
    cost=0.00, # Trials are often free
    billing_cycle=BillingCycle.OTHER, # No regular billing cycle during trial
    start_date=date.today() - timedelta(days=25), # Started 25 days ago
    status=SubscriptionStatus.TRIAL,
    trial_end_date=date.today() + timedelta(days=5), # Ends in 5 days
    service_provider="TrialSoft Inc.",
    payment_method="None required"
)

SAMPLE_TRIAL_SUB_ENDED = Subscription(
    id="trial2",
    name="Software Trial B",
    cost=0.00,
    billing_cycle=BillingCycle.OTHER,
    start_date=date.today() - timedelta(days=40),
    status=SubscriptionStatus.TRIAL, # Status might become inactive/cancelled later
    trial_end_date=date.today() - timedelta(days=10) # Ended 10 days ago
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    return tmp_path

@pytest.fixture
def temp_data_path(temp_data_dir):
    """Path for the temporary subscriptions JSON file."""
    return temp_data_dir / "test_subscriptions.json"

@pytest.fixture
def temp_settings_path(temp_data_dir):
    """Path for the temporary settings JSON file."""
    return temp_data_dir / "test_settings.json"

@pytest.fixture
def empty_service(temp_data_path, temp_settings_path):
    """Provides a SubscriptionService instance with temporary, empty data/settings paths."""
    # Ensure files don't exist before test
    if temp_data_path.exists():
        temp_data_path.unlink()
    if temp_settings_path.exists():
        temp_settings_path.unlink()
    # Service will create default settings if settings file doesn't exist
    return SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))

@pytest.fixture
def populated_service(temp_data_path, temp_settings_path):
    """Provides a SubscriptionService instance initialized with sample data."""
    initial_data = [SAMPLE_SUB_1.__dict__, SAMPLE_SUB_2.__dict__]
    # Manually calculate expected initial renewal dates for saving
    initial_data[0]['next_renewal_date'] = date(2024, 2, 15)
    initial_data[1]['next_renewal_date'] = date(2025, 3, 1) # Assuming today is after 2024-03-01

    # Ensure directory exists
    temp_data_path.parent.mkdir(parents=True, exist_ok=True)

    # Write initial data using the custom encoder
    with open(temp_data_path, 'w') as f:
        json.dump(initial_data, f, cls=SubscriptionEncoder, indent=4)

    # Create dummy settings file
    with open(temp_settings_path, 'w') as f:
        json.dump({"data_path": str(temp_data_path)}, f, indent=4)

    service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))
    # The service recalculates on load, ensure they match our calculation relative to today
    sub1_recalculated = service.get_subscription("sub1")
    sub2_recalculated = service.get_subscription("sub2")
    assert sub1_recalculated is not None
    assert sub2_recalculated is not None
    # Calculate expected dates dynamically using the utility function
    expected_renewal_1 = calculate_next_renewal_date(sub1_recalculated.start_date, sub1_recalculated.billing_cycle)
    expected_renewal_2 = calculate_next_renewal_date(sub2_recalculated.start_date, sub2_recalculated.billing_cycle)
    # Assert against the dynamically calculated dates
    assert sub1_recalculated.next_renewal_date == expected_renewal_1
    assert sub2_recalculated.next_renewal_date == expected_renewal_2
    return service

# --- Test Initialization ---

def test_init_no_files(empty_service, temp_data_path, temp_settings_path):
    """Test initializing service when no data or settings file exists."""
    assert empty_service.get_all_subscriptions() == []
    assert not temp_data_path.exists() # Data file shouldn't be created until save
    assert temp_settings_path.exists() # Default settings should be created
    with open(temp_settings_path, 'r') as f:
        settings = json.load(f)
        # Just check that data_path is set correctly; other default settings may be added over time
        assert "data_path" in settings
        assert settings["data_path"] == str(temp_data_path) # Default setting points to correct temp path

def test_init_with_data(populated_service, temp_data_path):
    """Test initializing service with an existing data file."""
    assert temp_data_path.exists()
    subs = populated_service.get_all_subscriptions()
    assert len(subs) == 2
    sub_ids = {s.id for s in subs}
    assert "sub1" in sub_ids
    assert "sub2" in sub_ids
    # Verify data loaded correctly (check one field)
    assert populated_service.get_subscription("sub1").name == "Streaming Service"
    assert populated_service.get_subscription("sub2").cost == 99.00

def test_init_corrupt_data_file(temp_data_path, temp_settings_path):
    """Test initializing with a corrupt JSON file."""
    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_data_path, 'w') as f:
        f.write("this is not valid json {")
    # Should load empty, maybe print error (capture stderr if needed)
    service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))
    assert service.get_all_subscriptions() == []

def test_init_invalid_subscription_data(temp_data_path, temp_settings_path, capfd):
    """Test loading data with one invalid subscription entry."""
    valid_entry = SAMPLE_SUB_1.__dict__.copy() # type: ignore
    valid_entry['next_renewal_date'] = date(2024, 2, 15)
    invalid_entry = {
        "id": "invalid_sub",
        "name": "Missing Fields",
        # Missing cost, billing_cycle, start_date etc.
    }
    initial_data = [valid_entry, invalid_entry]

    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_data_path, 'w') as f:
        json.dump(initial_data, f, cls=SubscriptionEncoder, indent=4)

    service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))
    # Should skip the invalid entry and load the valid one
    subs = service.get_all_subscriptions()
    assert len(subs) == 1
    assert subs[0].id == "sub1"
    # Check stderr for warning message
    captured = capfd.readouterr()
    assert "Warning: Skipping invalid subscription data" in captured.err or \
           "Warning: Skipping invalid subscription data" in captured.out # Depending on print target


# --- Test Settings ---

def test_update_setting(empty_service, temp_settings_path):
    """Test updating a setting."""
    empty_service.update_setting("test_key", "test_value")
    assert empty_service.settings["test_key"] == "test_value"
    # Verify file was saved
    with open(temp_settings_path, 'r') as f:
        settings = json.load(f)
        assert settings["test_key"] == "test_value"
        assert "data_path" in settings # Ensure original settings persist

def test_update_data_path_setting(temp_data_path, temp_settings_path, temp_data_dir):
    """Test that updating the data_path setting reloads subscriptions."""
    # 1. Initial setup with original data path
    initial_data = [SAMPLE_SUB_1.__dict__]
    initial_data[0]['next_renewal_date'] = date(2024, 2, 15)
    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_data_path, 'w') as f:
        json.dump(initial_data, f, cls=SubscriptionEncoder, indent=4)
    with open(temp_settings_path, 'w') as f:
        json.dump({"data_path": str(temp_data_path)}, f, indent=4)

    service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))
    assert len(service.get_all_subscriptions()) == 1
    assert service.get_subscription("sub1") is not None

    # 2. Create a *new* data file with different content
    new_data_path = temp_data_dir / "new_subscriptions.json"
    new_data = [SAMPLE_SUB_2.__dict__]
    new_data[0]['next_renewal_date'] = date(2025, 3, 1)
    with open(new_data_path, 'w') as f:
        json.dump(new_data, f, cls=SubscriptionEncoder, indent=4)

    # 3. Update the setting
    service.update_setting("data_path", str(new_data_path))

    # 4. Verify data was reloaded from the new path
    assert service.data_path == str(new_data_path)
    assert len(service.get_all_subscriptions()) == 1
    assert service.get_subscription("sub1") is None # Old data gone
    assert service.get_subscription("sub2") is not None # New data loaded
    assert service.get_subscription("sub2").name == "Yearly Software"


# --- Test CRUD Operations ---

def test_add_subscription_valid(empty_service, temp_data_path):
    """Test adding a valid subscription."""
    service = empty_service
    sub_to_add = SAMPLE_SUB_1 # type: ignore
    service.add_subscription(sub_to_add)

    # Check in memory
    assert len(service.get_all_subscriptions()) == 1
    added_sub = service.get_subscription(sub_to_add.id)
    assert added_sub is not None
    assert added_sub.name == sub_to_add.name
    assert added_sub.cost == sub_to_add.cost
    # Check if saved to file
    assert temp_data_path.exists()
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    assert len(data_from_file) == 1
    saved_sub_dict = data_from_file[0]
    assert saved_sub_dict["id"] == sub_to_add.id
    assert saved_sub_dict["name"] == sub_to_add.name
    # Calculate expected date dynamically
    expected_renewal = calculate_next_renewal_date(sub_to_add.start_date, sub_to_add.billing_cycle)
    assert saved_sub_dict["next_renewal_date"] == expected_renewal

def test_add_subscription_other_cycle(empty_service, temp_data_path, capfd):
    """Test adding a subscription with BillingCycle.OTHER."""
    service = empty_service
    sub_to_add = SAMPLE_SUB_OTHER_CYCLE
    service.add_subscription(sub_to_add)

    # Check in memory
    assert len(service.get_all_subscriptions()) == 1
    added_sub = service.get_subscription(sub_to_add.id)
    assert added_sub is not None
    assert added_sub.name == sub_to_add.name
    # Renewal date should be None as it cannot be calculated
    assert added_sub.next_renewal_date is None

    # Check if saved to file
    assert temp_data_path.exists()
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    assert len(data_from_file) == 1
    saved_sub_dict = data_from_file[0]
    assert saved_sub_dict["id"] == sub_to_add.id
    assert saved_sub_dict["next_renewal_date"] is None

    # Check for warning message
    captured = capfd.readouterr()
    assert "Warning: Could not automatically calculate renewal date" in captured.err or \
           "Warning: Could not automatically calculate renewal date" in captured.out


def test_add_subscription_duplicate_id(populated_service):
    """Test adding a subscription with an existing ID."""
    service = populated_service
    assert len(service.get_all_subscriptions()) == 2 # Start with 2
    duplicate_sub = Subscription(
        id="sub1", # Same ID as SAMPLE_SUB_1
        name="Another Service",
        cost=10.00,
        currency="EUR",
        billing_cycle=BillingCycle.MONTHLY,
        start_date=date.today()
    )
    with pytest.raises(ValueError, match=f"Subscription with ID {duplicate_sub.id} already exists."):
        service.add_subscription(duplicate_sub)
    # Ensure no change was made
    assert len(service.get_all_subscriptions()) == 2

def test_add_subscription_invalid_type(empty_service):
    """Test adding an object that is not a Subscription."""
    with pytest.raises(TypeError, match="Item must be a Subscription object."):
        empty_service.add_subscription({"id": "wrong", "name": "Not a Subscription"})

def test_add_subscription_trial(empty_service, temp_data_path, capfd):
    """Test adding a subscription with a trial end date."""
    service = empty_service
    trial_sub = Subscription(
        id="trial_new",
        name="New Trial Service",
        cost=0.0,
        billing_cycle=BillingCycle.MONTHLY, # Cycle after trial
        start_date=date.today() - timedelta(days=10),
        trial_end_date=date.today() + timedelta(days=20),
        service_provider="Trial Co",
        payment_method="Card ending 1111"
        # Status should be auto-set to TRIAL by __post_init__
    )

    # Capture print output from __post_init__
    _ = capfd.readouterr()
    service.add_subscription(trial_sub)

    # Check in memory
    added_sub = service.get_subscription("trial_new")
    assert added_sub is not None
    assert added_sub.name == "New Trial Service"
    assert added_sub.status == SubscriptionStatus.TRIAL # Verify status auto-set
    assert added_sub.trial_end_date == date.today() + timedelta(days=20)
    assert added_sub.service_provider == "Trial Co"
    assert added_sub.payment_method == "Card ending 1111"
    # Renewal date should likely be None if status is TRIAL
    assert added_sub.next_renewal_date is None # Service should set to None if status is trial

    # Check file persistence
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    assert len(data_from_file) == 1
    saved_sub_dict = data_from_file[0]
    assert saved_sub_dict["id"] == "trial_new"
    assert saved_sub_dict["status"] == SubscriptionStatus.TRIAL
    assert saved_sub_dict["trial_end_date"] == date.today() + timedelta(days=20)
    assert saved_sub_dict["service_provider"] == "Trial Co"
    assert saved_sub_dict["payment_method"] == "Card ending 1111"
    assert saved_sub_dict["next_renewal_date"] is None


def test_get_subscription_exists(populated_service):
    """Test getting an existing subscription."""
    sub = populated_service.get_subscription("sub1")
    assert sub is not None
    assert sub.id == "sub1"
    assert sub.name == SAMPLE_SUB_1.name # type: ignore

def test_get_subscription_not_exists(populated_service):
    """Test getting a non-existent subscription."""
    sub = populated_service.get_subscription("non_existent_id")
    assert sub is None

def test_get_all_subscriptions_empty(empty_service):
    """Test getting all subscriptions when the service is empty."""
    assert empty_service.get_all_subscriptions() == []

def test_get_all_subscriptions_populated(populated_service):
    """Test getting all subscriptions when the service has data."""
    subs = populated_service.get_all_subscriptions()
    assert len(subs) == 2
    sub_ids = {s.id for s in subs}
    assert "sub1" in sub_ids
    assert "sub2" in sub_ids

# --- More tests needed for update, delete, edge cases in loading/saving ---
# Update and delete subscription tests have been implemented below
# Recalculation tests have been implemented in the "Test Recalculation on Load" section


# --- Test Update Operations ---

def test_update_subscription_simple_fields(populated_service, temp_data_path):
    """Test updating simple fields like name, cost, notes, category, status."""
    service = populated_service
    sub_id = "sub1"
    update_data = {
        "name": "Updated Streaming Name",
        "cost": 16.50,
        "notes": "New notes added.",
        "category": "Streaming",
        "status": SubscriptionStatus.INACTIVE, # Test updating enum
    }

    original_sub = service.get_subscription(sub_id)
    original_renewal_date = original_sub.next_renewal_date

    success = service.update_subscription(sub_id, update_data)
    assert success is True

    # Check in memory
    updated_sub = service.get_subscription(sub_id)
    assert updated_sub is not None
    assert updated_sub.name == "Updated Streaming Name"
    assert updated_sub.cost == 16.50
    assert updated_sub.notes == "New notes added."
    assert updated_sub.category == "Streaming"
    assert updated_sub.status == SubscriptionStatus.INACTIVE
    # Renewal date should NOT change for these fields
    assert updated_sub.next_renewal_date == original_renewal_date

    # Check file persistence
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    saved_sub_dict = next(item for item in data_from_file if item["id"] == sub_id)
    assert saved_sub_dict["name"] == "Updated Streaming Name"
    assert saved_sub_dict["cost"] == 16.50
    assert saved_sub_dict["status"] == SubscriptionStatus.INACTIVE # Check enum saved correctly
    assert saved_sub_dict["next_renewal_date"] == original_renewal_date


def test_update_subscription_change_billing_cycle(populated_service):
    """Test updating billing_cycle triggers renewal date recalculation."""
    service = populated_service
    sub_id = "sub1" # Monthly, starts 2024-01-15, next renewal 2024-02-15
    original_sub = service.get_subscription(sub_id)
    assert original_sub.billing_cycle == BillingCycle.MONTHLY
    # Assert against the dynamically calculated date loaded by the fixture
    expected_initial_renewal = calculate_next_renewal_date(original_sub.start_date, original_sub.billing_cycle)
    assert original_sub.next_renewal_date == expected_initial_renewal

    update_data = {"billing_cycle": BillingCycle.YEARLY}
    success = service.update_subscription(sub_id, update_data)
    assert success is True

    updated_sub = service.get_subscription(sub_id)
    assert updated_sub.billing_cycle == BillingCycle.YEARLY
    # New renewal date should be 1 year from start date (assuming today > start date)
    # Calculate expected date dynamically
    expected_renewal = calculate_next_renewal_date(updated_sub.start_date, updated_sub.billing_cycle)
    assert updated_sub.next_renewal_date == expected_renewal


def test_update_subscription_change_start_date(populated_service):
    """Test updating start_date triggers renewal date recalculation."""
    service = populated_service
    sub_id = "sub1" # Monthly, starts 2024-01-15, next renewal 2024-02-15
    original_sub = service.get_subscription(sub_id)
    assert original_sub.start_date == date(2024, 1, 15)

    new_start_date = date(2024, 3, 10)
    update_data = {"start_date": new_start_date}
    success = service.update_subscription(sub_id, update_data)
    assert success is True

    updated_sub = service.get_subscription(sub_id)
    assert updated_sub.start_date == new_start_date
    # New renewal date should be 1 month from the new start date
    # Calculate expected date dynamically
    expected_renewal = calculate_next_renewal_date(updated_sub.start_date, updated_sub.billing_cycle)
    assert updated_sub.next_renewal_date == expected_renewal # Assuming today > 2024-03-10


def test_update_subscription_manual_renewal_date(populated_service):
    """Test manually setting the next_renewal_date."""
    service = populated_service
    sub_id = "sub1"
    manual_renewal_date = date(2024, 12, 25)

    update_data = {"next_renewal_date": manual_renewal_date}
    success = service.update_subscription(sub_id, update_data)
    assert success is True

    updated_sub = service.get_subscription(sub_id)
    assert updated_sub.next_renewal_date == manual_renewal_date

    # Also update billing cycle, manual renewal date should persist unless start_date/billing_cycle also change
    update_data_2 = {
        "cost": 20.00, # Non-recalculation field
        "next_renewal_date": date(2025, 1, 1) # New manual date
        }
    success_2 = service.update_subscription(sub_id, update_data_2)
    assert success_2 is True
    updated_sub_2 = service.get_subscription(sub_id)
    assert updated_sub_2.cost == 20.00
    assert updated_sub_2.next_renewal_date == date(2025, 1, 1)


def test_update_subscription_not_found(populated_service):
    """Test updating a non-existent subscription ID."""
    success = populated_service.update_subscription("non_existent", {"name": "Won't work"})
    assert success is False


def test_update_subscription_invalid_data_types(populated_service, capfd, caplog):
    """Test updating with invalid data types for fields."""
    service = populated_service
    sub_id = "sub1"
    original_sub = service.get_subscription(sub_id)
    original_cost = original_sub.cost
    original_status = original_sub.status

    update_data = {
        "cost": "not a number",
        "status": "invalid_status",
        "start_date": "not a date",
        "name": "Valid Name" # Include one valid field
    }
    success = service.update_subscription(sub_id, update_data)
    assert success is True # Should succeed, but skip invalid fields

    # Check that only the valid field was updated
    updated_sub = service.get_subscription(sub_id)
    assert updated_sub.name == "Valid Name"
    # Check that invalid fields were skipped and retain original values
    assert updated_sub.cost == original_cost
    assert updated_sub.status == original_status
    assert updated_sub.start_date == original_sub.start_date

    # Check log messages instead of printed warnings
    assert "Invalid type/value for field 'cost'" in caplog.text
    assert "Invalid type/value for field 'status'" in caplog.text
    assert "Invalid type/value for field 'start_date'" in caplog.text


def test_update_subscription_unknown_attribute(populated_service, capfd, caplog):
    """Test updating with an attribute that doesn't exist on the model."""
    service = populated_service
    sub_id = "sub1"
    original_name = service.get_subscription(sub_id).name

    update_data = {"non_existent_field": "some value", "name": "New Name"}
    success = service.update_subscription(sub_id, update_data)
    assert success is True # Should succeed, skipping the unknown field

    updated_sub = service.get_subscription(sub_id)
    assert updated_sub.name == "New Name" # Valid field updated
    assert not hasattr(updated_sub, "non_existent_field") # Unknown field not added

    # Check log messages instead of printed warnings
    assert "Attempted to update non-existent field" in caplog.text


def test_update_subscription_empty_data(populated_service):
    """Test updating with an empty data dictionary."""
    service = populated_service
    sub_id = "sub1"
    original_sub_dict = service.get_subscription(sub_id).__dict__.copy()

    success = service.update_subscription(sub_id, {})
    assert success is False  # Empty update data should fail or have no effect

    current_sub_dict = service.get_subscription(sub_id).__dict__.copy()
    assert current_sub_dict == original_sub_dict  # No changes made


def test_update_subscription_new_fields(populated_service, temp_data_path):
    """Test updating the new optional fields: service_provider, payment_method."""
    service = populated_service
    sub_id = "sub2"
    update_data = {
        "service_provider": "Software Corp",
        "payment_method": "PayPal user@example.com"
    }

    success = service.update_subscription(sub_id, update_data)
    assert success is True

    # Check in memory
    updated_sub = service.get_subscription(sub_id)
    assert updated_sub.service_provider == "Software Corp"
    assert updated_sub.payment_method == "PayPal user@example.com"

    # Check file persistence
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    saved_sub_dict = next(item for item in data_from_file if item["id"] == sub_id)
    assert saved_sub_dict["service_provider"] == "Software Corp"
    assert saved_sub_dict["payment_method"] == "PayPal user@example.com"


def test_update_subscription_add_trial_date(populated_service, temp_data_path, capfd, caplog):
    """Test updating an active subscription to add a trial end date."""
    service = populated_service
    sub_id = "sub1" # Currently ACTIVE
    assert service.get_subscription(sub_id).status == SubscriptionStatus.ACTIVE

    trial_end = date.today() + timedelta(days=15)
    update_data = {
        "trial_end_date": trial_end.isoformat() # Update using ISO string
    }

    success = service.update_subscription(sub_id, update_data)
    assert success is True

    # Check in memory - status should change to TRIAL
    updated_sub = service.get_subscription(sub_id)
    assert updated_sub.trial_end_date == trial_end
    assert updated_sub.status == SubscriptionStatus.TRIAL

    # Check file persistence
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    saved_sub_dict = next(item for item in data_from_file if item["id"] == sub_id)
    assert saved_sub_dict["trial_end_date"] == trial_end
    assert saved_sub_dict["status"] == SubscriptionStatus.TRIAL

    # Check captured output instead of log
    captured = capfd.readouterr()
    assert "Status auto-updated to TRIAL" in captured.out

def test_update_subscription_remove_trial_date(populated_service, temp_data_path, capfd, caplog):
    """Test updating a trial subscription to remove the trial end date."""
    service = populated_service
    # First, make sub1 a trial subscription
    trial_end = date.today() + timedelta(days=15)
    service.update_subscription("sub1", {"trial_end_date": trial_end})
    sub1 = service.get_subscription("sub1")
    assert sub1.status == SubscriptionStatus.TRIAL
    assert sub1.trial_end_date == trial_end
    _ = capfd.readouterr() # Clear captured output
    caplog.clear() # Clear log messages

    # Now, remove the trial end date
    update_data = {
        "trial_end_date": None
    }
    success = service.update_subscription("sub1", update_data)
    assert success is True

    # Check in memory - status should change back to ACTIVE
    updated_sub = service.get_subscription("sub1")
    assert updated_sub.trial_end_date is None
    assert updated_sub.status == SubscriptionStatus.ACTIVE

    # Check file persistence
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    saved_sub_dict = next(item for item in data_from_file if item["id"] == "sub1")
    assert saved_sub_dict["trial_end_date"] is None
    assert saved_sub_dict["status"] == SubscriptionStatus.ACTIVE

    # Check captured output instead of log
    captured = capfd.readouterr()
    assert "Status auto-updated to ACTIVE" in captured.out


# Tests for delete_subscription implemented above
# Tests for recalculate_all_renewal_dates implemented in the "Test Recalculation on Load" section


# --- Test Delete Operations ---

def test_delete_subscription_exists(populated_service, temp_data_path):
    """Test deleting an existing subscription."""
    service = populated_service
    sub_id_to_delete = "sub1"
    assert service.get_subscription(sub_id_to_delete) is not None # Verify it exists first
    assert len(service.get_all_subscriptions()) == 2

    success = service.delete_subscription(sub_id_to_delete)
    assert success is True

    # Check in memory
    assert service.get_subscription(sub_id_to_delete) is None
    assert len(service.get_all_subscriptions()) == 1
    remaining_sub = service.get_all_subscriptions()[0]
    assert remaining_sub.id == "sub2" # Verify the correct one remains

    # Check file persistence
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    assert len(data_from_file) == 1
    assert data_from_file[0]["id"] == "sub2"


def test_delete_subscription_not_found(populated_service, temp_data_path):
    """Test attempting to delete a non-existent subscription."""
    service = populated_service
    sub_id_to_delete = "non_existent"
    assert service.get_subscription(sub_id_to_delete) is None # Verify it doesn't exist
    initial_subs_count = len(service.get_all_subscriptions())

    success = service.delete_subscription(sub_id_to_delete)
    assert success is False # Should return False for not found

    # Verify no changes in memory or file
    assert len(service.get_all_subscriptions()) == initial_subs_count
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    assert len(data_from_file) == initial_subs_count


# Tests for recalculate_all_renewal_dates implemented in the "Test Recalculation on Load" section


# --- Test Recalculation on Load ---

def test_load_with_missing_renewal_dates(temp_data_path, temp_settings_path):
    """Test loading data where next_renewal_date is missing or null."""
    # Prepare data dictionary *before* creating Subscription objects
    initial_dict_data = [
        {
            "id": "sub1", "name": "Streaming Service", "cost": 15.99, "currency": "USD",
            "billing_cycle": BillingCycle.MONTHLY.value, "start_date": date(2024, 1, 15).isoformat(),
            "category": "Entertainment", "status": SubscriptionStatus.ACTIVE.value,
            "next_renewal_date": None # Explicitly None
        },
        {
            "id": "sub2", "name": "Yearly Software", "cost": 99.00, "currency": "USD",
            "billing_cycle": BillingCycle.YEARLY.value, "start_date": date(2023, 3, 1).isoformat(),
            "category": "Software", "status": SubscriptionStatus.ACTIVE.value
            # next_renewal_date is missing
        }
    ]

    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_data_path, 'w') as f:
        # Save the raw dictionary data directly
        json.dump(initial_dict_data, f, indent=4)

    # Create dummy settings file
    with open(temp_settings_path, 'w') as f:
        json.dump({"data_path": str(temp_data_path)}, f, indent=4)

    # Initialize service - this should trigger recalculation
    service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))

    # Check in memory - dates should be calculated
    sub1 = service.get_subscription("sub1")
    sub2 = service.get_subscription("sub2")
    assert sub1 is not None
    assert sub2 is not None
    # Calculate expected dates dynamically
    expected_renewal_1 = calculate_next_renewal_date(sub1.start_date, sub1.billing_cycle)
    expected_renewal_2 = calculate_next_renewal_date(sub2.start_date, sub2.billing_cycle)
    assert sub1.next_renewal_date == expected_renewal_1
    assert sub2.next_renewal_date == expected_renewal_2

    # Check if file was updated with calculated dates
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    assert len(data_from_file) == 2
    saved_sub1 = next((item for item in data_from_file if item["id"] == "sub1"), None)
    saved_sub2 = next((item for item in data_from_file if item["id"] == "sub2"), None)
    assert saved_sub1 is not None
    assert saved_sub2 is not None
    assert saved_sub1["next_renewal_date"] == expected_renewal_1
    assert saved_sub2["next_renewal_date"] == expected_renewal_2

def test_load_with_outdated_renewal_dates(temp_data_path, temp_settings_path):
    """Test loading data where next_renewal_date is outdated (in the past)."""
    # Prepare data with outdated renewal dates
    initial_data_dict = {
        "id": "sub1", "name": "Streaming Service", "cost": 15.99, "currency": "USD",
        "billing_cycle": BillingCycle.MONTHLY.value, "start_date": date(2024, 1, 15).isoformat(),
        "category": "Entertainment", "status": SubscriptionStatus.ACTIVE.value,
        "next_renewal_date": date(2024, 1, 15).isoformat() # Outdated date
    }

    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_data_path, 'w') as f:
        json.dump([initial_data_dict], f, indent=4)

    with open(temp_settings_path, 'w') as f:
        json.dump({"data_path": str(temp_data_path)}, f, indent=4)

    # Initialize service
    service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))

    # Check in memory - date should be recalculated to the correct *next* renewal
    sub1 = service.get_subscription("sub1")
    assert sub1 is not None
    # Calculate expected date dynamically
    expected_renewal = calculate_next_renewal_date(sub1.start_date, sub1.billing_cycle)
    assert sub1.next_renewal_date == expected_renewal # Should be Feb 15, not Jan 15

    # Check file was updated
    with open(temp_data_path, 'r') as f:
        data_from_file = json.load(f, object_hook=subscription_decoder)
    assert data_from_file[0]["next_renewal_date"] == expected_renewal

def test_load_with_other_cycle_no_recalculation(temp_data_path, temp_settings_path):
    """Test loading BillingCycle.OTHER doesn't attempt recalculation if date is None."""
    initial_data_dict = {
        "id": "sub3", "name": "Gym Membership", "cost": 50.00, "currency": "GBP",
        "billing_cycle": BillingCycle.OTHER.value, "start_date": date(2024, 5, 20).isoformat(),
        "category": "Health", "status": SubscriptionStatus.ACTIVE.value,
        "next_renewal_date": None # Correctly set to None initially
    }

    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_data_path, 'w') as f:
        json.dump([initial_data_dict], f, indent=4)

    with open(temp_settings_path, 'w') as f:
        json.dump({"data_path": str(temp_data_path)}, f, indent=4)

    service = SubscriptionService(data_path=str(temp_data_path), settings_path=str(temp_settings_path))

    # Check in memory - date should remain None
    sub3 = service.get_subscription("sub3")
    assert sub3 is not None
    assert sub3.billing_cycle == BillingCycle.OTHER
    assert sub3.next_renewal_date is None

    # Verify file wasn't unnecessarily saved (if only OTHER cycle was present)
    # Note: This is tricky to assert perfectly without mocking os.path.getmtime
    # or checking specific log messages. We'll rely on the logic check above.


# --- Test Notifications / Upcoming Events ---

@pytest.fixture
def notification_service(empty_service):
    """Provides a service populated with various subscriptions for notification testing."""
    service = empty_service
    today = date.today()

    # 1. Renews soon (in 3 days)
    sub_renews_soon = Subscription(
        id="renews_soon", name="Monthly News", cost=5.0, billing_cycle=BillingCycle.MONTHLY,
        start_date=today - timedelta(days=40),
        next_renewal_date=today + timedelta(days=3)
    )
    # 2. Renews later (in 10 days)
    sub_renews_later = Subscription(
        id="renews_later", name="Quarterly Box", cost=30.0, billing_cycle=BillingCycle.QUARTERLY,
        start_date=today - timedelta(days=100),
        next_renewal_date=today + timedelta(days=10)
    )
    # 3. Renews today
    sub_renews_today = Subscription(
        id="renews_today", name="Weekly Service", cost=2.0, billing_cycle=BillingCycle.WEEKLY,
        start_date=today - timedelta(days=7),
        next_renewal_date=today
    )
    # 4. Trial ends soon (in 5 days)
    sub_trial_ends_soon = Subscription(
        id="trial_ends_soon", name="Trial Software X", cost=0.0, billing_cycle=BillingCycle.OTHER,
        start_date=today - timedelta(days=25),
        status=SubscriptionStatus.TRIAL,
        trial_end_date=today + timedelta(days=5)
    )
    # 5. Trial ends later (in 12 days)
    sub_trial_ends_later = Subscription(
        id="trial_ends_later", name="Trial Service Y", cost=0.0, billing_cycle=BillingCycle.OTHER,
        start_date=today - timedelta(days=18),
        status=SubscriptionStatus.TRIAL,
        trial_end_date=today + timedelta(days=12)
    )
    # 6. Trial ended already
    sub_trial_ended = Subscription(
        id="trial_ended", name="Old Trial Z", cost=0.0, billing_cycle=BillingCycle.OTHER,
        start_date=today - timedelta(days=50),
        status=SubscriptionStatus.TRIAL, # Status might be different in reality
        trial_end_date=today - timedelta(days=20)
    )
    # 7. Active, but renewal date far in future
    sub_active_far_renewal = Subscription(
        id="active_far", name="Yearly Domain", cost=12.0, billing_cycle=BillingCycle.YEARLY,
        start_date=today - timedelta(days=100),
        next_renewal_date=today + timedelta(days=300)
    )
    # 8. Inactive subscription renewing soon (should be ignored)
    sub_inactive_renews_soon = Subscription(
        id="inactive_soon", name="Old Monthly", cost=5.0, billing_cycle=BillingCycle.MONTHLY,
        start_date=today - timedelta(days=60),
        status=SubscriptionStatus.INACTIVE,
        next_renewal_date=today + timedelta(days=4)
    )

    # Add all to the service (bypassing save for setup speed)
    service._subscriptions = {
        sub.id: sub for sub in [
            sub_renews_soon, sub_renews_later, sub_renews_today,
            sub_trial_ends_soon, sub_trial_ends_later, sub_trial_ended,
            sub_active_far_renewal, sub_inactive_renews_soon
        ]
    }
    return service

def test_get_upcoming_events_default_7_days(notification_service):
    """Test getting events within the default 7-day window."""
    service = notification_service
    upcoming = service.get_upcoming_events() # Default days_ahead = 7

    assert len(upcoming) == 3 # Renews today, Renews soon (3d), Trial ends soon (5d)
    event_ids = {sub.id for sub, desc in upcoming}
    assert "renews_today" in event_ids
    assert "renews_soon" in event_ids
    assert "trial_ends_soon" in event_ids

    # Check order (should be sorted by date)
    assert upcoming[0][0].id == "renews_today"
    assert upcoming[1][0].id == "renews_soon"
    assert upcoming[2][0].id == "trial_ends_soon"

    # Check descriptions
    assert "renews on" in upcoming[0][1]
    assert "renews on" in upcoming[1][1]
    assert "trial ends on" in upcoming[2][1]

def test_get_upcoming_events_custom_days(notification_service):
    """Test getting events with a custom days_ahead value."""
    service = notification_service
    upcoming = service.get_upcoming_events(days_ahead=11)

    assert len(upcoming) == 4 # Includes renews_later (10d)
    event_ids = {sub.id for sub, desc in upcoming}
    assert "renews_today" in event_ids
    assert "renews_soon" in event_ids
    assert "trial_ends_soon" in event_ids
    assert "renews_later" in event_ids

    # Check order
    assert upcoming[0][0].id == "renews_today"
    assert upcoming[1][0].id == "renews_soon"
    assert upcoming[2][0].id == "trial_ends_soon"
    assert upcoming[3][0].id == "renews_later"

def test_get_upcoming_events_no_events(notification_service):
    """Test getting events when none are within the window."""
    service = notification_service
    # Clear existing subs and add only one far in the future
    far_sub = Subscription(
        id="far_future", name="Very Far", cost=1, billing_cycle=BillingCycle.YEARLY,
        start_date=date(2020,1,1),
        next_renewal_date=date.today() + timedelta(days=100)
        )
    service._subscriptions = {far_sub.id: far_sub}

    upcoming = service.get_upcoming_events(days_ahead=7)
    assert len(upcoming) == 0

def test_get_upcoming_events_empty_service(empty_service):
    """Test getting events from an empty service."""
    upcoming = empty_service.get_upcoming_events()
    assert len(upcoming) == 0
