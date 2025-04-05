# src/tui/dialogs/EditCategoryScreen.py
from typing import Optional, Union

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Label, Static

# Return type: New budget (float), None (cancel), or "__DELETE__" (delete signal)
class EditCategoryScreen(ModalScreen[Optional[Union[float, str]]]):
    """A modal screen to edit a category's budget or delete the category."""

    CSS = """
    EditCategoryScreen {
        align: center middle;
    }

    #edit-cat-container {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    #edit-cat-container Label {
        margin-bottom: 1;
    }
    #edit-cat-container Static {
        margin-bottom: 1;
        border: round $background-lighten-2;
        padding: 0 1;
        color: $text-muted;
    }

    #edit-cat-budget-input {
        margin-bottom: 1;
    }

    #edit-cat-buttons {
        align-horizontal: right;
        height: auto;
        padding-top: 1;
    }

    #edit-cat-buttons Button {
        margin-left: 2;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+d", "delete", "Delete Category"), # Add binding for delete
    ]

    def __init__(self, category_name: str, current_budget: Optional[float]) -> None:
        super().__init__()
        self.category_name = category_name
        self.current_budget = current_budget

    def compose(self) -> ComposeResult:
        with Vertical(id="edit-cat-container"):
            yield Label("Editing Category:")
            yield Static(self.category_name) # Display category name (read-only)

            yield Label("Optional monthly budget:")
            yield Input(
                value=f"{self.current_budget:.2f}" if self.current_budget is not None else "",
                placeholder="e.g., 50.00 (leave blank for no budget)",
                id="edit-cat-budget-input",
                type="number"
            )
            with Horizontal(id="edit-cat-buttons"):
                yield Button("Save Changes", variant="primary", id="save-button")
                yield Button("Delete Category", variant="error", id="delete-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def on_mount(self) -> None:
        """Focus the budget input field when the screen is mounted."""
        self.query_one("#edit-cat-budget-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-button":
            self.action_submit()
        elif event.button.id == "delete-button":
            self.action_delete()
        elif event.button.id == "cancel-button":
            self.action_cancel()

    def action_submit(self) -> None:
        """Validate budget and dismiss the screen, returning the new budget value or None."""
        budget_str = self.query_one("#edit-cat-budget-input", Input).value.strip()
        new_budget: Optional[float] = None

        if budget_str:
            try:
                new_budget = float(budget_str)
                if new_budget < 0:
                    raise ValueError("Budget cannot be negative.")
            except ValueError:
                self.notify("Invalid budget amount. Must be a non-negative number.", severity="error", title="Validation Error")
                self.query_one("#edit-cat-budget-input", Input).focus()
                return # Prevent dismissal

        # Dismiss with the new budget value (can be None if cleared)
        self.dismiss(new_budget)

    def action_delete(self) -> None:
        """Dismiss the screen, returning the delete signal."""
        # Optionally add a ConfirmDialog here before dismissing
        # For now, dismiss directly with the signal
        self.dismiss("__DELETE__")

    def action_cancel(self) -> None:
        """Dismiss the screen, returning None."""
        self.dismiss(None)