# src/tui/screens/MainScreen.py
import sys
import os
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Set
from textual.app import ComposeResult # Removed App, Binding
from textual.reactive import var # Import var for reactive attributes
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Button, Placeholder, Static, ListView, ListItem, Label,
)
from textual.containers import Horizontal, Vertical, Container
from datetime import date

# Import the model
from ...models.subscription import Subscription, SubscriptionStatus

# Import the new dialog
from ..dialogs.AddEditDialog import AddEditDialog
from ..dialogs.ConfirmDialog import ConfirmDialog # Import confirmation dialog
from ..components.FinancialSummary import FinancialSummary # Import FinancialSummary
from ..components.CustomCalendarView import CustomCalendarView # Import widget and message

if TYPE_CHECKING:
    from ...services.subscription_service import SubscriptionService

# --- Custom ListItem for Subscriptions ---
class SubscriptionListItem(ListItem):
    """A ListItem widget to display subscription information."""
    def __init__(self, subscription: Subscription):
        super().__init__()
        self.subscription = subscription
        # Display format: Name ($Price - Next Renewal: YYYY-MM-DD or Status)
        renewal_info = subscription.next_renewal_date.strftime('%Y-%m-%d') if subscription.next_renewal_date else subscription.status.value

        # Add ID to help with debugging
        display_text = f"{subscription.name} (${subscription.cost:.2f} - Next: {renewal_info}) [ID: {subscription.id[:8]}]"
        self.item_label = Label(display_text)

        # Set a CSS class based on status for styling
        self.add_class(f"status-{subscription.status.value}")

    def compose(self) -> ComposeResult:
        yield self.item_label

    # Optional: Add styling or more complex layout here if needed


# --- Main Screen ---
class MainScreen(Screen):
    """The main screen for the TUI application."""

    BINDINGS = [
        ("a", "add_sub", "Add"),
        ("e", "edit_sub", "Edit"),
        ("d", "delete_sub", "Delete"),
        ("r", "refresh", "Refresh"), # Add refresh binding
    ]

    # --- Reactive Variables ---
    # Store the ID of the currently selected subscription (Moved to class level)
    selected_subscription_id: var[Optional[str]] = var(None) # type: ignore

    def __init__(self, service: "SubscriptionService", name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name, id, classes)
        self.service = service
        self.sub_list_view: Optional[ListView] = None
        # Removed initialization from __init__
        # Update type hint for the calendar reference
        self.calendar: Optional[CustomCalendarView] = None # Changed type hint
        self.financial_summary: Optional[FinancialSummary] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the main screen."""
        with Horizontal(id="main-split"):
            with Vertical(id="left-pane"):
                yield Static("Subscriptions", id="sub-list-title")
                # Replace Placeholder with ListView
                yield Container(ListView(id="sub-list"), id="sub-list-container")
                with Horizontal(id="button-bar"):
                    yield Button("Add", id="add-button", variant="success")
                    yield Button("Edit", id="edit-button", disabled=True)
                    yield Button("Delete", id="delete-button", variant="error", disabled=True)

            with Vertical(id="right-pane"):
                yield Static("Upcoming Renewals", id="calendar-title") # Add title for calendar
                # Use the custom calendar view
                yield CustomCalendarView(id="calendar-view") # Changed instantiation
                yield FinancialSummary(service=self.service, id="financial-summary") # Add the summary widget

    def on_mount(self) -> None:
        """Called when the screen is mounted. Load initial data."""
        self.sub_list_view = self.query_one("#sub-list", ListView)
        # Update query selector and type
        self.calendar = self.query_one(CustomCalendarView) # Changed type
        self.financial_summary = self.query_one(FinancialSummary)
        self.log("MainScreen mounted, loading all data...")

        # Add diagnostic notification to check the data path
        data_path = self.service.data_path
        self.notify(f"Using data path: {data_path}", title="Diagnostic")

        # Check if data file exists
        if os.path.exists(data_path):
            self.notify(f"Data file exists at {data_path}", title="Diagnostic")
        else:
            self.notify(f"Data file does not exist at {data_path}", title="Diagnostic")

        self._refresh_all_data()

        # Check if subscriptions were loaded after refresh
        subs = self.service.get_all_subscriptions()
        self.notify(f"Loaded {len(subs)} subscriptions", title="Diagnostic")
        for sub in subs:
            self.log.info(f"Loaded subscription: {sub.name} (ID: {sub.id})")

        # Force a second refresh to make sure the list is populated
        self.set_timer(1, self._refresh_all_data)

    def _refresh_all_data(self) -> None:
        """Refreshes all dynamic data on the screen."""
        self.log("Refreshing all screen data...")
        self._refresh_subscription_list() # Also updates button states
        self._refresh_right_pane()

    def _refresh_subscription_list(self) -> None:
        """Clears and repopulates the subscription list."""
        if not self.sub_list_view:
            self.log.error("Subscription list view not found during refresh.")
            return

        self.sub_list_view.clear()
        self.selected_subscription_id = None # Clear selection

        try:
            self._extracted_from__refresh_subscription_list_11()
        except Exception as e:
            # Handle error display more gracefully
            # Maybe push an error screen or show a notification
            self.log.error(f"Error refreshing subscription list: {e}")
            self.notify(f"Error loading subscriptions: {e}", title="Error", severity="error")
            # You could potentially add a static message here too

        # Ensure buttons are in correct state after refresh
        self._update_button_states()

    # TODO Rename this here and in `_refresh_subscription_list`
    def _extracted_from__refresh_subscription_list_11(self):
        self.log.info("Getting all subscriptions from service...")
        subs = self.service.get_all_subscriptions()
        self.log.info(f"Retrieved {len(subs)} subscriptions")

        # Log each subscription for debugging
        for sub in subs:
            self.log.info(f"Retrieved subscription: {sub.name} (ID: {sub.id})")

        subs.sort(key=lambda s: s.name.lower()) # Sort alphabetically by name

        if not subs:
            # Optionally display a message within the ListView container or as a Static widget
            self.log.info("No subscriptions found.")
            # Add a message so the user knows there are no subscriptions
            from textual.widgets import Static
            message = Static("No subscriptions found. Press 'a' or click 'Add' to create one.", classes="no-subs-message")
            self.sub_list_view.append(message)
        else:
            self.log.info(f"Populating list with {len(subs)} subscriptions.")
            for sub in subs:
                self.log.info(f"Creating list item for subscription: {sub.name}")
                list_item = SubscriptionListItem(sub)
                list_item.id = f"sub-{sub.id}" # Assign unique ID based on subscription ID
                self.sub_list_view.append(list_item)
                self.log.info(f"Added subscription item to list: {sub.name}")

    def _refresh_right_pane(self) -> None:
        """Refreshes the calendar and financial summary."""
        self.log("Refreshing right pane (Custom Calendar & Summary)...")
        # --- Refresh Calendar ---
        if self.calendar:
            try:
                events_raw = self.service.get_upcoming_events(days_ahead=60) # Fetch data
                new_highlighted_dates: Set[date] = {
                    sub.next_renewal_date
                    for sub, desc in events_raw
                    if sub.next_renewal_date
                }
                # Call the method on the custom widget to update its highlights
                self.calendar.set_highlighted_dates(new_highlighted_dates)

            except Exception as e:
                self.log.error(f"Error fetching upcoming events for custom calendar: {e}")
                self.notify(f"Error updating calendar: {e}", title="Error", severity="error")
                # Optionally clear highlights on error
                if self.calendar: # Check again, might have been removed
                    self.calendar.set_highlighted_dates(set())

        # --- Refresh Financial Summary ---
        if self.financial_summary:
            try:
                self.financial_summary.refresh_summary()
            except Exception as e:
                 self.log.error(f"Error refreshing financial summary widget: {e}")
                 self.notify(f"Error updating financial summary: {e}", title="Error", severity="error")

    def watch_selected_subscription_id(self, old_id: Optional[str], new_id: Optional[str]) -> None:
        """Called when the selected_subscription_id changes."""
        self.log(f"Selection changed from {old_id} to {new_id}")
        self._update_button_states()

    def _update_button_states(self) -> None:
        """Enable/disable Edit and Delete buttons based on selection."""
        has_selection = self.selected_subscription_id is not None
        edit_button = self.query_one("#edit-button", Button)
        delete_button = self.query_one("#delete-button", Button)
        edit_button.disabled = not has_selection
        delete_button.disabled = not has_selection

    # --- Event Handlers ---
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle subscription selection in the ListView."""
        list_item = event.item
        if isinstance(list_item, SubscriptionListItem):
            self.selected_subscription_id = list_item.subscription.id
            self.log(f"Selected subscription ID: {self.selected_subscription_id}")
        else:
            # This might happen if other item types are ever added or if selection is cleared
            self.selected_subscription_id = None
            self.log("Selection cleared or item is not a SubscriptionListItem.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
         """Handle button presses by calling the appropriate action."""
         button_id = event.button.id
         if button_id == "add-button":
             self.action_add_sub()
         elif button_id == "edit-button":
             # Guard against action if button is somehow pressed while disabled
             if self.selected_subscription_id is not None:
                 self.action_edit_sub()
             else:
                self.log.warning("Edit button pressed but no subscription selected.")
         elif button_id == "delete-button":
             if self.selected_subscription_id is not None:
                 self.action_delete_sub()
             else:
                 self.log.warning("Delete button pressed but no subscription selected.")

    # --- Callback methods for dialogs ---
    def _on_add_dialog_closed(self, data: Optional[Dict[str, Any]]) -> None:
        """Callback function for when the Add dialog is closed."""
        if data:
            self.log.info(f"Add dialog returned data: {data}")
            try:
                self._extracted_from__on_add_dialog_closed_7(data)
            except Exception as e:
                self._extracted_from__on_edit_dialog_closed_29(
                    'Failed to add subscription: ', e
                )
        else:
            self.log.info("Add dialog cancelled or returned no data.")

    # TODO Rename this here and in `_on_add_dialog_closed`
    def _extracted_from__on_add_dialog_closed_7(self, data):
        # Remove 'id' as it's auto-generated for new subs
        if 'id' in data:
            self.log.info("Removing 'id' from data to let it be auto-generated")
            del data['id']

        # Log the data being used to create subscription
        self.log.info(f"Creating new subscription with data: {data}")

        # Create subscription
        new_sub = Subscription(**data)
        self.log.info(f"Created Subscription object: {new_sub.name} (ID: {new_sub.id})")

        # Add it to service
        self.service.add_subscription(new_sub)
        self.log.info(f"Added subscription to service: {new_sub.name} (ID: {new_sub.id})")

        # Notify user
        self.notify(f"Subscription '{new_sub.name}' added.", title="Success")

        # Refresh the UI
        self.log.info("Refreshing UI after adding subscription")
        self._refresh_all_data()

    def _on_edit_dialog_closed(self, data: Optional[Dict[str, Any]]) -> None:
        """Callback function for when the Edit dialog is closed."""
        if data:
            self.log.info(f"Edit dialog returned data: {data}")
            try:
                # Ensure ID is present for updating
                if data.get('id') is None:
                    raise ValueError("Subscription ID missing for update.")

                updated_sub = Subscription(**data)
                self.service.update_subscription(updated_sub)
                self.notify(f"Subscription '{updated_sub.name}' updated.", title="Success")
                self._refresh_all_data() # Refresh everything
            except Exception as e:
                self._extracted_from__on_edit_dialog_closed_29(
                    'Failed to update subscription: ', e
                )
        else:
            self.log.info("Edit dialog cancelled or returned no data.")

    #  Rename this here and in `_on_add_dialog_closed` and `_on_edit_dialog_closed`
    def _extracted_from__on_edit_dialog_closed_29(self, arg0, e):
        error_msg = f"{arg0}{e}"
        self.log.error(error_msg)
        self.notify(error_msg, title="Error", severity="error")

    # --- Callback for Delete Confirmation ---
    def _handle_delete_confirmation(self, confirmed: bool) -> None:
        """Callback function for the delete confirmation dialog."""
        if confirmed:
            sub_id_to_delete = self.selected_subscription_id
            if sub_id_to_delete is not None:
                self.log.info(f"Delete confirmed for subscription ID: {sub_id_to_delete}")
                try:
                    sub = self.service.get_subscription(sub_id_to_delete)
                    sub_name = sub.name if sub else f"ID {sub_id_to_delete}" # Get name before deleting

                    if not sub:
                        # Should ideally not happen if we just selected it, but check again.
                        self.notify(f"Subscription {sub_name} not found for deletion.", title="Error", severity="error")
                        self._refresh_subscription_list()
                        return

                    if self.service.delete_subscription(sub_id_to_delete):
                        self.log.info(f"Action: Delete Subscription ID {sub_id_to_delete} - Success")
                        self.notify(f"Subscription '{sub_name}' deleted.", title="Success")
                    else:
                        # Service indicated failure (e.g., ID not found at the last moment)
                        self.log.warning(f"Action: Delete Subscription ID {sub_id_to_delete} - Failed (service returned false)")
                        self.notify(f"Failed to delete subscription '{sub_name}'. It might have been removed already.", title="Error", severity="error")
                    self._refresh_all_data() # Refresh everything
                except Exception as e:
                    self._extracted_from_action_delete_sub_26(
                        'Failed to delete subscription ID ', sub_id_to_delete, e
                    )
            else:
                # This case should technically not happen if the button was enabled
                self.log.warning("Delete confirmation callback received, but no subscription was selected.")
        else:
            self.log.info("Delete action cancelled by user.")
            self.notify("Delete cancelled.", title="Info")

    # --- Action Handlers (Updated) ---
    def action_add_sub(self) -> None:
        """Action to open the Add Subscription dialog."""
        self.log("Action: Add Subscription triggered.")
        # Get current categories using the updated service method
        available_categories = set(self.service.get_categories())
        # available_categories.add("Uncategorized") # get_categories should handle this if needed
        # Pass categories and service to the dialog
        self.app.push_screen(
            AddEditDialog(service=self.service, available_categories=available_categories),
            self._on_add_dialog_closed
        )

    def action_edit_sub(self) -> None:
        """Action to open the Edit Subscription dialog for the selected item."""
        selected_id = self.selected_subscription_id
        if selected_id:
            self.log(f"Action: Edit Subscription triggered for ID: {selected_id}")
            try:
                sub_to_edit = self.service.get_subscription_by_id(selected_id)
                if sub_to_edit:
                    # Get current categories using the updated service method
                    available_categories = set(self.service.get_categories())
                    # available_categories.add("Uncategorized") # get_categories should handle this
                    # Pass the subscription, categories and service to the dialog
                    self.app.push_screen(
                        AddEditDialog(
                            subscription=sub_to_edit,
                            available_categories=available_categories,
                            service=self.service # Pass service here too
                        ),
                        self._on_edit_dialog_closed
                    )
                else:
                    self.log.warning(f"Attempted to edit subscription with ID {selected_id}, but it was not found.")
                    self.notify("Selected subscription not found. Please refresh.", title="Error", severity="warning")
                    self.selected_subscription_id = None # Deselect if not found
            except Exception as e:
                self.log.error(f"Error retrieving subscription {selected_id} for editing: {e}")
                self.notify(f"Error loading subscription details: {e}", title="Error", severity="error")
        else:
            self.log.warning("Edit action triggered but no subscription selected.")
            self.notify("Please select a subscription to edit.", title="Action Required", severity="warning")

    def action_delete_sub(self) -> None:
        """Action to prompt for deleting the selected subscription."""
        if self.selected_subscription_id is not None:
            sub_id = self.selected_subscription_id
            try:
                sub = self.service.get_subscription(sub_id)
                if sub:
                    sub_name = sub.name
                    self.log(f"Action: Delete Subscription ID {sub_id} ('{sub_name}') - Showing confirmation")
                    # Show the confirmation dialog
                    confirm_message = f"Are you sure you want to delete '{sub_name}'?"
                    self.app.push_screen(ConfirmDialog(message=confirm_message), self._handle_delete_confirmation)
                else:
                    # Subscription disappeared between selection and delete button press
                    self.log.error(f"Subscription with ID {sub_id} not found when attempting to delete.")
                    self.notify("Selected subscription not found. It may have already been deleted.", title="Error", severity="error")
                    self._refresh_subscription_list() # Refresh the list
            except Exception as e:
                self._extracted_from_action_delete_sub_26(
                    'Error preparing delete confirmation for ID ', sub_id, e
                )
        else:
            self.notify("No subscription selected to delete.", title="Warning", severity="warning")
    def _extracted_from_action_delete_sub_26(self, arg0, arg1, e):
        error_msg = f"{arg0}{arg1}: {e}"
        self.log.error(error_msg)
        self.notify(error_msg, title="Error", severity="error")
    def _extracted_from_action_delete_sub_26(self, arg0, arg1, e):
        error_msg = f"{arg0}{arg1}: {e}"
        self.log.error(error_msg)
        self.notify(error_msg, title="Error", severity="error")

    def action_refresh(self) -> None:
        """Refreshes all data on the screen."""
        self.log("Action: Refresh All Data")
        self._refresh_all_data()
        self.notify("Screen data refreshed.", title="Success", severity="information")

    # --- Custom Calendar Event Handler ---
    def on_custom_calendar_view_date_selected(self, event: CustomCalendarView.DateSelected) -> None:
        """Handle date selection on the custom calendar."""
        selected_date = event.date # Get date from the custom message event
        self.log(f"Custom Calendar date selected: {selected_date}")

        renewing_subs: List[str] = []
        try:
            all_subs = self.service.get_all_subscriptions()
            renewing_subs = [
                f"- {s.name} (${s.cost:.2f})"
                for s in all_subs
                if s.next_renewal_date == selected_date and s.status == SubscriptionStatus.ACTIVE
            ]
        except Exception as e:
            self.log.error(f"Error getting renewals for date {selected_date}: {e}")
            self.notify(f"Error fetching renewals: {e}", title="Error", severity="error")
            return

        if renewing_subs:
            message = f"Renewals on {selected_date.strftime('%Y-%m-%d')}:\n" + "\n".join(renewing_subs)
            self.notify(message, title="Renewals", timeout=10)
        else:
            # Optionally notify if no renewals on selected date, or do nothing
            self.notify(f"No active renewals found for {selected_date.strftime('%Y-%m-%d')}.", title="Info", severity="information", timeout=5)
            pass