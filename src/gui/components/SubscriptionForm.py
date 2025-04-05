from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QComboBox, QDateEdit,
    QDoubleSpinBox, QTextEdit, QCheckBox, QPushButton, QHBoxLayout, QGridLayout,
    QLabel, QMessageBox, QInputDialog # Added QGridLayout, QLabel
)
from PyQt6.QtCore import QDate, Qt, pyqtSlot # Added pyqtSlot
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from ...models.subscription import Subscription, BillingCycle, SubscriptionStatus

# Forward reference for type hinting
if TYPE_CHECKING:
    from ...services.subscription_service import SubscriptionService # Updated import path

class SubscriptionForm(QWidget):
    """Reusable form widget for editing subscription details."""
    def __init__(self, service: "SubscriptionService", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.service = service
        self._current_subscription_id: Optional[int] = None # To track if editing

        # --- Widgets ---
        self.name_edit = QLineEdit()
        self.cost_spinbox = QDoubleSpinBox()
        self.cost_spinbox.setDecimals(2)
        self.cost_spinbox.setMaximum(99999.99)
        self.currency_edit = QLineEdit("USD")
        self.billing_cycle_combo = QComboBox()
        self.status_combo = QComboBox()
        self.start_date_edit = QDateEdit(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        # Category Row
        self.category_combo = QComboBox()
        self.add_category_button = QPushButton("+")
        self.add_category_button.setToolTip("Add new category")
        self.add_category_button.setFixedWidth(30)
        # Username/URL
        self.username_edit = QLineEdit()
        self.url_edit = QLineEdit()
        self.service_provider_edit = QLineEdit()
        self.payment_method_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        # Trial Fields
        self.is_trial_checkbox = QCheckBox("Is Trial?")
        self.trial_end_date_edit = QDateEdit(QDate.currentDate().addDays(30))
        self.trial_end_date_edit.setCalendarPopup(True)
        self.trial_end_date_edit.setEnabled(False)

        # Populate Combo Boxes
        self.billing_cycle_combo.addItems([cycle.value for cycle in BillingCycle])
        self.status_combo.addItems([status.value for status in SubscriptionStatus if status != SubscriptionStatus.TRIAL])
        self._update_category_combo()

        # --- Layout ---
        # Use QGridLayout for more control if needed, or stick with QFormLayout
        form_layout = QFormLayout(self)
        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Cost:", self.cost_spinbox)
        form_layout.addRow("Currency:", self.currency_edit)
        form_layout.addRow("Billing Cycle:", self.billing_cycle_combo)
        form_layout.addRow("Start Date:", self.start_date_edit)
        # Category layout
        category_layout = QHBoxLayout()
        category_layout.addWidget(self.category_combo, 1) # Give combo more space
        category_layout.addWidget(self.add_category_button)
        form_layout.addRow("Category:", category_layout)
        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("URL:", self.url_edit)
        form_layout.addRow("Service Provider:", self.service_provider_edit)
        form_layout.addRow("Payment Method:", self.payment_method_edit)
        form_layout.addRow("Status:", self.status_combo)
        form_layout.addRow(self.is_trial_checkbox)
        form_layout.addRow("  Trial End Date:", self.trial_end_date_edit)
        form_layout.addRow("Notes:", self.notes_edit)

        self.setLayout(form_layout)

        # --- Connections ---
        self.is_trial_checkbox.stateChanged.connect(self._toggle_trial_fields)
        self.add_category_button.clicked.connect(self._add_category)

    def set_subscription(self, subscription: Optional[Subscription]):
        """Populate the form with data from a subscription object, or clear if None."""
        if subscription:
            self._current_subscription_id = subscription.id
            self._populate_fields(subscription)
        else:
            self._current_subscription_id = None
            self._clear_fields()

    def _populate_fields(self, subscription: Subscription):
        """Internal method to fill form fields."""
        self.name_edit.setText(subscription.name)
        self.cost_spinbox.setValue(subscription.cost)
        self.currency_edit.setText(subscription.currency)
        self.billing_cycle_combo.setCurrentText(subscription.billing_cycle.value)
        self.start_date_edit.setDate(QDate(subscription.start_date))

        self._update_category_combo(select_category=subscription.category)

        self.username_edit.setText(subscription.username or "")
        self.url_edit.setText(subscription.url or "")
        self.service_provider_edit.setText(subscription.service_provider or "")
        self.payment_method_edit.setText(subscription.payment_method or "")
        self.notes_edit.setPlainText(subscription.notes or "")

        is_trial = subscription.status == SubscriptionStatus.TRIAL
        self.is_trial_checkbox.setChecked(is_trial)
        self._toggle_trial_fields(self.is_trial_checkbox.checkState().value)
        if is_trial and subscription.trial_end_date:
             self.trial_end_date_edit.setDate(QDate(subscription.trial_end_date))
        else:
             # Ensure the status exists before setting it
            if subscription.status.value in [self.status_combo.itemText(i) for i in range(self.status_combo.count())]:
                 self.status_combo.setCurrentText(subscription.status.value)
            else: # Default to active if current status is invalid (e.g. was TRIAL)
                self.status_combo.setCurrentText(SubscriptionStatus.ACTIVE.value)

    def _clear_fields(self):
        """Reset all fields to default/empty state."""
        self.name_edit.clear()
        self.cost_spinbox.setValue(0.0)
        self.currency_edit.setText("USD")
        self.billing_cycle_combo.setCurrentIndex(0)
        self.start_date_edit.setDate(QDate.currentDate())
        self._update_category_combo()
        self.username_edit.clear()
        self.url_edit.clear()
        self.service_provider_edit.clear()
        self.payment_method_edit.clear()
        self.status_combo.setCurrentIndex(0) # Default to first non-trial status
        self.notes_edit.clear()
        self.is_trial_checkbox.setChecked(False)
        self.trial_end_date_edit.setDate(QDate.currentDate().addDays(30))
        self._toggle_trial_fields(Qt.CheckState.Unchecked.value)

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Validate and return the current form data as a dictionary."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Subscription name cannot be empty.")
            return None

        is_trial = self.is_trial_checkbox.isChecked()
        trial_end_date_val = self.trial_end_date_edit.date().toPython() if is_trial else None
        status_val = SubscriptionStatus.TRIAL if is_trial else SubscriptionStatus(self.status_combo.currentText())
        selected_category = self.category_combo.currentText() or None

        data = {
            "name": name,
            "cost": self.cost_spinbox.value(),
            "currency": self.currency_edit.text().strip() or "USD",
            "billing_cycle": BillingCycle(self.billing_cycle_combo.currentText()),
            "start_date": self.start_date_edit.date().toPython(),
            "status": status_val,
            "category": selected_category,
            "username": self.username_edit.text().strip() or None,
            "url": self.url_edit.text().strip() or None,
            "service_provider": self.service_provider_edit.text().strip() or None,
            "payment_method": self.payment_method_edit.text().strip() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "trial_end_date": trial_end_date_val,
        }
        # Include ID if we are editing an existing subscription
        if self._current_subscription_id is not None:
            data['id'] = self._current_subscription_id
        return data

    # --- Helper Methods (similar to dialog) ---
    def _update_category_combo(self, select_category: Optional[str] = None):
        """Updates the category combo box items from the service."""
        try:
            current_categories = self.service.get_categories()
            self.category_combo.clear()
            self.category_combo.addItems(current_categories)
            if select_category and select_category in current_categories:
                self.category_combo.setCurrentText(select_category)
            elif current_categories:
                 self.category_combo.setCurrentIndex(0)
        except Exception as e:
            # Handle cases where service might not be ready or fails
            print(f"Error updating category combo: {e}")
            self.category_combo.clear()
            self.category_combo.addItem("- Error loading categories -")
            self.category_combo.setEnabled(False)

    @pyqtSlot()
    def _add_category(self):
        """Opens an input dialog to add a new category via the service."""
        text, ok = QInputDialog.getText(self, "Add Category", "Enter new category name:")
        if ok and text:
            new_category = text.strip()
            if new_category:
                try:
                    added = self.service.add_category(new_category)
                    if added:
                        self._update_category_combo(select_category=new_category)
                    else:
                        # Category might already exist, just select it
                        if new_category in self.service.get_categories():
                            self.category_combo.setCurrentText(new_category)
                        else:
                            QMessageBox.warning(self, "Error", f"Could not add category '{new_category}'.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add category: {e}")
            else:
                # If category already exists after stripping (e.g., user enters spaces)
                if new_category in self.service.get_categories():
                    self.category_combo.setCurrentText(new_category)

    @pyqtSlot(int)
    def _toggle_trial_fields(self, state: int):
        """Enable/disable trial end date based on checkbox state."""
        is_trial = state == Qt.CheckState.Checked.value
        self.trial_end_date_edit.setEnabled(is_trial)
        self.status_combo.setEnabled(not is_trial)
        if is_trial:
            # Save current status maybe?
            pass # Status will be set to TRIAL when getting data
        else:
            # Restore previous status or default to ACTIVE if needed
             if self.status_combo.count() > 0 and self.status_combo.findText(SubscriptionStatus.ACTIVE.value) != -1:
                self.status_combo.setCurrentText(SubscriptionStatus.ACTIVE.value)
             elif self.status_combo.count() > 0:
                 self.status_combo.setCurrentIndex(0)