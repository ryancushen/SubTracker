from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
import logging
import os

# Import the main screen
from .screens.MainScreen import MainScreen
from ..services.subscription_service import SubscriptionService

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
        # Setup logging
        self._setup_logging()
        # Initialize the service - it will load/create the JSON file
        self.service = SubscriptionService()
        logging.info("SubTrackerApp initialized with SubscriptionService")

    def _setup_logging(self):
        """Configure logging for the application."""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/subtacker.log"),
                logging.StreamHandler()
            ]
        )
        logging.info("Logging configured for SubTrackerApp")

    def on_mount(self) -> None:
        """Called when the app starts."""
        logging.info("SubTrackerApp mounted, pushing MainScreen")
        # Start on the main screen, passing the service
        self.push_screen(MainScreen(service=self.service)) # Pass service instance

    # Removed compose method as screens handle their composition
    # Removed Container and Placeholder imports

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark