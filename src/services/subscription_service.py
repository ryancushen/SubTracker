"""
Subscription Service Module

This module provides the core functionality for managing subscriptions in the SubTracker application.
It handles data persistence, CRUD operations, budget management, and various subscription calculations.

The primary class is SubscriptionService, which serves as the main interface for both the GUI and TUI
to interact with subscription data. It handles loading and saving data to disk, managing subscriptions,
categories, and budget settings.

Classes:
    SubscriptionEncoder: Custom JSON encoder for subscription-related objects
    SubscriptionService: Primary service for managing subscriptions and related data

Functions:
    subscription_decoder: Custom JSON decoder hook for subscription data
"""

import json
import os
import logging
from collections import defaultdict # Added import
from datetime import date, timedelta
from typing import List, Optional, Dict, Any, Set, get_type_hints, get_origin, get_args, Union, Tuple
from types import UnionType # For Python 3.10+
import sys

from ..models.subscription import Subscription, BillingCycle, SubscriptionStatus
from ..utils.date_utils import calculate_next_renewal_date

# Default paths and configuration values
DEFAULT_DATA_PATH = "subscriptions.json"
DEFAULT_SETTINGS_PATH = os.path.join("config", "settings.json")
_DEFAULT_CATEGORIES = ["Software", "Streaming", "Utilities", "Other"] # Define default categories constant
# Define default budget structure (nested)
_DEFAULT_BUDGET = {"monthly": {"global": None, "categories": {}}}

# Configure logger
logger = logging.getLogger(__name__)


class SubscriptionEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for Subscription objects and related enums/types.

    This encoder allows the application to serialize Subscription objects,
    Enum values, and date objects to JSON format for storage.

    Attributes:
        Inherits all attributes from json.JSONEncoder

    Methods:
        default(obj): Custom handling for serialization of specialized types
    """

    def default(self, obj):
        """
        Handle serialization of Subscription, Enum, and date objects.

        This method provides custom serialization for the following types:
        - Subscription objects (converts to a dictionary with serialized fields)
        - BillingCycle and SubscriptionStatus enums (converts to their string values)
        - date objects (converts to ISO format strings)
        - Decimal objects (converts to float)

        Args:
            obj: The object to serialize

        Returns:
            The serialized representation of the object

        Raises:
            TypeError: If the object cannot be serialized (delegated to parent class)
        """
        if isinstance(obj, Subscription):
            return self._encode_subscription(obj)
        elif isinstance(obj, (BillingCycle, SubscriptionStatus)):
            return obj.value
        elif isinstance(obj, date):
            return obj.isoformat()
        # Handle Decimal objects directly
        from decimal import Decimal
        return float(obj) if isinstance(obj, Decimal) else super().default(obj)

    def _encode_subscription(self, subscription: Subscription) -> Dict[str, Any]:
        """
        Convert a Subscription object to a dictionary for JSON encoding.

        Args:
            subscription: The Subscription object to encode

        Returns:
            A dictionary representation of the subscription
        """
        # Convert dataclass to dict, handling enums and dates
        d = subscription.__dict__.copy()
        d["billing_cycle"] = subscription.billing_cycle.value
        d["status"] = subscription.status.value
        d["start_date"] = subscription.start_date.isoformat()
        d["next_renewal_date"] = (
            subscription.next_renewal_date.isoformat() if subscription.next_renewal_date else None
        )
        d["trial_end_date"] = (
             subscription.trial_end_date.isoformat() if subscription.trial_end_date else None
        )
        # Ensure ID is included if it exists (it should for saving)
        if 'id' not in d and hasattr(subscription, 'id'):
            d['id'] = subscription.id
        # Convert cost from Decimal to float for JSON serialization
        if 'cost' in d and hasattr(subscription, 'cost') and d['cost'] is not None:
            from decimal import Decimal
            if isinstance(subscription.cost, Decimal):
                d['cost'] = float(subscription.cost)
        return d


def subscription_decoder(dct: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom JSON decoder hook for Subscription objects.

    This function converts serialized subscription data back into the appropriate
    Python types, specifically handling enums and dates.

    Args:
        dct: Dictionary containing the serialized subscription data

    Returns:
        Dictionary with properly typed values for subscription data

    Note:
        This function does not directly create Subscription objects but prepares
        the data for the SubscriptionService to instantiate them.
    """
    if "billing_cycle" in dct:
        try:
            dct["billing_cycle"] = BillingCycle(dct["billing_cycle"])
        except ValueError:
            # Handle potential invalid enum value during load, maybe log or default
            logger.warning(f"Warning: Invalid billing cycle '{dct['billing_cycle']}' found.")
            dct["billing_cycle"] = BillingCycle.OTHER # Or raise error
    if "status" in dct:
        try:
            dct["status"] = SubscriptionStatus(dct["status"])
        except ValueError:
            logger.warning(f"Warning: Invalid status '{dct['status']}' found.")
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
    """
    Manages all subscription-related operations and data persistence.

    This class serves as the core service for the application, handling CRUD operations
    for subscriptions, category management, budget settings, and various calculations
    such as spending forecasts and budget alerts.

    Attributes:
        settings_path (str): Path to the settings JSON file
        data_path (str): Path to the subscription data JSON file
        settings (dict): Application settings
        _categories (set): Set of subscription categories
        _budget (dict): Budget configuration
        _subscriptions (dict): Dictionary of subscription objects indexed by ID

    Methods are grouped into several categories:
        - Settings management
        - Category management
        - Budget management
        - Subscription CRUD operations
        - Data calculations and analysis
    """

    def __init__(self, data_path: str = DEFAULT_DATA_PATH, settings_path: str = DEFAULT_SETTINGS_PATH):
        """
        Initialize the SubscriptionService with paths to data and settings files.

        Args:
            data_path: Path to the subscription data JSON file (default: "subscriptions.json")
            settings_path: Path to the settings JSON file (default: "config/settings.json")

        Note:
            The actual data_path used may be overridden by the value in settings.
        """
        self.settings_path = settings_path
        self._potential_data_path = data_path
        self.settings = self._load_settings()
        self.data_path = self.settings.get("data_path", self._potential_data_path)
        # Initialize categories from settings (use a set for efficient add/check)
        self._categories: set[str] = set(self.settings.get("categories", _DEFAULT_CATEGORIES)) # Use constant
        # Initialize budget from settings using the new structure
        self._budget: Dict[str, Dict[str, Any]] = self.settings.get("budget", _DEFAULT_BUDGET.copy())
        self._subscriptions: Dict[str, Subscription] = {}
        self._load_subscriptions()

    def _load_settings(self) -> Dict[str, Any]:
        """
        Load settings from the settings JSON file, handling new budget structure.

        This method reads the settings file, validates its contents, and migrates
        from old format to new format if necessary. If the file doesn't exist or is
        invalid, it creates a default settings file.

        Returns:
            Dictionary containing the application settings
        """
        default_settings = {
            "data_path": self._potential_data_path,
            "categories": _DEFAULT_CATEGORIES, # Use constant
            "budget": _DEFAULT_BUDGET.copy() # Use new default budget structure
        }
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    return self._extracted_from__load_settings_20(f, default_settings)
            else:
                # Create default settings if file doesn't exist
                self._save_settings(default_settings)
                return default_settings
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading settings from {self.settings_path}: {e}")
            logger.info("Using default settings.")
            return default_settings

    # TODO Rename this here and in `_load_settings`
    def _extracted_from__load_settings_20(self, f, default_settings):
        loaded_settings = json.load(f)

        # --- Standard Settings Validation --- #
        if "data_path" not in loaded_settings:
            loaded_settings["data_path"] = default_settings["data_path"]
        if "categories" not in loaded_settings:
             loaded_settings["categories"] = default_settings["categories"]
        if not isinstance(loaded_settings.get("categories"), list):
            loaded_settings["categories"] = list(_DEFAULT_CATEGORIES)

        # --- Budget Settings Validation (Handling potential old format) --- #
        budget_setting = loaded_settings.get("budget")
        validated_budget = _DEFAULT_BUDGET.copy() # Start with default structure

        if isinstance(budget_setting, dict):
            monthly_budget_data = budget_setting.get("monthly")

            if isinstance(monthly_budget_data, dict): # New format check
                # Validate global budget
                global_budget = monthly_budget_data.get("global")
                if global_budget is not None:
                    try:
                        validated_budget["monthly"]["global"] = float(global_budget)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid global monthly budget value '{global_budget}'. Setting to None.")
                        validated_budget["monthly"]["global"] = None
                else:
                     validated_budget["monthly"]["global"] = None # Explicitly set if None

                # Validate category budgets
                category_budgets = monthly_budget_data.get("categories")
                if isinstance(category_budgets, dict):
                    for category, value in category_budgets.items():
                        if value is not None:
                            try:
                                validated_budget["monthly"]["categories"][category] = float(value)
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid budget value '{value}' for category '{category}'. Setting to None.")
                                # Optionally keep category key with None, or remove invalid entry
                                # validated_budget["monthly"]["categories"][category] = None
                        else:
                            validated_budget["monthly"]["categories"][category] = None # Allow explicitly setting None

            elif monthly_budget_data is not None: # Handle potential old format (float/int)
                try:
                    # Migrate old global budget value
                    validated_budget["monthly"]["global"] = float(monthly_budget_data)
                    logger.info("Migrated old budget format to new structure (global budget).")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value '{monthly_budget_data}' found in old budget format. Ignoring.")

        loaded_settings["budget"] = validated_budget # Replace potentially invalid/old structure

        return loaded_settings

    def _save_settings(self, settings: Dict[str, Any]) -> None:
        """
        Save settings to the settings JSON file.

        This method ensures the categories are saved as a sorted list and
        the budget structure is valid before saving to disk.

        Args:
            settings: Dictionary of settings to save

        Raises:
            IOError: If there is an error saving the settings file
        """
        try:
            # Ensure categories are saved as a sorted list for consistency
            if "categories" in settings and isinstance(settings["categories"], set):
                settings["categories"] = sorted(list(settings["categories"]))
            elif "categories" not in settings:
                 settings["categories"] = sorted(list(self._categories)) # Save current categories if missing

            # Ensure budget is saved correctly
            if not hasattr(self, 'settings') or "budget" not in self.settings:
                # During initialization, use the default budget
                settings["budget"] = _DEFAULT_BUDGET.copy()
            else:
                # After initialization, use the current budget
                settings["budget"] = self.settings["budget"].copy()

            # Write to disk
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4)

        except (OSError, IOError) as e:
            logger.error(f"Failed to save settings: {e}")
            raise IOError(f"Failed to save settings file: {e}")

    def update_setting(self, key: str, value: Any) -> None:
        """
        Update a specific setting and save the settings file.

        This method handles special cases for category and budget updates
        to ensure they are properly validated.

        Args:
            key: The settings key to update
            value: The new value to assign

        Raises:
            IOError: If there is an error saving the settings file
        """
        self.settings[key] = value
        # Special handling if categories are updated externally (though unlikely needed now)
        if key == "categories":
            self._categories = set(value)
        # Handle budget updates
        elif key == "budget":
             # Ensure budget data is valid (e.g., a dict with expected keys/types)
            if isinstance(value, dict):
                self._budget = value # Update internal state
            else:
                logger.warning(f"Warning: Invalid budget data provided for update: {value}. Keeping existing budget.")
                # Revert settings change if invalid
                self.settings[key] = self._budget
                return # Don't save invalid data

        self._save_settings(self.settings)
        # Potentially handle settings changes, e.g., reloading data if data_path changed
        if key == "data_path" and self.data_path != value:
            self.data_path = value
            self._load_subscriptions() # Reload data from new path

    # --- Category Management ---
    def get_categories(self) -> List[str]:
        """Returns a sorted list of available categories from settings and budget keys."""
        # Combine categories from the main list and budget keys
        all_known_categories = set(self._categories) # Start with categories from settings["categories"]
        budget_categories = self._budget.get("monthly", {}).get("categories", {}).keys()
        all_known_categories.update(budget_categories)
        return sorted(list(all_known_categories))

    def add_category(self, category: str) -> bool:
        """Adds a new category, saves settings, and initializes budget if needed."""
        category = category.strip()
        category_added = False
        if category and category not in self._categories:
            self._categories.add(category)
            self.settings["categories"] = sorted(list(self._categories)) # Update settings dict
            category_added = True

        # Ensure category exists in budget dictionary, initialize with None if new
        monthly_budgets = self._budget.setdefault("monthly", {})
        category_budget_dict = monthly_budgets.setdefault("categories", {})
        if category and category not in category_budget_dict:
            category_budget_dict[category] = None
            # No need to set category_added = True here, only save if category list or budget value changed

        if category_added: # Only save if the main category list was modified
            self._save_settings(self.settings)
            return True
        # Return False if category was empty, already existed in self._categories
        # (even if it was just added to budget dict with None)
        return False

    # --- Budget Management ---
    def get_budget(self) -> Dict[str, Dict[str, Any]]:
        """Returns the current budget settings."""
        # Return the budget from settings if it exists, otherwise return default
        if "budget" in self.settings:
            return self.settings["budget"].copy()
        else:
            # Return a default budget structure if no budget is set
            return _DEFAULT_BUDGET.copy()

    def set_budget(self, budget_data: Dict[str, Dict[str, Any]]) -> bool:
        """Sets or updates monthly budget settings (global and per-category).

        Expects a dictionary structure like:
        {
            "monthly": {
                "global": 150.0,  # Set global budget to 150.0
                "categories": {
                    "Software": 75.0, # Set Software budget to 75.0
                    "Streaming": None, # Clear Streaming budget
                    # Categories not mentioned are left unchanged
                }
            }
        }
        Or pass None/empty dicts to clear sections.
        Example to clear only global: {"monthly": {"global": None}}
        Example to clear only Software: {"monthly": {"categories": {"Software": None}}}

        Args:
            budget_data: The dictionary containing budget updates.

        Returns:
            True if the budget was successfully updated, False otherwise.
        """
        # Start with a deep copy of the current budget to modify
        # Using json load/dump for a simple deep copy
        current_budget = json.loads(json.dumps(self._budget))
        updated = False

        if not isinstance(budget_data, dict):
            logger.error("Invalid budget_data format: must be a dictionary.")
            return False

        monthly_updates = budget_data.get("monthly")
        if isinstance(monthly_updates, dict):
            # --- Update Global Budget --- #
            if "global" in monthly_updates:
                global_val = monthly_updates["global"]
                new_global_budget = None
                valid_global = False
                if global_val is None:
                    new_global_budget = None
                    valid_global = True
                else:
                    try:
                        new_global_budget = float(global_val)
                        if new_global_budget < 0:
                             logger.warning(f"Global budget cannot be negative ('{global_val}'). Ignoring update.")
                        else:
                             valid_global = True
                    except (ValueError, TypeError):
                        logger.error(f"Invalid global monthly budget value '{global_val}'. Must be a number or None.")

                if valid_global and current_budget["monthly"]["global"] != new_global_budget:
                    current_budget["monthly"]["global"] = new_global_budget
                    updated = True

            # --- Update Category Budgets --- #
            category_updates = monthly_updates.get("categories")
            if isinstance(category_updates, dict):
                if "categories" not in current_budget["monthly"]:
                     current_budget["monthly"]["categories"] = {} # Ensure dict exists

                available_categories = self.get_categories()
                for category, value in category_updates.items():
                    # Only update budgets for existing categories
                    if category not in available_categories and category != "Uncategorized": # Allow setting budget for uncategorized
                         logger.warning(f"Attempted to set budget for non-existent category '{category}'. Skipping.")
                         continue

                    new_cat_budget = None
                    valid_cat = False
                    if value is None:
                        new_cat_budget = None
                        valid_cat = True
                    else:
                        try:
                            new_cat_budget = float(value)
                            if new_cat_budget < 0:
                                logger.warning(f"Category budget for '{category}' cannot be negative ('{value}'). Ignoring update.")
                            else:
                                valid_cat = True
                        except (ValueError, TypeError):
                            logger.error(f"Invalid budget value '{value}' for category '{category}'. Must be a number or None.")

                    if valid_cat:
                        current_category_budget = current_budget["monthly"]["categories"].get(category)
                        if current_category_budget != new_cat_budget:
                            current_budget["monthly"]["categories"][category] = new_cat_budget
                            updated = True
                        # Remove category key if budget is set back to None (optional, keeps structure cleaner)
                        if new_cat_budget is None and category in current_budget["monthly"]["categories"]:
                            # Check if it actually existed before potentially deleting
                            if current_category_budget is not None:
                                updated = True # Mark as updated even if just clearing
                            del current_budget["monthly"]["categories"][category]

        elif monthly_updates is not None:
            logger.error("Invalid format for 'monthly' budget data: must be a dictionary.")
            return False

        # If any valid updates were made, save the changes
        if updated:
            # Use update_setting to ensure persistence and state update
            self.update_setting("budget", current_budget)
            logger.info("Budget settings updated.")
            return True
        else:
            logger.info("No changes applied to budget settings.")
            return False

    def set_monthly_category_budget(self, category: str, budget: Optional[float]) -> None:
        """Sets the monthly budget for a specific category and saves settings."""
        category = category.strip()
        if not category:
            logger.warning("Attempted to set budget for empty category name.")
            return

        try:
            self._extracted_from_set_monthly_category_budget_10(budget, category)
        except Exception as e:
             logger.error(f"Error setting category budget for '{category}': {e}", exc_info=True)
    def _extracted_from_set_monthly_category_budget_10(self, budget, category):
        # Ensure structure exists
        monthly_budgets = self._budget.setdefault("monthly", {})
        category_budget_dict = monthly_budgets.setdefault("categories", {})

        # Validate budget type before setting
        if budget is not None:
            try:
                budget = float(budget) # Ensure it's a float
                if budget < 0:
                    logger.warning(f"Attempted to set negative budget for {category}. Setting to None.")
                    budget = None
            except (ValueError, TypeError):
                logger.warning(f"Invalid budget value type for {category}. Setting to None.")
                budget = None

        # Update the budget value
        category_budget_dict[category] = budget
        # Ensure the category is also in the main category list
        if category not in self._categories:
            self._categories.add(category)
            self.settings["categories"] = sorted(list(self._categories))

        # Save the entire settings object (which includes the updated self._budget)
        self._save_settings(self.settings)
        logger.info(f"Set budget for category '{category}' to {budget}")

    def get_monthly_category_budget(self, category: str) -> Optional[float]:
        """Gets the monthly budget for a specific category."""
        category = category.strip()
        if not category:
            return None
        try:
            budget = self._budget.get("monthly", {}).get("categories", {}).get(category)
            # Ensure it's a float or None before returning
            return float(budget) if budget is not None else None
        except Exception as e:
            logger.error(f"Error getting budget for category '{category}': {e}", exc_info=True)
            return None

    def delete_category(self, category_to_delete: str) -> bool:
        """Deletes a category and updates associated subscriptions to 'Uncategorized'."""
        category_to_delete = category_to_delete.strip()
        if not category_to_delete or category_to_delete == "Uncategorized":
            logger.warning(f"Cannot delete empty or 'Uncategorized' category: '{category_to_delete}'")
            return False

        settings_changed = False
        subscriptions_changed = False

        # Remove from main category list in settings
        if category_to_delete in self._categories:
            self._categories.remove(category_to_delete)
            self.settings["categories"] = sorted(list(self._categories))
            settings_changed = True

        # Remove from budget dictionary
        monthly_budgets = self._budget.get("monthly", {})
        category_budget_dict = monthly_budgets.get("categories", {})
        if category_to_delete in category_budget_dict:
            del category_budget_dict[category_to_delete]
            # If categories dict becomes empty, maybe remove it? Optional.
            # if not category_budget_dict:
            #     del monthly_budgets['categories']
            settings_changed = True # Budget structure changed

        # Update subscriptions using this category
        for sub_id, sub in self._subscriptions.items():
            if sub.category == category_to_delete:
                sub.category = "Uncategorized"
                subscriptions_changed = True
                logger.info(f"Subscription '{sub.name}' ({sub_id}) category changed to Uncategorized due to deletion of '{category_to_delete}'.")

        # Save changes if any occurred
        if settings_changed:
            self._save_settings(self.settings)
        if subscriptions_changed:
            self._save_subscriptions()

        if settings_changed or subscriptions_changed:
            logger.info(f"Category '{category_to_delete}' deleted.")
            return True
        else:
            logger.warning(f"Category '{category_to_delete}' not found for deletion.")
            return False

    # --- Subscription Loading/Saving ---
    def _load_subscriptions(self) -> None:
        """
        Load subscriptions from the data file.

        This method will attempt to read and parse the subscriptions.json file. If the file
        does not exist or is empty, the subscriptions dictionary will remain empty.
        """
        self._subscriptions = {}

        if not os.path.exists(self.data_path):
            logger.info(f"No data file found at {self.data_path}. Starting with an empty subscription list.")
            return

        try:
            with open(self.data_path, 'r') as file:
                subscription_dicts = json.load(file, object_hook=subscription_decoder)
                num_loaded = 0

                for sub_dict in subscription_dicts:
                    try:
                        # Create Subscription object from the dictionary
                        subscription = Subscription(**sub_dict)
                        # Store in dictionary by ID
                        self._subscriptions[subscription.id] = subscription
                        num_loaded += 1
                    except (TypeError, ValueError) as e:
                        # Log error and skip invalid entries
                        error_msg = f"Warning: Skipping invalid subscription data: {sub_dict}. Error: {e}"
                        logger.warning(error_msg)
                        print(error_msg, file=sys.stderr)  # Also print to stderr for test capture
                        continue
                logger.info(f"Loaded {num_loaded} subscriptions from {self.data_path}")
                self._recalculate_all_renewal_dates()

        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading subscriptions from {self.data_path}: {e}")
            self._subscriptions = {}

    def _recalculate_all_renewal_dates(self):
        """Iterates through loaded subscriptions and recalculates/validates renewal dates."""
        updated = False
        for sub_id, sub in self._subscriptions.items():
            # Skip recalculation for TRIAL status or OTHER cycle
            if sub.status == SubscriptionStatus.TRIAL:
                # Ensure renewal date is None for trials
                if sub.next_renewal_date is not None:
                    sub.next_renewal_date = None
                    updated = True
                continue # Skip to next subscription

            elif sub.billing_cycle == BillingCycle.OTHER:
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
                # Log the specific error during recalculation
                logger.warning(f"Could not calculate renewal date for {sub.name} ({sub_id}) on load: {e}. Setting to None.")
                # Ensure renewal date is None if calculation fails unexpectedly
                if sub.next_renewal_date is not None:
                     sub.next_renewal_date = None
                     updated = True
            except Exception as e:
                 # Catch any other unexpected errors during recalculation for a specific sub
                 logger.error(f"Unexpected error recalculating date for {sub.name} ({sub_id}): {e}", exc_info=True)
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

            # Debug logging
            logger.info(f"Saving {len(self._subscriptions)} subscriptions to {self.data_path}")
            for sub_id, sub in self._subscriptions.items():
                logger.info(f"Subscription: {sub.name} (ID: {sub_id})")

            with open(self.data_path, 'w') as f:
                # Convert dict values (Subscription objects) to a list for saving
                json.dump(list(self._subscriptions.values()), f, cls=SubscriptionEncoder, indent=4)

            logger.info(f"Successfully saved subscriptions to {self.data_path}")
        except IOError as e:
            logger.error(f"Error saving subscriptions to {self.data_path}: {e}")
            # Potentially raise the error or handle it more gracefully

    # --- CRUD Operations --- #

    def add_subscription(self, subscription: Subscription) -> None:
        """
        Add a new subscription to the service and save it.

        Args:
            subscription: The subscription object to add

        Raises:
            TypeError: If the item is not a Subscription object
            ValueError: If a subscription with the same ID already exists
        """
        if not isinstance(subscription, Subscription):
            raise TypeError("Item must be a Subscription object.")

        if subscription.id in self._subscriptions:
            raise ValueError(f"Subscription with ID {subscription.id} already exists.")

        # Set renewal date based on start date and billing cycle (if ACTIVE)
        if subscription.status != SubscriptionStatus.TRIAL:
            try:
                if subscription.billing_cycle == BillingCycle.OTHER:
                    warning_msg = f"Warning: Could not automatically calculate renewal date for {subscription.name}: Cannot calculate for 'OTHER' billing cycle."
                    logger.warning(warning_msg)
                    print(warning_msg, file=sys.stderr)  # Also print to stderr for test capture
                    subscription.next_renewal_date = None
                else:
                    # Recalculate the next renewal date on add
                    subscription.next_renewal_date = calculate_next_renewal_date(
                        subscription.start_date, subscription.billing_cycle
                    )
            except ValueError as e:
                warning_msg = f"Warning: Could not automatically calculate renewal date for {subscription.name}: {e}"
                logger.warning(warning_msg)
                print(warning_msg, file=sys.stderr)  # Also print to stderr for test capture
                subscription.next_renewal_date = None
        else:
            # For TRIAL subscriptions, no renewal date needed initially
            subscription.next_renewal_date = None

        # Add and save
        self._subscriptions[subscription.id] = subscription
        self._save_subscriptions()

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Retrieves a subscription by its ID."""
        return self._subscriptions.get(subscription_id)

    def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """Alias for get_subscription for backward compatibility."""
        logger.info(f"Getting subscription by ID: {subscription_id}")
        sub = self.get_subscription(subscription_id)
        if sub:
            logger.info(f"Found subscription: {sub.name}")
        else:
            logger.warning(f"No subscription found with ID: {subscription_id}")
        return sub

    def get_all_subscriptions(self) -> List[Subscription]:
        """Retrieves all subscriptions."""
        return list(self._subscriptions.values())

    def update_subscription(self, subscription_id: str, updated_data: Dict[str, Any]) -> bool:
        """Updates an existing subscription with validated data."""
        if subscription_id not in self._subscriptions:
            logger.warning(f"Attempted to update non-existent subscription ID: {subscription_id}")
            return False

        original_subscription = self._subscriptions[subscription_id]
        changed_fields: Set[str] = set()

        # --- 1. Validate and Prepare Updates ---
        valid_updates, initial_changed_fields = self._validate_and_prepare_updates(
            original_subscription, updated_data
        )
        changed_fields.update(initial_changed_fields)

        if not valid_updates:
            logger.info(f"No valid updates provided for subscription ID: {subscription_id}")
            return False # No valid fields to update

        # --- 2. Apply Validated Updates ---
        for key, value in valid_updates.items():
            setattr(original_subscription, key, value)

        # --- 3. Post-update logic (Status Consistency, Renewal Date) ---
        status_changed = self._ensure_status_consistency(original_subscription)
        if status_changed:
            changed_fields.add("status")

        # Determine if manual renewal was set *during this update*
        manually_set_renewal = "next_renewal_date" in valid_updates

        # Recalculate renewal date if necessary
        renewal_changed = self._update_renewal_date(original_subscription, changed_fields, manually_set_renewal)
        if renewal_changed:
            changed_fields.add("next_renewal_date")

        # --- 4. Save if changes were made ---
        if changed_fields:
            logger.info(f"Subscription '{original_subscription.name}' (ID: {subscription_id}) updated. Changed fields: {changed_fields}")
            self._save_subscriptions()
            return True

        logger.info(f"No effective changes applied to subscription ID: {subscription_id}")
        return False # No changes were effectively made

    def delete_subscription(self, subscription_id: str) -> bool:
        """Deletes a subscription by its ID and saves the data."""
        if subscription_id in self._subscriptions:
            deleted_name = self._subscriptions[subscription_id].name
            del self._subscriptions[subscription_id]
            self._save_subscriptions()
            logger.info(f"Subscription '{deleted_name}' deleted.") # Placeholder feedback
            return True
        return False

    # --- Helper/Utility Methods --- #

    def get_upcoming_events(self, days_ahead: int = 7) -> List[Tuple[Subscription, str]]:
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
            if sub.next_renewal_date and sub.status not in [SubscriptionStatus.TRIAL, SubscriptionStatus.CANCELLED, SubscriptionStatus.INACTIVE] and today <= sub.next_renewal_date <= target_date:
                event_desc = f"renews on {sub.next_renewal_date.isoformat()}"
                upcoming_events.append((sub, event_desc))

            # Check for upcoming trial ends
            if sub.trial_end_date and sub.status == SubscriptionStatus.TRIAL and today <= sub.trial_end_date <= target_date:
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

    # --- Update Helper Methods ---

    def _validate_and_prepare_updates(self, subscription: Subscription, update_data: Dict[str, Any]) -> tuple[Dict[str, Any], Set[str]]:
        """Validates input data against subscription fields and types.

        Args:
            subscription: The original subscription object.
            update_data: The dictionary of proposed updates.

        Returns:
            A tuple containing:
                - dict: Validated data ready to be applied.
                - set: Fields that changed compared to the original subscription.
        """
        valid_updates: Dict[str, Any] = {}
        changed_fields: Set[str] = set()
        type_hints = get_type_hints(Subscription)

        for key, value in update_data.items():
            if key == "id" or not hasattr(subscription, key):
                if key != "id":
                    logger.warning(f"Attempted to update non-existent field '{key}' for sub ID {subscription.id}. Skipping.")
                continue

            original_value = getattr(subscription, key)
            actual_type = type_hints.get(key)
            origin = get_origin(actual_type)
            args = get_args(actual_type)
            is_optional = origin is Optional or (origin is Union and type(None) in args) or (origin is UnionType and type(None) in args)
            base_type = args[0] if is_optional and args and args[0] is not type(None) else None if is_optional else actual_type
            # Handle Unions like Optional[date] -> date
            if origin is Union or origin is UnionType:
                 non_none_args = [t for t in args if t is not type(None)]
                 if len(non_none_args) == 1:
                     base_type = non_none_args[0]
                 elif not non_none_args: # Should not happen for valid type hints
                     base_type = actual_type # Fallback

            # Allow None for optional fields
            if value is None and is_optional:
                if original_value is not None:
                    valid_updates[key] = None
                    changed_fields.add(key)
                continue
            elif value is None:
                logger.warning(f"Attempted to set non-optional field '{key}' to None for sub ID {subscription.id}. Skipping.")
                continue

            # Handle specific type conversions/validations
            expected_type = base_type
            converted_value = value
            valid = False
            try:
                if expected_type == date and isinstance(value, str):
                    converted_value = date.fromisoformat(value)
                elif expected_type == BillingCycle and isinstance(value, str):
                    converted_value = BillingCycle(value)
                elif expected_type == SubscriptionStatus and isinstance(value, str):
                    converted_value = SubscriptionStatus(value)
                elif expected_type == float and not isinstance(value, float):
                    converted_value = float(value)
                elif expected_type == str and not isinstance(value, str):
                    converted_value = str(value).strip()
                # Ensure final value is of the expected type (or can be coerced)
                if isinstance(converted_value, expected_type):
                    valid = True
                else:
                    # Try direct coercion as a last resort
                    converted_value = expected_type(value)
                    if isinstance(converted_value, expected_type):
                         valid = True

                if valid and (key == 'cost' and converted_value < 0):
                    logger.warning(f"Cost cannot be negative ('{value}'). Skipping update for '{key}' for sub ID {subscription.id}.")
                    valid = False

                if valid:
                    if original_value != converted_value:
                        valid_updates[key] = converted_value
                        changed_fields.add(key)
                elif not isinstance(converted_value, expected_type):
                    # If validation failed after coercion attempts
                    raise TypeError(f"Final type mismatch: expected {expected_type}, got {type(converted_value)}")

            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid type/value for field '{key}' ('{value}'). Expected {expected_type}. Error: {e}. Skipping update for sub ID {subscription.id}.")

        return valid_updates, changed_fields

    def _ensure_status_consistency(self, subscription: Subscription) -> bool:
        """Ensures status is TRIAL if trial_end_date is set, and vice-versa.

        Args:
            subscription: The subscription object (potentially modified).

        Returns:
            True if the status was changed, False otherwise.
        """
        changed = False
        trial_end_date = getattr(subscription, "trial_end_date", None)
        current_status = getattr(subscription, "status", None)

        if trial_end_date and current_status != SubscriptionStatus.TRIAL:
            status_msg = f"Status auto-updated to TRIAL for sub ID {subscription.id} because trial_end_date was set."
            logger.info(status_msg)
            print(status_msg)  # Print to stdout for test capture
            setattr(subscription, "status", SubscriptionStatus.TRIAL)
            changed = True
        elif not trial_end_date and current_status == SubscriptionStatus.TRIAL:
            status_msg = f"Status auto-updated to ACTIVE for sub ID {subscription.id} because trial_end_date was removed/unset."
            logger.info(status_msg)
            print(status_msg)  # Print to stdout for test capture
            setattr(subscription, "status", SubscriptionStatus.ACTIVE)
            changed = True
        return changed

    def _update_renewal_date(self, subscription: Subscription, changed_fields: Optional[Set[str]] = None, manually_set: bool = False) -> bool:
        """Calculates, sets, or clears the next_renewal_date based on status and changes.

        Args:
            subscription: The subscription object.
            changed_fields: Set of fields changed in the current operation (relevant for updates).
            manually_set: Flag indicating if next_renewal_date was explicitly set in this operation.

        Returns:
            True if the next_renewal_date was changed, False otherwise.
        """
        original_renewal_date = getattr(subscription, "next_renewal_date", None)
        current_status = getattr(subscription, "status")
        needs_recalc = False
        date_changed = False

        # Determine if recalc is needed (only relevant for updates)
        if changed_fields and any(f in changed_fields for f in ["start_date", "billing_cycle", "status"]):
            needs_recalc = True

        # --- Logic --- #
        new_renewal_date = original_renewal_date

        # 1. If manually set during update, respect it (unless status becomes TRIAL)
        if manually_set and current_status != SubscriptionStatus.TRIAL:
            # The date was already set by _apply_subscription_updates
            needs_recalc = False # Manual overrides auto-calc
        # 2. If status is TRIAL, renewal must be None
        elif current_status == SubscriptionStatus.TRIAL:
            new_renewal_date = None
            needs_recalc = False
        # 3. If status is CANCELLED (but not INACTIVE), renewal should be None
        elif current_status == SubscriptionStatus.CANCELLED:
             new_renewal_date = None
             needs_recalc = False
        # 4. If adding a new subscription or relevant fields changed during update:
        elif needs_recalc or changed_fields is None: # changed_fields is None implies adding new
            try:
                new_renewal_date = calculate_next_renewal_date(
                    getattr(subscription, "start_date"),
                    getattr(subscription, "billing_cycle")
                )
            except ValueError as e:
                logger.warning(f"Could not calculate renewal date for {subscription.name} ({subscription.id}): {e}. Setting to None.")
                new_renewal_date = None

        if original_renewal_date != new_renewal_date:
            setattr(subscription, "next_renewal_date", new_renewal_date)
            date_changed = True

        return date_changed

    def calculate_and_set_next_renewal(self, subscription: Subscription) -> None:
        """
        Calculate and set the next renewal date for a subscription.

        This is a helper method used internally when subscription details change.

        Args:
            subscription: The subscription to update
        """
        # Skip calculation for trials and "OTHER" billing cycle
        if subscription.status == SubscriptionStatus.TRIAL:
            subscription.next_renewal_date = None
            return

        try:
            if subscription.billing_cycle != BillingCycle.OTHER:
                subscription.next_renewal_date = calculate_next_renewal_date(
                    subscription.start_date, subscription.billing_cycle
                )
            else:
                # Can't calculate for OTHER billing cycle
                subscription.next_renewal_date = None

        except ValueError as e:
            logger.warning(f"Could not calculate renewal date: {e}")
            subscription.next_renewal_date = None

    # --- Financial Calculation Methods --- #

    def calculate_cost_per_category(self, period: str = 'monthly') -> Dict[str, float]:
        """
        Calculates the approximate cost per category for all active subscriptions,
        normalized to the specified period ('monthly' or 'annually').

        Args:
            period: The target period ('monthly' or 'annually'). Defaults to 'monthly'.

        Returns:
            A dictionary mapping category names to their total normalized cost for the period.
            Subscriptions without a category are grouped under 'Uncategorized'.
        """
        cost_by_category: Dict[str, float] = defaultdict(float)
        period = period.lower()
        if period not in ['monthly', 'annually']:
            raise ValueError("Period must be 'monthly' or 'annually'.")

        for sub in self.get_all_subscriptions():
            # Only include active subscriptions in recurring cost calculations
            if sub.status == SubscriptionStatus.ACTIVE:
                try:
                    normalized_cost = self._normalize_cost_to_period(
                        sub.cost, sub.billing_cycle, target_period=period
                    )
                    # Use 'Uncategorized' if category is missing or empty
                    category = sub.category.strip() if sub.category and sub.category.strip() else "Uncategorized"
                    cost_by_category[category] += normalized_cost
                except ValueError as e:
                     # Error during normalization (should be rare with period check)
                     logger.warning(f"Could not normalize cost for category calculation for {sub.name}: {e}")
                except AttributeError:
                     # Handle case where subscription object might miss expected attributes
                     logger.error(f"Subscription object {sub.name} ({sub.id}) is missing expected attributes (e.g., cost, billing_cycle, category, status).")
                except Exception as e:
                    # Catch any other unexpected errors during processing a subscription
                    logger.error(f"Unexpected error processing subscription {sub.name} ({sub.id}) for category cost: {e}")


        # Ensure all defined categories exist in the result, even if their cost is 0
        all_categories = self.get_categories()
        for cat in all_categories:
            if cat not in cost_by_category:
                cost_by_category[cat] = 0.0
        # Also ensure 'Uncategorized' exists if needed
        if "Uncategorized" not in cost_by_category:
             # Check if any active sub actually was uncategorized before adding the key
             has_uncategorized = any(
                 sub.status == SubscriptionStatus.ACTIVE and (not sub.category or not sub.category.strip())
                 for sub in self.get_all_subscriptions()
             )
             if has_uncategorized:
                 cost_by_category["Uncategorized"] = 0.0


        return dict(cost_by_category) # Convert back to regular dict

    def calculate_spending_forecast(self, start_date: date, end_date: date) -> float:
        """Calculates the total cost of subscription renewals within a given date range.

        Args:
            start_date: The inclusive start date of the forecast period.
            end_date: The inclusive end date of the forecast period.

        Returns:
            The total estimated cost of renewals within the specified range.
        """
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise TypeError("start_date and end_date must be date objects.")
        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date.")

        total_forecast_cost = 0.0

        for sub in self.get_all_subscriptions():
            # Only forecast for active, recurring subscriptions
            if sub.status != SubscriptionStatus.ACTIVE or sub.billing_cycle == BillingCycle.OTHER:
                continue

            # Find the first renewal date on or after the forecast start date
            current_renewal_date = sub.next_renewal_date

            # If the stored renewal date is missing or before the forecast period, calculate forward
            # from the start_date or subscription start date if needed.
            if not current_renewal_date or current_renewal_date < start_date:
                 # Calculate the first renewal *after* or *on* the start_date
                 # We might need multiple steps if the cycle is short and start_date is far from the last renewal
                temp_date = sub.next_renewal_date or sub.start_date
                while temp_date < start_date:
                     try:
                         # Pass the most recent known date (temp_date) to calculate the next one
                         temp_date = calculate_next_renewal_date(sub.start_date, sub.billing_cycle, last_renewal=temp_date)
                         # If calculate_next_renewal_date returns None (e.g., for OTHER cycle, though filtered above),
                         # or raises an error, break the loop for this subscription.
                         if temp_date is None:
                             break
                     except ValueError:
                          # Handle cases where next date can't be calculated (should be rare here)
                          logger.warning(f"Could not calculate future renewal date for {sub.name} ({sub.id}) from {temp_date}. Skipping forecast.")
                          temp_date = None # Signal to break outer loop
                          break
                current_renewal_date = temp_date

            # Now, iterate through renewals within the forecast period [start_date, end_date]
            while current_renewal_date and current_renewal_date <= end_date:
                # Add cost if the renewal falls within the period (it should by the loop condition)
                total_forecast_cost += sub.cost

                # Calculate the next renewal date *after* the current one
                try:
                    current_renewal_date = calculate_next_renewal_date(sub.start_date, sub.billing_cycle, last_renewal=current_renewal_date)
                    if current_renewal_date is None:
                         break # Stop if next date can't be determined
                except ValueError:
                    logger.warning(f"Could not calculate subsequent renewal date for {sub.name} ({sub.id}) from {current_renewal_date}. Stopping forecast for this sub.")
                    break # Stop forecasting for this subscription

        return total_forecast_cost

    def calculate_cost_per_period(self, period: str = 'monthly') -> float:
         """
         Calculates the approximate total cost of all active subscriptions,
         normalized to the specified period ('monthly' or 'annually').
         """
         total_cost_for_period = 0.0
         period = period.lower()
         if period not in ['monthly', 'annually']:
             raise ValueError("Period must be 'monthly' or 'annually'.")

         for sub in self.get_all_subscriptions():
             # Only include active subscriptions in recurring cost calculations
             if sub.status == SubscriptionStatus.ACTIVE:
                 try:
                     normalized_cost = self._normalize_cost_to_period(sub.cost, sub.billing_cycle, target_period=period)
                     total_cost_for_period += normalized_cost
                 except ValueError as e:
                      # Should not happen with validated period, but good practice
                      logger.warning(f"Warning: Could not normalize cost for {sub.name}: {e}")
         return total_cost_for_period

    def _get_annual_factor(self, cycle: BillingCycle) -> float:
        """Returns the number of times a billing cycle occurs per year."""
        if cycle == BillingCycle.MONTHLY:
            return 12.0
        elif cycle == BillingCycle.YEARLY:
            return 1.0
        elif cycle == BillingCycle.QUARTERLY:
            return 4.0
        elif cycle == BillingCycle.WEEKLY:
            return 52.0
        elif cycle == BillingCycle.BI_ANNUALLY: # Assuming twice a year
            return 2.0
        else: # OTHER
            return 0.0 # Non-recurring cycles don't contribute to annual cost this way

    def _normalize_cost_to_period(self, cost: float, cycle: BillingCycle, target_period: str = 'monthly') -> float:
        """Normalizes subscription cost to a target period (monthly or annually)."""
        annual_cost = cost * self._get_annual_factor(cycle)

        if target_period.lower() == 'monthly':
            return annual_cost / 12.0 if annual_cost > 0 else 0.0
        elif target_period.lower() == 'annually':
            return annual_cost
        else:
            raise ValueError(f"Unsupported target period: {target_period}. Use 'monthly' or 'annually'.")

    def check_budget_alerts(self) -> List[str]:
        """Checks if the current total monthly spending exceeds the set monthly budget.

        Returns:
            A list of alert messages. Currently only checks for monthly budget exceeded.
            Returns an empty list if no budget is set or if spending is within budget.
        """
        alerts = []
        budget_settings = self.get_budget() # Get the full budget dict
        monthly_budget_data = budget_settings.get("monthly", {}) # Get the monthly sub-dict safely
        global_monthly_budget = monthly_budget_data.get("global") # Get the global value

        # Only check if a global monthly budget is actually set (is a number, not None)
        if isinstance(global_monthly_budget, (int, float)) and global_monthly_budget >= 0:
            try:
                current_monthly_cost = self.calculate_cost_per_period(period='monthly')

                if current_monthly_cost > global_monthly_budget:
                    overage = current_monthly_cost - global_monthly_budget
                    # Format the alert message clearly
                    alert_msg = (
                        f"Budget Alert: Monthly spending ({current_monthly_cost:.2f}) "
                        f"exceeds global budget ({global_monthly_budget:.2f}) by {overage:.2f}."
                    )
                    alerts.append(alert_msg)

            except ValueError as e:
                 # This might happen if calculate_cost_per_period fails, though unlikely
                 logger.error(f"Error calculating monthly cost for budget check: {e}")
                 alerts.append("Alert: Could not check budget due to calculation error.")
            except Exception as e:
                 # Catch any other unexpected errors
                 logger.error(f"Unexpected error during global budget check: {e}")
                 alerts.append("Alert: An unexpected error occurred while checking the global budget.")

        # --- Check Per-Category Budgets ---
        category_budgets = monthly_budget_data.get("categories", {})
        if category_budgets: # Only proceed if there are category budgets defined
            try:
                monthly_costs_per_category = self.calculate_cost_per_category(period='monthly')

                for category, budget in category_budgets.items():
                    # Check if a specific budget is set for this category (not None, is number, non-negative)
                    if isinstance(budget, (int, float)) and budget >= 0:
                        current_category_cost = monthly_costs_per_category.get(category, 0.0)
                        if current_category_cost > budget:
                            cat_overage = current_category_cost - budget
                            alert_msg = (
                                f"Budget Alert: Monthly spending for '{category}' ({current_category_cost:.2f}) "
                                f"exceeds budget ({budget:.2f}) by {cat_overage:.2f}."
                            )
                            alerts.append(alert_msg)

            except Exception as e:
                # Catch any errors during category budget checking
                logger.error(f"Unexpected error during category budget check: {e}")
                alerts.append("Alert: An unexpected error occurred while checking category budgets.")

        return alerts

    # --- Filtering and Sorting Methods ---

    def get_subscriptions_by_status(self, status: SubscriptionStatus) -> List[Subscription]:
        """Filter subscriptions by their status."""
        return [sub for sub in self._subscriptions.values() if sub.status == status]

    def get_subscriptions_by_category(self, category: str) -> List[Subscription]:
        """Filter subscriptions by their category (case-insensitive)."""
        return [sub for sub in self._subscriptions.values() if sub.category.lower() == category.lower()]

    def get_subscriptions_by_cost_range(self, min_cost: float, max_cost: float) -> List[Subscription]:
        """Filter subscriptions by cost range (inclusive)."""
        return [sub for sub in self._subscriptions.values() if min_cost <= sub.cost <= max_cost]

    def get_subscriptions_by_billing_cycle(self, cycle: BillingCycle) -> List[Subscription]:
        """Filter subscriptions by their billing cycle."""
        return [sub for sub in self._subscriptions.values() if sub.billing_cycle == cycle]

    def get_subscriptions_by_renewal_range(self, start_date: date, end_date: date) -> List[Subscription]:
        """Filter subscriptions by next renewal date range (inclusive)."""
        return [sub for sub in self._subscriptions.values()
                if sub.next_renewal_date and start_date <= sub.next_renewal_date <= end_date]

    def get_all_subscriptions_sorted(self, sort_by: str = "name", ascending: bool = True) -> List[Subscription]:
        """Get all subscriptions sorted by a specified field."""
        subs = list(self._subscriptions.values())

        # Handle sorting by renewal date where it might be None
        if sort_by == "next_renewal_date":
            # Sort None values to the end regardless of ascending/descending
            subs.sort(key=lambda x: (x.next_renewal_date is None, x.next_renewal_date), reverse=not ascending)
        else:
            # Default sort for other fields
            try:
                subs.sort(key=lambda x: getattr(x, sort_by), reverse=not ascending)
            except AttributeError:
                logger.error(f"Invalid sort key: {sort_by}")
                # Return unsorted or raise error
                return list(self._subscriptions.values())
        return subs

    def search_subscriptions(self, query: str) -> List[Subscription]:
        """Search subscriptions by name, category, notes, or service provider (case-insensitive)."""
        query = query.lower()
        return [sub for sub in self._subscriptions.values()
                if (query in sub.name.lower())
                or (sub.category and query in sub.category.lower())
                or (sub.notes and query in sub.notes.lower())
                or (sub.service_provider and query in sub.service_provider.lower())]