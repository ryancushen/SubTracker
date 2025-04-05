# src/tui/dialogs/ConfirmDialog.py
from typing import Optional, Type

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

class ConfirmDialog(ModalScreen[bool]):
    """A simple Yes/No confirmation dialog."""

    CSS = """
    ConfirmDialog {
        align: center middle;
    }

    #confirm-dialog-container {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto auto; /* Row for message, row for buttons */
        padding: 0 1;
        width: 50; /* Adjust width as needed */
        height: auto;
        border: thick $accent;
        background: $surface;
    }

    #confirm-message {
        column-span: 2; /* Message spans both columns */
        height: auto;
        width: 100%;
        margin: 1;
        text-align: center;
    }

    #confirm-dialog-container Button {
        width: 100%; /* Make buttons fill their grid cell */
    }
    """

    def __init__(self, message: str, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name, id, classes)
        self.message = message

    def compose(self) -> ComposeResult:
        yield Grid(
            Static(self.message, id="confirm-message"),
            Button("Yes", variant="error", id="confirm-yes"),
            Button("No", variant="primary", id="confirm-no"),
            id="confirm-dialog-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-yes":
            self.dismiss(True)
        elif event.button.id == "confirm-no":
            self.dismiss(False)

    def on_mount(self) -> None:
        # Focus the 'No' button by default for safety
        self.query_one("#confirm-no", Button).focus()