from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ...models.subscription import Subscription

class SubscriptionListItem(QWidget):
    """Custom widget to display a subscription's summary in a list."""
    def __init__(self, subscription: Subscription, parent: QWidget | None = None):
        """Initializes the SubscriptionListItem widget.

        Args:
            subscription: The Subscription object to display.
            parent: The parent widget, if any.
        """
        super().__init__(parent)
        self.subscription = subscription

        # --- Layouts ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        info_layout = QVBoxLayout()
        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Widgets ---
        self.name_label = QLabel(self.subscription.name)
        font = self.name_label.font()
        font.setBold(True)
        self.name_label.setFont(font)

        # Combine cost, currency, and billing cycle
        cost_text = f"{self.subscription.cost:.2f} {self.subscription.currency}"
        cycle_text = self.subscription.billing_cycle.value
        self.details_label = QLabel(f"{cost_text} / {cycle_text}")

        # Status Indicator (Example: just text for now)
        self.status_label = QLabel(self.subscription.status.value.upper())
        status_font = self.status_label.font()
        status_font.setPointSize(status_font.pointSize() - 2)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # --- Assemble Layouts ---
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.details_label)
        info_layout.addStretch()

        status_layout.addWidget(self.status_label)

        main_layout.addLayout(info_layout, 1) # Give info layout more space
        main_layout.addLayout(status_layout)

        # Optional: Add a frame for visual separation
        # frame = QFrame(self)
        # frame.setFrameShape(QFrame.Shape.StyledPanel)
        # frame.setLayout(main_layout)
        # outer_layout = QVBoxLayout(self)
        # outer_layout.addWidget(frame)
        # outer_layout.setContentsMargins(0,0,0,0)

        self.setLayout(main_layout)

    def get_subscription_id(self) -> int:
        """Returns the ID of the subscription this item represents."""
        # Assuming subscription objects always have an id after being added/fetched
        return self.subscription.id