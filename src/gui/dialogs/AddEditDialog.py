from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from typing import Optional, Dict, Any, TYPE_CHECKING

from ...models.subscription import Subscription
from ..components.SubscriptionForm import SubscriptionForm # Import the form

if TYPE_CHECKING:
    from ...services.subscription_service import SubscriptionService # Updated import path

class AddEditSubscriptionDialog(QDialog):
    """Dialog for adding or editing a subscription using SubscriptionForm."""
    def __init__(self, service: "SubscriptionService", subscription: Optional[Subscription] = None, parent=None):
        super().__init__(parent)
        self.subscription = subscription
        self.service = service

        self.setWindowTitle("Add Subscription" if subscription is None else "Edit Subscription")

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)

        # --- Subscription Form ---
        self.form = SubscriptionForm(service=self.service, parent=self)
        if self.subscription:
            self.form.set_subscription(self.subscription) # Populate form if editing
        main_layout.addWidget(self.form)

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept) # Connect to built-in accept
        self.button_box.rejected.connect(self.reject) # Connect to built-in reject
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Gets the validated data from the embedded form."""
        # The form's get_data method already handles validation
        return self.form.get_data()

    # Override accept to ensure data is valid before closing
    def accept(self):
        """Override accept to validate data before closing."""
        if self.get_data() is not None:
            super().accept()
        # If get_data() returns None, the form already showed an error message
        # so we don't close the dialog.