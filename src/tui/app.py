from textual.app import App, ComposeResult
from textual.widgets import Header, Footer # Removed Placeholder
# from textual.containers import Container # Removed Container

# Import the main screen
from .screens.MainScreen import MainScreen
from ..services.subscription_service import SubscriptionService # Assuming service setup

class SubTrackerApp(App):
    """A Textual app to manage subscriptions."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]
    CSS_PATH = "app.tcss"
    TITLE = "SubTracker TUI"

    # --- Screens ---
    # Define screens the app can push/pop
    SCREENS = {
        "main": MainScreen # Register the main screen
    }

    def __init__(self):
        super().__init__()
        # Initialize the service - it will load/create the JSON file
        self.service = SubscriptionService()

    def on_mount(self) -> None:
        """Called when the app starts."""
        # Start on the main screen, passing the service
        self.push_screen(MainScreen(service=self.service)) # Pass service instance

    # Removed compose method as screens handle their composition
    # Removed Container and Placeholder imports

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark