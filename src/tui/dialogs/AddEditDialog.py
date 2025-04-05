# src/tui/dialogs/AddEditDialog.py
from datetime import date, datetime
from typing import Optional, Any, Dict, cast, Set, Tuple, List, Union # Add Union

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Header, Footer, Input, Button, Label, Static, Select, TextArea, RadioSet, RadioButton # Keep this clean
)
from textual.containers import VerticalScroll, Container, Vertical, Horizontal # Import containers
from textual.css.query import NoMatches # Corrected import path again
from .CategoryPromptScreen import CategoryPromptScreen # Import the new screen
from .EditCategoryScreen import EditCategoryScreen # Import the new edit screen

from ...models.subscription import Subscription, SubscriptionStatus, BillingCycle

class AddEditDialog(ModalScreen[Optional[Dict[str, Any]]]):
    """A modal dialog screen for adding or editing subscriptions."""

    CSS = """
    AddEditDialog {
        align: center middle;
    }

    #dialog-container {
        width: 80;
        height: auto; /* Adjust based on content, maybe max-height */
        max-height: 90%;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    #dialog-container > VerticalScroll {
        padding: 0 1; /* Padding inside the scrollable area */
    }

    #dialog-container Label {
        margin-top: 1;
        margin-bottom: 0; /* Reduce space below label */
    }

    #dialog-container Input, #dialog-container Select, #dialog-container TextArea, #dialog-container RadioSet {
        margin-bottom: 1; /* Space below inputs */
        width: 100%;
    }

    #dialog-container TextArea {
        height: 4; /* Specific height for notes */
    }

    #button-group {
        padding-top: 1;
        align-horizontal: right;
        height: auto;
    }

    #button-group Button {
        margin-left: 2;
    }

    #category-group {
        width: 100%;
        height: auto;
        /* border: round red; /* For debugging */
    }

    #category-group > Select {
        width: 1fr; /* Select takes most space */
        margin-right: 1; /* Space between select and button */
    }

    #category-group > Button {
        /* width: auto; Removed auto width */
        min-width: 3; /* Set fixed width for '+' button */
        /* height: 1; Removed fixed height */
        margin: 0 0 0 1; /* Add left margin for spacing */
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        # Add binding for save if needed, e.g., ctrl+s
    ]

    def __init__(self,
                 subscription: Optional[Subscription] = None,
                 available_categories: Set[str] = set(),
                 service: Optional[Any] = None, # Add service parameter (use specific type if possible)
                 name: str | None = None,
                 id: str | None = None,
                 classes: str | None = None):
        super().__init__(name, id, classes)
        self.subscription = subscription # Store the subscription being edited, if any
        self.available_categories = available_categories # Store categories
        self.service = service # Store the service instance
        self.title = "Edit Subscription" if subscription else "Add New Subscription"

    def compose(self) -> ComposeResult:
        with Container(id="dialog-container"):
            yield Static(self.title, classes="dialog-title") # Use Static for title
            with VerticalScroll(): # Make content scrollable
                yield Label("Name:")
                yield Input(
                    value=self.subscription.name if self.subscription else "",
                    placeholder="e.g., Netflix Premium",
                    id="name-input"
                )

                yield Label("Price:")
                yield Input(
                    value=str(self.subscription.cost) if self.subscription else "",
                    placeholder="e.g., 19.99",
                    id="price-input",
                    type="number" # Use number type for validation (basic)
                )

                yield Label("Category:")
                with Horizontal(id="category-group"): # Added ID
                    # Prepare category options for Select
                    category_options = sorted(list(self.available_categories))
                    # Ensure the current category is an option, even if not in the initial set
                    current_category = self.subscription.category if self.subscription else "Uncategorized"
                    if current_category not in category_options:
                        category_options.insert(0, current_category) # Add it to the top

                    select_options = [(cat, cat) for cat in category_options]
                    initial_category_value = current_category if current_category in category_options else Select.BLANK

                    yield Select(
                        options=select_options,
                        value=initial_category_value,
                        id="category-select",
                        prompt="Select category..." # Add a prompt
                    )
                    yield Button("E", id="edit-category-button", variant="default") # Add Edit button
                    yield Button("+", id="add-category-button", variant="success") # Changed label to '+', kept variant

                yield Label("URL (Optional):") # New field
                yield Input(
                    value=self.subscription.url if self.subscription and self.subscription.url else "",
                    placeholder="e.g., https://netflix.com",
                    id="url-input"
                )

                yield Label("Username (Optional):") # New field
                yield Input(
                    value=self.subscription.username if self.subscription and self.subscription.username else "",
                    placeholder="e.g., user@example.com",
                    id="username-input"
                )

                yield Label("Start Date (YYYY-MM-DD):")
                start_date_val = self.subscription.start_date.isoformat() if self.subscription and self.subscription.start_date else date.today().isoformat()
                yield Input(
                    value=start_date_val,
                    placeholder="YYYY-MM-DD",
                    id="start-date-input"
                )

                yield Label("Billing Cycle:")
                cycle_options = [(cycle.value.capitalize(), cycle) for cycle in BillingCycle]
                initial_cycle = self.subscription.billing_cycle if self.subscription else BillingCycle.MONTHLY
                yield Select(
                    options=cycle_options,
                    value=initial_cycle,
                    id="billing-cycle-select"
                )

                yield Label("Next Renewal Date (YYYY-MM-DD, Optional):")
                renewal_date_val = self.subscription.next_renewal_date.isoformat() if self.subscription and self.subscription.next_renewal_date else ""
                yield Input(
                    value=renewal_date_val,
                    placeholder="YYYY-MM-DD or leave blank",
                    id="renewal-date-input"
                )

                yield Label("Status:")
                initial_status = self.subscription.status if self.subscription else SubscriptionStatus.ACTIVE
                with RadioSet(id="status-radioset"):
                    for status in SubscriptionStatus:
                         # Set initial checked state by setting RadioSet.value in on_mount
                        yield RadioButton(status.value.capitalize(), value=status, id=f"status-{status.name}") # Removed state=is_checked

                yield Label("Notes:")
                yield TextArea(
                    text=self.subscription.notes if self.subscription else "",
                    id="notes-textarea"
                )

            with Horizontal(id="button-group"):
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def on_mount(self) -> None:
        """Set initial values after mounting."""
        # Set the initial value for the status RadioSet
        initial_status = self.subscription.status if self.subscription else SubscriptionStatus.ACTIVE
        try:
            status_radioset = self.query_one("#status-radioset", RadioSet)
            status_radioset.value = initial_status
        except NoMatches:
            self.log.error("Could not find #status-radioset to set initial value.")
        # You might want to add focus here, e.g., self.query_one("#name-input").focus()

    def _validate_date_string(self, date_str: str, field_name: str, required: bool) -> Optional[date]:
        """Helper function to validate a date string."""
        if not date_str:
            if required:
                self.notify(f"{field_name} cannot be empty.", title="Validation Error", severity="error")
                return None # Indicate validation failure but value is None conceptually
            else:
                return None # Valid optional empty date
        try:
            # Attempt to parse the date string
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            return parsed_date
        except ValueError:
            # Handle incorrect format
            self.notify(f"Invalid date format for {field_name}. Use YYYY-MM-DD.", title="Validation Error", severity="error")
            return None # Indicate validation failure

    def _get_input_data(self) -> Optional[Dict[str, Any]]:
        """Retrieves and validates data from input fields."""
        try:
            name = self.query_one("#name-input", Input).value
            price_str = self.query_one("#price-input", Input).value
            # Get category from Select widget
            category_select = self.query_one("#category-select", Select)
            category = category_select.value if category_select.value != Select.BLANK else "Uncategorized"
            billing_cycle = self.query_one("#billing-cycle-select", Select).value
            status_radioset = self.query_one("#status-radioset", RadioSet)
            status = status_radioset.pressed_button.value if status_radioset.pressed_button else SubscriptionStatus.ACTIVE
            status = cast(SubscriptionStatus, status)
            notes = self.query_one("#notes-textarea", TextArea).text
            url = self.query_one("#url-input", Input).value.strip() # Get URL
            username = self.query_one("#username-input", Input).value.strip() # Get Username

            start_date_str = self.query_one("#start-date-input", Input).value
            renewal_date_str = self.query_one("#renewal-date-input", Input).value

            start_date = self._validate_date_string(start_date_str, "Start Date", required=True)
            if start_date is None and start_date_str:
                return None

            renewal_date = self._validate_date_string(renewal_date_str, "Renewal Date", required=False)
            if renewal_date is None and renewal_date_str:
                return None

            if not name:
                self.notify("Name cannot be empty.", title="Validation Error", severity="error")
                return None
            if not price_str:
                self.notify("Price cannot be empty.", title="Validation Error", severity="error")
                return None
            try:
                cost = float(price_str)
                if cost < 0:
                    raise ValueError("Cost cannot be negative.")
            except ValueError:
                self.notify("Invalid price format. Cost must be a non-negative number.", title="Validation Error", severity="error")
                return None
            if billing_cycle is None:
                self.notify("Billing cycle must be selected.", title="Validation Error", severity="error")
                return None
            if category is None: # Check if category is None (e.g., prompt selected)
                 self.notify("Category must be selected.", title="Validation Error", severity="error")
                 return None

            data = {
                "id": self.subscription.id if self.subscription else None,
                "name": name,
                "cost": cost,
                "category": category, # Use validated category
                "start_date": start_date,
                "billing_cycle": billing_cycle,
                "next_renewal_date": renewal_date,
                "status": status,
                "notes": notes,
                "url": url or None, # Add URL to data
                "username": username or None, # Add Username to data
            }
            return data
        except Exception as e:
            self.notify(f"Error processing form: {e}", title="Error", severity="error")
            self.log.error(f"Error getting input data: {e}")
            return None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-button":
            data = self._get_input_data()
            if data is not None:
                self.dismiss(data)
        elif event.button.id == "cancel-button":
            self.dismiss(None)
        elif event.button.id == "add-category-button": # Handle new button
            # Push the custom prompt screen
            self.app.push_screen(
                CategoryPromptScreen(),
                self._add_new_category
            )
        elif event.button.id == "edit-category-button": # Handle Edit button
            self._handle_edit_category_action()

    def _handle_edit_category_action(self) -> None:
        """Handles the logic for pressing the edit category button."""
        if not self.service:
            self.notify("Service not available to edit categories.", severity="error")
            return
        try:
            category_select = self.query_one("#category-select", Select)
            selected_category = category_select.value

            if selected_category is None or selected_category == Select.BLANK:
                self.notify("Please select a category to edit.", severity="warning")
                return
            if selected_category == "Uncategorized":
                 self.notify("Cannot edit the 'Uncategorized' category.", severity="warning")
                 return

            current_budget = self.service.get_monthly_category_budget(selected_category)
            self.app.push_screen(
                EditCategoryScreen(category_name=selected_category, current_budget=current_budget),
                self._handle_edit_category_result
            )

        except NoMatches:
            self.log.error("Could not find #category-select widget.")
            self.notify("Error accessing category list.", severity="error")
        except Exception as e:
             self.log.error(f"Error preparing category edit: {e}", exc_info=True)
             self.notify(f"Error preparing edit: {e}", severity="error")

    def _handle_edit_category_result(self, result: Optional[Union[float, str]]) -> None:
        """Callback function for EditCategoryScreen."""
        category_select = self.query_one("#category-select", Select) # Assume it exists here
        category_to_edit = category_select.value # Get category again

        if result == "__DELETE__":
            # Handle deletion
            if category_to_edit and self.service:
                deleted = self.service.delete_category(category_to_edit)
                if deleted:
                    self.notify(f"Category '{category_to_edit}' deleted.", severity="information")
                    # Refresh the category options in the Select widget
                    self._refresh_category_select()
                    # Optionally refresh main screen if needed via callback
                else:
                    self.notify(f"Failed to delete category '{category_to_edit}'.", severity="error")
            else:
                 self.log.warning("Delete signal received but category or service missing.")

        elif isinstance(result, (float, int)) or result is None:
            # Handle budget update (result is the new budget value or None)
            new_budget = result # result can be None here
            if category_to_edit and self.service:
                self.service.set_monthly_category_budget(category_to_edit, new_budget)
                budget_str = f"{new_budget:.2f}" if new_budget is not None else "None"
                self.notify(f"Budget for '{category_to_edit}' updated to {budget_str}.", severity="information")
            else:
                 self.log.warning("Budget update received but category or service missing.")

        # else: result is None (Cancel was pressed), do nothing

    def _refresh_category_select(self) -> None:
        """Helper to refresh the category select options after deletion/addition."""
        if not self.service:
            return
        try:
            category_select = self.query_one("#category-select", Select)
            current_value = category_select.value # Store current selection if possible

            all_categories = self.service.get_categories()
            new_options = [(cat, cat) for cat in all_categories] # Assumes get_categories is sorted
            category_select.set_options(new_options)

            # Try to restore selection, default to blank if deleted category was selected
            if current_value in all_categories:
                category_select.value = current_value
            else:
                category_select.value = Select.BLANK # Reset if selected category was deleted
            self.log.info("Category select options refreshed.")

        except NoMatches:
             self.log.error("Cannot refresh category select: Widget not found.")
        except Exception as e:
             self.log.error(f"Error refreshing category select: {e}", exc_info=True)

    def _add_new_category(self, result: Optional[Tuple[str, Optional[float]]]) -> None: # Renamed method
        """Callback to add a new category from the prompt."""
        if result:
            new_category, budget = result
            self.log(f"Processing new category: {new_category} with budget: {budget}")
            try:
                category_select = self.query_one("#category-select", Select)
                # We don't read .options, we check against self.available_categories
                # current_options: List[Tuple[str, str]] = list(category_select.options)
                category_modified_in_select = False # Track if Select widget options were changed

                # Check if category already exists in our known set
                if new_category not in self.available_categories:
                    self.available_categories.add(new_category) # Add to our local set
                    # Regenerate the full options list
                    all_options = sorted(list(self.available_categories))
                    new_options_list = [(cat, cat) for cat in all_options]
                    # Update the select widget
                    category_select.set_options(new_options_list)
                    self.notify(f"Category '{new_category}' added to dropdown.", severity="information")
                    category_modified_in_select = True # Mark that we updated the widget
                else:
                    self.notify(f"Category '{new_category}' already exists.", severity="warning")

                # Set/Update the budget via the service (this also handles adding the category if new)
                if self.service:
                    self.service.set_monthly_category_budget(new_category, budget)
                    self.log.info(f"Budget for '{new_category}' set via service to {budget}")
                else:
                     self.log.warning("SubscriptionService not passed to AddEditDialog, cannot save budget.")

                # Set the value to the new/existing category
                category_select.value = new_category
                category_select.focus() # Focus the select after adding

            except NoMatches:
                self.log.error("Could not find #category-select widget to add new category.")
            except Exception as e: # Catch potential errors during service call or widget update
                self.log.error(f"Error processing category '{new_category}': {e}", exc_info=True)
                self.notify(f"Error processing category: {e}", severity="error")

    def action_cancel(self) -> None:
        """Action bound to the Escape key."""
        self.dismiss(None)