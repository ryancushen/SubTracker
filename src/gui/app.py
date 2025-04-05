import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon, QAction
from ..services.subscription_service import SubscriptionService
from ..models.subscription import SubscriptionStatus
from .screens.MainScreen import MainScreen # Import the widget

class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self, service: SubscriptionService):
        """Initializes the MainWindow.

        Args:
            service: The subscription service instance.
        """
        super().__init__()
        self.service = service

        self.setWindowTitle("Subscription Tracker")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        # Create and set the central widget
        self.main_screen_widget = MainScreen(self.service)
        self.setCentralWidget(self.main_screen_widget)

        # Add Menu bar and Status bar
        self._create_menu_bar()
        self._create_status_bar()

    def _create_menu_bar(self):
        """Creates the main menu bar for the application."""
        menu_bar = self.menuBar()
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        # Add other menus (e.g., Edit, Help) here if needed

    def _create_status_bar(self):
        """Creates the status bar at the bottom of the window."""
        self.statusBar().showMessage("Ready")

    # Removed _update_subscription_list and _update_notifications
    # The MainScreen widget handles its own data refreshing.

def run_gui(service: SubscriptionService):
    """Initializes and runs the PyQt6 GUI application."""
    app = QApplication(sys.argv)

    # You can set application-wide styles here if desired
    # app.setStyleSheet(""" QWidget { font-size: 14px; } """)

    main_window = MainWindow(service)
    main_window.show()

    sys.exit(app.exec())