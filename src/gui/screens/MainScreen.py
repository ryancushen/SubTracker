import sys
from datetime import date, timedelta # Added timedelta
from PyQt6.QtWidgets import ( # Grouped imports
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox, QHBoxLayout, # Added QHBoxLayout
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate # Added QDate
from PyQt6.QtGui import QIcon, QFont
from typing import TYPE_CHECKING, List

# Import the new dialog and components
from ..dialogs.AddEditDialog import AddEditSubscriptionDialog # Changed dialog import
from ..components import SubscriptionListItem # New component
from ..components.CalendarView import CalendarView # New component
from ...models.subscription import Subscription, SubscriptionStatus # Import the model class itself

if TYPE_CHECKING:
    from ...services.subscription_service import SubscriptionService # Corrected module name

class MainScreen(QWidget):
    """Main screen widget holding the primary UI elements."""
    def __init__(self, service: "SubscriptionService", parent=None):
        super().__init__(parent)
        self.service = service

        # --- Main Layout (Horizontal Split) ---
        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout() # Subscriptions and buttons
        right_layout = QVBoxLayout() # Calendar/Notifications

        # --- Left Side: Subscriptions ---
        self.title_label = QLabel("Subscriptions")
        font = self.title_label.font()
        font.setPointSize(16) # Adjusted size
        font.setBold(True)
        self.title_label.setFont(font)
        left_layout.addWidget(self.title_label)

        # Subscription List (Using QListWidget)
        self.sub_list_widget = QListWidget()
        # Set size policy to expand vertically
        self.sub_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(self.sub_list_widget)

        # Buttons (Horizontal Layout)
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add") # Shorter names
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.edit_button.setEnabled(False) # Disable until item selected
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        left_layout.addLayout(button_layout)

        # --- Right Side: Calendar/Notifications ---
        self.calendar_view = CalendarView(self)
        # Set size policy to expand
        self.calendar_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.calendar_view)

        # --- Right Side: Financial Summary ---
        financial_summary_layout = QVBoxLayout()
        financial_summary_layout.setContentsMargins(0, 10, 0, 0) # Add some top margin

        # Title for the section
        summary_title_label = QLabel("Financial Summary")
        summary_font = summary_title_label.font()
        summary_font.setBold(True)
        summary_font.setPointSize(14)
        summary_title_label.setFont(summary_font)
        financial_summary_layout.addWidget(summary_title_label)

        # Cost per Category Display
        category_title_label = QLabel("Monthly Cost per Category:")
        category_font = category_title_label.font()
        category_font.setBold(True)
        category_title_label.setFont(category_font)
        financial_summary_layout.addWidget(category_title_label)
        self.category_cost_display = QTextEdit()
        self.category_cost_display.setReadOnly(True)
        self.category_cost_display.setFixedHeight(100) # Adjust height as needed
        self.category_cost_display.setFont(QFont("Monospace")) # Use monospace for alignment
        financial_summary_layout.addWidget(self.category_cost_display)

        # Spending Forecast Display
        forecast_title_label = QLabel("Spending Forecast (Next 30 Days):")
        forecast_font = forecast_title_label.font()
        forecast_font.setBold(True)
        forecast_font.setPointSize(14)
        forecast_title_label.setFont(forecast_font)
        financial_summary_layout.addWidget(forecast_title_label)
        self.forecast_display = QTextEdit()
        self.forecast_display.setReadOnly(True)
        self.forecast_display.setFixedHeight(40) # Adjust height
        financial_summary_layout.addWidget(self.forecast_display)

        # Budget Alerts Display
        alerts_title_label = QLabel("Budget Alerts:")
        alerts_font = alerts_title_label.font()
        alerts_font.setBold(True)
        alerts_font.setPointSize(14)
        alerts_title_label.setFont(alerts_font)
        financial_summary_layout.addWidget(alerts_title_label)
        self.alerts_display = QTextEdit()
        self.alerts_display.setReadOnly(True)
        self.alerts_display.setFixedHeight(60) # Adjust height
        financial_summary_layout.addWidget(self.alerts_display)

        # Add the financial summary layout below the calendar
        right_layout.addLayout(financial_summary_layout)
        # Ensure calendar still takes priority in expansion if needed
        right_layout.setStretchFactor(self.calendar_view, 1) # Give calendar priority
        right_layout.setStretchFactor(financial_summary_layout, 0) # Financial summary takes fixed space defined by widget heights

        # Add layouts to main layout
        main_layout.addLayout(left_layout, 2) # Give left side more space (ratio 2:1)
        main_layout.addLayout(right_layout, 1)

        # --- Connections ---
        self.sub_list_widget.currentItemChanged.connect(self._handle_selection_change)
        self.sub_list_widget.itemDoubleClicked.connect(self._edit_subscription) # Double-click to edit
        self.add_button.clicked.connect(self._add_subscription)
        self.edit_button.clicked.connect(self._edit_subscription)
        self.delete_button.clicked.connect(self._delete_subscription)

        self.setLayout(main_layout)
        self.refresh_data()

    def _handle_selection_change(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Enable/disable edit/delete buttons based on selection."""
        is_selected = current is not None
        self.edit_button.setEnabled(is_selected)
        self.delete_button.setEnabled(is_selected)

    def refresh_subscriptions(self):
        """Clears and repopulates the subscription list using custom widgets."""
        self.sub_list_widget.clear()
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        try:
            subs = self.service.get_all_subscriptions()
            subs.sort(key=lambda s: s.name.lower())
            if not subs:
                # Add a placeholder item if the list is empty
                placeholder_item = QListWidgetItem("No subscriptions found.")
                placeholder_item.setFlags(placeholder_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                placeholder_item.setForeground(Qt.GlobalColor.gray)
                self.sub_list_widget.addItem(placeholder_item)
                self.sub_list_widget.setEnabled(False)
            else:
                self.sub_list_widget.setEnabled(True)
                for sub in subs:
                    # Create the custom widget
                    list_item_widget = SubscriptionListItem(sub)
                    # Create a QListWidgetItem
                    list_item = QListWidgetItem(self.sub_list_widget)
                    # Store the subscription ID (optional, widget has it too)
                    list_item.setData(Qt.ItemDataRole.UserRole, sub.id)
                    # Set the size hint for the item based on the widget
                    list_item.setSizeHint(list_item_widget.sizeHint())
                    # Add the item to the list widget
                    self.sub_list_widget.addItem(list_item)
                    # Set the custom widget for the item
                    self.sub_list_widget.setItemWidget(list_item, list_item_widget)
        except Exception as e:
            # Handle error display more gracefully
            placeholder_item = QListWidgetItem(f"Error loading: {e}")
            placeholder_item.setFlags(placeholder_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            placeholder_item.setForeground(Qt.GlobalColor.red)
            self.sub_list_widget.addItem(placeholder_item)
            self.sub_list_widget.setEnabled(False)
            print(f"Error refreshing subscription list: {e}")

    def refresh_notifications(self):
        """Fetches upcoming events and updates the CalendarView."""
        try:
            # Example: Get events for the next 30 days
            events_raw = self.service.get_upcoming_events(days_ahead=30)
            # Process events into the format CalendarView expects: {QDate: [description]}
            event_dates: dict[QDate, list[str]] = {}
            for sub, desc in events_raw:
                renewal_date = QDate(sub.next_renewal_date) if sub.next_renewal_date else None
                if renewal_date:
                    if renewal_date not in event_dates:
                        event_dates[renewal_date] = []
                    event_dates[renewal_date].append(f"{sub.name}: {desc}")

            self.calendar_view.set_event_dates(event_dates)
        except Exception as e:
            # Optionally display an error state in the calendar view
            self.calendar_view.event_label.setText(f"Error loading events: {e}")
            print(f"Error fetching upcoming events: {e}")

    def refresh_data(self):
        """Refreshes both subscriptions and notifications (calendar)."""
        self.refresh_subscriptions()
        self.refresh_notifications()
        self.refresh_financial_summary() # Added call to refresh financial data

    def _add_subscription(self):
        """Opens the dialog to add a new subscription."""
        dialog = AddEditSubscriptionDialog(service=self.service, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                try:
                    new_sub = Subscription(**data)
                    self.service.add_subscription(new_sub)
                    self.refresh_data()
                    QMessageBox.information(self, "Success", f"Subscription '{new_sub.name}' added.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add subscription: {e}")
                    print(f"Error adding subscription: {e}")

    def _edit_subscription(self):
        """Opens the dialog to edit the selected subscription."""
        current_item = self.sub_list_widget.currentItem()
        if not current_item:
            return
        sub_id = current_item.data(Qt.ItemDataRole.UserRole)
        try:
            subscription_to_edit = self.service.get_subscription(sub_id)
            if not subscription_to_edit:
                QMessageBox.warning(self, "Error", "Could not find the selected subscription to edit.")
                self.refresh_data() # Refresh list in case it was deleted elsewhere
                return

            dialog = AddEditSubscriptionDialog(service=self.service, subscription=subscription_to_edit, parent=self)
            if dialog.exec():
                data = dialog.get_data()
                if data:
                    # Create a Subscription object to pass to update method
                    updated_sub = Subscription(**data)
                    self.service.update_subscription(updated_sub)
                    self.refresh_data()
                    QMessageBox.information(self, "Success", f"Subscription '{updated_sub.name}' updated.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit subscription: {e}")
            print(f"Error editing subscription (ID: {sub_id}): {e}")

    def _delete_subscription(self):
        """Deletes the selected subscription after confirmation."""
        current_item = self.sub_list_widget.currentItem()
        if not current_item:
            return
        sub_id = current_item.data(Qt.ItemDataRole.UserRole)
        try:
            sub = self.service.get_subscription(sub_id)
            sub_name = sub.name if sub else "Unknown"

            if not sub:
                 QMessageBox.warning(self, "Error", "Could not find the selected subscription to delete.")
                 self.refresh_data()
                 return

            reply = QMessageBox.question(self, 'Confirm Delete',
                                       f"Are you sure you want to delete '{sub_name}'?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.service.delete_subscription(sub_id):
                    self.refresh_data()
                    QMessageBox.information(self, "Success", f"Subscription '{sub_name}' deleted.")
                else:
                    # This case might indicate the ID didn't exist, though we checked
                    QMessageBox.warning(self, "Error", "Failed to delete the subscription. It might have already been removed.")
                    self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete subscription: {e}")
            print(f"Error deleting subscription (ID: {sub_id}): {e}")

    def refresh_financial_summary(self):
        """Refreshes the financial summary section."""
        # --- Cost per Category ---
        try:
            costs = self.service.calculate_cost_per_category(period='monthly')
            if costs:
                # Format: Category Name    $ Amount
                # Find max category name length for alignment (only if costs exist)
                max_len = max(len(cat) for cat in costs.keys()) + 2 # Add padding

                cost_text_lines = [
                    f"{cat:<{max_len}} ${amount:.2f}"
                    for cat, amount in sorted(costs.items())
                ]
                self.category_cost_display.setText("\n".join(cost_text_lines))
            else:
                self.category_cost_display.setText("No active subscriptions found.")
        except Exception as e:
            self.category_cost_display.setText(f"Error calculating costs: {e}")
            print(f"Error calculating cost per category: {e}")

        # --- Spending Forecast ---
        try:
            today = date.today()
            forecast_end_date = today + timedelta(days=30)
            forecast_total = self.service.calculate_spending_forecast(start_date=today, end_date=forecast_end_date)
            self.forecast_display.setText(f"Total cost: ${forecast_total:.2f}")
        except Exception as e:
            self.forecast_display.setText(f"Error calculating forecast: {e}")
            print(f"Error calculating spending forecast: {e}")

        # --- Budget Alerts ---
        try:
            alerts = self.service.check_budget_alerts()
            if alerts:
                self.alerts_display.setText("\n".join(alerts))
            else:
                self.alerts_display.setText("No budget alerts.")
        except Exception as e:
            self.alerts_display.setText(f"Error checking alerts: {e}")
            print(f"Error checking budget alerts: {e}")