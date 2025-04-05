# src/tui/dialogs/CategoryPromptScreen.py
from typing import Optional, Tuple

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Label, Static

class CategoryPromptScreen(ModalScreen[Optional[Tuple[str, Optional[float]]]]):
    """A modal screen to prompt the user for a new category name and optional budget."""

    CSS = """
    CategoryPromptScreen {
        align: center middle;
    }

    #prompt-container {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    #prompt-container Label {
        margin-bottom: 1;
    }

    #prompt-category-input {
        margin-bottom: 1;
    }

    #prompt-budget-input {
        margin-bottom: 1;
    }

    #prompt-buttons {
        align-horizontal: right;
        height: auto;
        padding-top: 1;
    }

    #prompt-buttons Button {
        margin-left: 2;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, initial_category: str = "") -> None:
        super().__init__()
        self.initial_category = initial_category

    def compose(self) -> ComposeResult:
        with Vertical(id="prompt-container"):
            yield Label("Enter new category name:")
            yield Input(
                value=self.initial_category,
                placeholder="New Category",
                id="prompt-category-input"
            )
            yield Label("Optional monthly budget:")
            yield Input(
                placeholder="e.g., 50.00 (leave blank for no budget)",
                id="prompt-budget-input",
                type="number"
            )
            with Horizontal(id="prompt-buttons"):
                yield Button("OK", variant="primary", id="ok-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def on_mount(self) -> None:
        """Focus the category input field when the screen is mounted."""
        self.query_one("#prompt-category-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok-button":
            self.action_submit()
        elif event.button.id == "cancel-button":
            self.action_cancel()

    def action_submit(self) -> None:
        """Validate inputs and dismiss the screen, returning (category, budget)."""
        category_name = self.query_one("#prompt-category-input", Input).value.strip()
        budget_str = self.query_one("#prompt-budget-input", Input).value.strip()
        budget_value: Optional[float] = None

        if not category_name:
            self.notify("Category name cannot be empty.", severity="error", title="Validation Error")
            self.query_one("#prompt-category-input", Input).focus()
            return

        if budget_str:
            try:
                budget_value = float(budget_str)
                if budget_value < 0:
                    raise ValueError("Budget cannot be negative.")
            except ValueError:
                self.notify("Invalid budget amount. Must be a non-negative number.", severity="error", title="Validation Error")
                self.query_one("#prompt-budget-input", Input).focus()
                return

        self.dismiss((category_name, budget_value))

    def action_cancel(self) -> None:
        """Dismiss the screen, returning None."""
        self.dismiss(None)