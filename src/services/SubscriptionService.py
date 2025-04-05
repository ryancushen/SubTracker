import json
import os
from datetime import date, timedelta
from typing import List, Optional, Dict, Any

from ..models.subscription import Subscription, BillingCycle, SubscriptionStatus
from ..utils.DateUtils import calculate_next_renewal_date

DEFAULT_DATA_PATH = "subscriptions.json"
DEFAULT_SETTINGS_PATH = os.path.join("config", "settings.json")


class SubscriptionEncoder(json.JSONEncoder):
    """Custom JSON encoder for Subscription objects and related enums/types."""
    def default(self, obj):
        if isinstance(obj, Subscription):
            return self._extracted_from_default_4(obj)
        elif isinstance(obj, (BillingCycle, SubscriptionStatus)):
            return obj.value
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

    # TODO Rename this here and in `default`
    def _extracted_from_default_4(self, obj):
        # Convert dataclass to dict, handling enums and dates
        d = obj.__dict__.copy()
        d["billing_cycle"] = obj.billing_cycle.value
        d["status"] = obj.status.value
        d["start_date"] = obj.start_date.isoformat()
        d["next_renewal_date"] = (
            obj.next_renewal_date.isoformat() if obj.next_renewal_date else None
        )
        return d


def subscription_decoder(dct: Dict[str, Any]) -> Dict[str, Any]:
    """Custom JSON decoder hook for Subscription objects."""
    if "billing_cycle" in dct:
        try:
            dct["billing_cycle"] = BillingCycle(dct["billing_cycle"])
        except ValueError:
            # Handle potential invalid enum value during load, maybe log or default
            print(f"Warning: Invalid billing cycle '{dct['billing_cycle']}' found.")
            dct["billing_cycle"] = BillingCycle.OTHER # Or raise error
    if "status" in dct:
        try:
            dct["status"] = SubscriptionStatus(dct["status"])
        except ValueError:
            print(f"Warning: Invalid status '{dct['status']}' found.")
            dct["status"] = SubscriptionStatus.INACTIVE # Or raise error
    if "start_date" in dct and isinstance(dct["start_date"], str):
        dct["start_date"] = date.fromisoformat(dct["start_date"])
    if "next_renewal_date" in dct and isinstance(dct["next_renewal_date"], str):
        dct["next_renewal_date"] = date.fromisoformat(dct["next_renewal_date"])
    if "trial_end_date" in dct and isinstance(dct["trial_end_date"], str):
        dct["trial_end_date"] = date.fromisoformat(dct["trial_end_date"])
    # We don't convert to Subscription object here, let the service do it.
    return dct


class SubscriptionService:
    """Handles loading, saving, and CRUD operations for subscriptions."""

    def __init__(self, data_path: str = DEFAULT_DATA_PATH, settings_path: str = DEFAULT_SETTINGS_PATH):
        self.settings_path = settings_path
        self._potential_data_path = data_path
        self.settings = self._load_settings()
        self.data_path = self.settings.get("data_path", self._potential_data_path)
        # Initialize categories from settings (use a set for efficient add/check)
        self._categories: set[str] = set(self.settings.get("categories", ["Software", "Streaming", "Utilities", "Other"])) # Default categories
        self._subscriptions: Dict[str, Subscription] = {}
        self._load_subscriptions()

    def _load_settings(self) -> Dict[str, Any]:
        """Loads settings from the settings JSON file."""
        default_settings = {
            "data_path": self._potential_data_path,
            "categories": ["Software", "Streaming", "Utilities", "Other"] # Default categories
        }
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    loaded_settings = json.load(f)
                    # Ensure critical settings are present, default if not
                    if "data_path" not in loaded_settings:
                        loaded_settings["data_path"] = default_settings["data_path"]
                    if "categories" not in loaded_settings:
                         loaded_settings["categories"] = default_settings["categories"]
                    # Ensure categories are stored as a list in the JSON
                    if not isinstance(loaded_settings["categories"], list):
                        loaded_settings["categories"] = list(loaded_settings.get("categories", default_settings["categories"]))

                    return loaded_settings
            else:
                # Create default settings if file doesn't exist
                self._save_settings(default_settings) # Save defaults including categories
                return default_settings
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings from {self.settings_path}: {e}")
            print("Using default settings.")
            return default_settings

    def _save_settings(self, settings: Dict[str, Any]) -> None:
        """Saves settings to the settings JSON file."""
        try:
            # Ensure categories are saved as a sorted list for consistency
            if "categories" in settings and isinstance(settings["categories"], set):
                settings["categories"] = sorted(list(settings["categories"]))
            elif "categories" not in settings:
                 settings["categories"] = sorted(list(self._categories)) # Save current categories if missing

            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings to {self.settings_path}: {e}")

    def update_setting(self, key: str, value: Any) -> None:
        """Updates a specific setting and saves the settings file."""
        self.settings[key] = value
        # Special handling if categories are updated externally (though unlikely needed now)
        if key == "categories":
            self._categories = set(value)
        self._save_settings(self.settings)
        # Potentially handle settings changes, e.g., reloading data if data_path changed
        if key == "data_path" and self.data_path != value:
            self.data_path = value
            self._load_subscriptions() # Reload data from new path

    # --- Category Management ---
    def get_categories(self) -> List[str]:
        """Returns a sorted list of available categories."""
        return sorted(list(self._categories))

    def add_category(self, category: str) -> bool:
        """Adds a new category and saves settings if it's unique."""
        category = category.strip()
        if category and category not in self._categories:
            self._categories.add(category)
            self.settings["categories"] = sorted(list(self._categories)) # Update settings dict
            self._save_settings(self.settings)
            return True
        return False # Category was empty or already exists

    # --- Subscription Loading/Saving ---
    def _load_subscriptions(self) -> None:
        """Loads subscriptions from the JSON data file."""
        self._subscriptions = {}
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    # Load raw data using the decoder hook
                    raw_data = json.load(f, object_hook=subscription_decoder)
                    # Convert list of dicts to dict of Subscription objects
                    for item_dict in raw_data:
                        try:
                            # Reconstruct Subscription object
                            sub = Subscription(**item_dict)
                            self._subscriptions[sub.id] = sub
                        except (TypeError, ValueError) as e:
                            print(f"Warning: Skipping invalid subscription data: {item_dict}. Error: {e}")
            # If file doesn't exist, it's fine, we start with an empty list
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading subscriptions from {self.data_path}: {e}")
            # Decide on behavior: raise error, start fresh, or attempt recovery?
            # Starting fresh for now.
            self._subscriptions = {}
        except Exception as e:
            # Catch unexpected errors during loading/parsing
            print(f"Unexpected error loading subscriptions: {e}")
            self._subscriptions = {}

        # Always recalculate/validate renewal dates after loading or starting fresh
        self._recalculate_all_renewal_dates()

    def _recalculate_all_renewal_dates(self):
        """Iterates through loaded subscriptions and recalculates/validates renewal dates."""
        updated = False
        for sub_id, sub in self._subscriptions.items():
            # Skip recalculation for TRIAL status or OTHER cycle
            if sub.status == SubscriptionStatus.TRIAL or sub.billing_cycle == BillingCycle.OTHER:
                # Ensure renewal date is None for trials
                if sub.status == SubscriptionStatus.TRIAL and sub.next_renewal_date is not None:
                    sub.next_renewal_date = None
                    updated = True
                continue # Skip to next subscription

            try:
                # Use the utility function to get the correct next renewal date
                # Pass the existing next_renewal_date as a hint for the calculation base
                new_renewal_date = calculate_next_renewal_date(
                    sub.start_date, sub.billing_cycle, last_renewal=sub.next_renewal_date
                )

                if sub.next_renewal_date != new_renewal_date:
                    sub.next_renewal_date = new_renewal_date
                    updated = True
            except ValueError as e:
                # This shouldn't happen now unless the cycle was changed to OTHER elsewhere
                print(f"Warning: Could not calculate renewal date for {sub.name} ({sub_id}) on load: {e}")
                # Ensure renewal date is None if calculation fails unexpectedly
                if sub.next_renewal_date is not None:
                     sub.next_renewal_date = None
                     updated = True
        # If any dates were updated/fixed on load, save the changes
        if updated:
            self._save_subscriptions()

    def _save_subscriptions(self) -> None:
        """Saves the current list of subscriptions to the JSON data file."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, 'w') as f:
                # Convert dict values (Subscription objects) to a list for saving
                json.dump(list(self._subscriptions.values()), f, cls=SubscriptionEncoder, indent=4)
        except IOError as e:
            print(f"Error saving subscriptions to {self.data_path}: {e}")
            # Potentially raise the error or handle it more gracefully

    # --- CRUD Operations --- #

    def add_subscription(self, subscription: Subscription) -> None:
        """Adds a new subscription and saves the data."""
        if not isinstance(subscription, Subscription):
            raise TypeError("Item must be a Subscription object.")
        if subscription.id in self._subscriptions:
            raise ValueError(f"Subscription with ID {subscription.id} already exists.")

        # If the status is TRIAL (potentially set by __post_init__), renewal date should be None
        if subscription.status == SubscriptionStatus.TRIAL:
            subscription.next_renewal_date = None
        else:
            # Calculate and set the next renewal date for non-trial subscriptions
            try:
                subscription.next_renewal_date = calculate_next_renewal_date(
                    subscription.start_date, subscription.billing_cycle
                )
            except ValueError as e:
                # Handle cases like 'OTHER' cycle where calculation isn't possible
                print(f"Warning: Could not automatically calculate renewal date for {subscription.name}: {e}")
                subscription.next_renewal_date = None # Explicitly set to None

        self._subscriptions[subscription.id] = subscription
        self._save_subscriptions()
        print(f"Subscription '{subscription.name}' added.") # Placeholder feedback

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Retrieves a subscription by its ID."""
        return self._subscriptions.get(subscription_id)

    def get_all_subscriptions(self) -> List[Subscription]:
        """Retrieves all subscriptions."""
        return list(self._subscriptions.values())

    def update_subscription(self, subscription_id: str, updated_data: Dict[str, Any]) -> bool:
        """Updates an existing subscription and saves the data."""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            print(f"Error: Subscription with ID {subscription_id} not found.")
            return False

        valid_updates: Dict[str, Any] = {}
        needs_recalculation = False
        original_start_date = subscription.start_date
        original_billing_cycle = subscription.billing_cycle
        original_status = subscription.status

        # 1. Validate and process incoming data
        for key, value in updated_data.items():
            if not hasattr(subscription, key):
                print(f"Warning: Attribute '{key}' does not exist on Subscription. Skipping.")
                continue

            processed_value = value
            try:
                if key == "billing_cycle":
                    if not isinstance(value, BillingCycle):
                        processed_value = BillingCycle(value)
                    if processed_value != original_billing_cycle:
                        needs_recalculation = True
                elif key == "status" and not isinstance(value, SubscriptionStatus):
                    processed_value = SubscriptionStatus(value)
                elif key == "start_date":
                    if not isinstance(value, date):
                        processed_value = date.fromisoformat(str(value))
                    if processed_value != original_start_date:
                        needs_recalculation = True
                elif key == "cost" and not isinstance(value, (int, float)):
                    processed_value = float(value)
                elif key == "next_renewal_date": # Allow manual override, ensure correct type
                    if value is not None and not isinstance(value, date):
                         processed_value = date.fromisoformat(str(value))
                    # No automatic recalculation trigger if manually set
                elif key == "trial_end_date":
                    if value is not None and not isinstance(value, date):
                        processed_value = date.fromisoformat(str(value))
                    # If trial date is set/unset, status might change via model's __post_init__ logic
                    # Need to ensure this consistency is applied after update
                # Add other field-specific validations/conversions here if needed

                valid_updates[key] = processed_value # Store valid, processed value

            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid value '{value}' provided for attribute '{key}'. Skipping update for this field. Error: {e}")

        if not valid_updates:
            print("No valid update fields provided.")
            return True # Operation successful, but no changes made

        # 2. Apply validated updates
        updated = False
        for key, value in valid_updates.items():
            if getattr(subscription, key) != value:
                setattr(subscription, key, value)
                updated = True

        # Re-apply status consistency check after updates involving trial_end_date or status
        needs_status_check = "trial_end_date" in valid_updates or "status" in valid_updates
        if needs_status_check:
            if subscription.trial_end_date and subscription.status != SubscriptionStatus.TRIAL:
                subscription.status = SubscriptionStatus.TRIAL
                print(f"Info: Status auto-updated to TRIAL for '{subscription.name}' due to trial_end_date presence.")
                if original_status != subscription.status:
                     updated = True # Mark as updated if status changed
            elif not subscription.trial_end_date and subscription.status == SubscriptionStatus.TRIAL:
                subscription.status = SubscriptionStatus.ACTIVE # Default back to active
                print(f"Info: Status auto-updated to ACTIVE for '{subscription.name}' due to trial_end_date removal.")
                if original_status != subscription.status:
                     updated = True # Mark as updated if status changed

        # 3. Recalculate next_renewal_date if needed (and not manually overridden)
        # Check if next_renewal_date was part of the manual updates
        manual_renewal_update = "next_renewal_date" in valid_updates

        # If status is now TRIAL, ensure renewal date is None
        if subscription.status == SubscriptionStatus.TRIAL:
             if subscription.next_renewal_date is not None:
                 subscription.next_renewal_date = None
                 updated = True # Mark updated if renewal date nulled
        # Otherwise (not TRIAL), calculate if necessary
        elif needs_recalculation and not manual_renewal_update:
            try:
                new_renewal_date = calculate_next_renewal_date(
                    subscription.start_date, subscription.billing_cycle
                )
                if subscription.next_renewal_date != new_renewal_date:
                    subscription.next_renewal_date = new_renewal_date
                    updated = True # Mark as updated if renewal date changes
            except ValueError as e:
                print(f"Warning: Could not recalculate renewal date for {subscription.name} after update: {e}")
                # Ensure renewal date is None if calculation fails when it should succeed
                if subscription.next_renewal_date is not None:
                     subscription.next_renewal_date = None
                     updated = True
        # Handle case where status changed *away* from TRIAL and might need initial calculation
        elif not needs_recalculation and original_status == SubscriptionStatus.TRIAL and subscription.status != SubscriptionStatus.TRIAL and not manual_renewal_update:
             try:
                 new_renewal_date = calculate_next_renewal_date(
                     subscription.start_date, subscription.billing_cycle
                 )
                 if subscription.next_renewal_date != new_renewal_date:
                     subscription.next_renewal_date = new_renewal_date
                     updated = True
             except ValueError as e:
                 print(f"Warning: Could not calculate renewal date for {subscription.name} after status change from TRIAL: {e}")
                 if subscription.next_renewal_date is not None:
                     subscription.next_renewal_date = None
                     updated = True

        # 4. Save if changes occurred
        if updated:
            self._save_subscriptions()
            print(f"Subscription '{subscription.name}' updated.")
        else:
            print(f"Subscription '{subscription.name}' data resulted in no changes.")

        return True

    def delete_subscription(self, subscription_id: str) -> bool:
        """Deletes a subscription by its ID and saves the data."""
        if subscription_id in self._subscriptions:
            deleted_name = self._subscriptions[subscription_id].name
            del self._subscriptions[subscription_id]
            self._save_subscriptions()
            print(f"Subscription '{deleted_name}' deleted.") # Placeholder feedback
            return True
        return False

    # --- Helper/Utility Methods --- #

    def get_upcoming_events(self, days_ahead: int = 7) -> List[tuple[Subscription, str]]:
        """Finds subscriptions renewing or trials ending within the specified timeframe.

        Args:
            days_ahead: The number of days in the future to check for events.
                        Defaults to 7.

        Returns:
            A list of tuples, where each tuple contains:
            - The Subscription object.
            - A string describing the event (e.g., "renews on YYYY-MM-DD" or
              "trial ends on YYYY-MM-DD").
        """
        today = date.today()
        target_date = today + timedelta(days=days_ahead)
        upcoming_events = []

        for sub in self.get_all_subscriptions():
            # Check for upcoming renewals (only for non-trial, active/other non-cancelled statuses)
            if sub.next_renewal_date and sub.status not in [SubscriptionStatus.TRIAL, SubscriptionStatus.CANCELLED, SubscriptionStatus.INACTIVE]:
                 if today <= sub.next_renewal_date <= target_date:
                     event_desc = f"renews on {sub.next_renewal_date.isoformat()}"
                     upcoming_events.append((sub, event_desc))

            # Check for upcoming trial ends
            if sub.trial_end_date and sub.status == SubscriptionStatus.TRIAL:
                if today <= sub.trial_end_date <= target_date:
                    event_desc = f"trial ends on {sub.trial_end_date.isoformat()}"
                    upcoming_events.append((sub, event_desc))

        # Sort events by date (either renewal or trial end)
        def get_event_date(event_tuple): # Helper function for sorting key
            sub, desc = event_tuple
            if "renews" in desc and sub.next_renewal_date:
                return sub.next_renewal_date
            elif "trial ends" in desc and sub.trial_end_date:
                return sub.trial_end_date
            return date.max # Should not happen if desc is correct

        upcoming_events.sort(key=get_event_date)

        return upcoming_events


    def calculate_and_set_next_renewal(self, subscription: Subscription):
        """Calculates and sets the next renewal date (placeholder)."""
        # This logic will be implemented in src/utils/date_utils.py
        # and called from here (or within add/update)
        # Implemented via direct calls now