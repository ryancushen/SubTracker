import sys
from PyQt6.QtWidgets import (
    QDialog, QWidget, QFormLayout, QLineEdit, QComboBox, QDateEdit,
    QDoubleSpinBox, QTextEdit, QDialogButtonBox, QVBoxLayout, QMessageBox, QCheckBox,
    QHBoxLayout, QPushButton, QInputDialog
)
from PyQt6.QtCore import QDate, pyqtSlot, Qt
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from ...models.subscription import Subscription, BillingCycle, SubscriptionStatus
if TYPE_CHECKING:
    from ...services.subscription_service import SubscriptionService

class SubscriptionDialog(QDialog):
    """Dialog for adding or editing a subscription."""
    def __init__(self, service: "SubscriptionService", subscription: Optional[Subscription] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.service = service # Store service instance
        self.subscription = subscription
        # No longer need to manage categories list locally
        # self.available_categories = ...

        self.setWindowTitle("Add Subscription" if subscription is None else "Edit Subscription")

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
        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Cost:", self.cost_spinbox)
        form_layout.addRow("Currency:", self.currency_edit)
        form_layout.addRow("Billing Cycle:", self.billing_cycle_combo)
        form_layout.addRow("Start Date:", self.start_date_edit)
        # Category layout
        category_layout = QHBoxLayout()
        category_layout.addWidget(self.category_combo)
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

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # --- Connections ---
        self.is_trial_checkbox.stateChanged.connect(self._toggle_trial_fields)
        self.add_category_button.clicked.connect(self._add_category)

        # --- Populate Fields if Editing ---
        if self.subscription:
            self._populate_fields()

    def _update_category_combo(self, select_category: Optional[str] = None):
        """Updates the category combo box items from the service."""
        current_categories = self.service.get_categories() # Get from service
        self.category_combo.clear()
        self.category_combo.addItems(current_categories)
        if select_category and select_category in current_categories:
            self.category_combo.setCurrentText(select_category)
        elif current_categories:
             self.category_combo.setCurrentIndex(0)

    @pyqtSlot()
    def _add_category(self):
        """Opens an input dialog to add a new category via the service."""
        text, ok = QInputDialog.getText(self, "Add Category", "Enter new category name:")
        if ok and text:
            new_category = text.strip()
            if new_category:
                added = self.service.add_category(new_category) # Use service method
                if added:
                    self._update_category_combo(select_category=new_category)
                else:
                    # Category might already exist, just select it
                    if new_category in self.service.get_categories():
                        self.category_combo.setCurrentText(new_category)
                    else:
                        # Should not happen if add_category logic is correct, but handle defensively
                        QMessageBox.warning(self, "Error", f"Could not add category '{new_category}'.")
            else:
                 self.category_combo.setCurrentText(new_category) # Select if exists

    @pyqtSlot(int)
    def _toggle_trial_fields(self, state: int):
        """Enable/disable trial end date based on checkbox state."""
        is_trial = state == Qt.CheckState.Checked.value
        self.trial_end_date_edit.setEnabled(is_trial)
        # If it becomes a trial, force status to TRIAL
        # If it stops being a trial, set status back to ACTIVE (or previous)
        # For now, simplify: disable status combo if trial
        self.status_combo.setEnabled(not is_trial)
        if is_trial:
            self.status_combo.setCurrentText(SubscriptionStatus.ACTIVE.value) # Set a default non-trial status when disabling
            # In a more robust implementation, store the pre-trial status

    def _populate_fields(self):
        """Populate the form fields with data from an existing subscription."""
        if not self.subscription:
            return

        self.name_edit.setText(self.subscription.name)
        self.cost_spinbox.setValue(self.subscription.cost)
        self.currency_edit.setText(self.subscription.currency)
        self.billing_cycle_combo.setCurrentText(self.subscription.billing_cycle.value)
        self.start_date_edit.setDate(QDate(self.subscription.start_date))
        # Ensure the category exists in the combo before setting
        category_to_select = self.subscription.category or ""
        if category_to_select in self.service.get_categories():
             self.category_combo.setCurrentText(category_to_select)
        elif self.service.get_categories(): # Select first if category missing
            self.category_combo.setCurrentIndex(0)

        self.username_edit.setText(self.subscription.username or "")
        self.url_edit.setText(self.subscription.url or "")
        self.service_provider_edit.setText(self.subscription.service_provider or "")
        self.payment_method_edit.setText(self.subscription.payment_method or "")
        self.notes_edit.setPlainText(self.subscription.notes or "")

        is_trial = self.subscription.status == SubscriptionStatus.TRIAL
        self.is_trial_checkbox.setChecked(is_trial)
        self._toggle_trial_fields(self.is_trial_checkbox.checkState().value)
        if is_trial and self.subscription.trial_end_date:
             self.trial_end_date_edit.setDate(QDate(self.subscription.trial_end_date))
        else:
            self.status_combo.setCurrentText(self.subscription.status.value)

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Validate and return the entered data as a dictionary."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Subscription name cannot be empty.")
            return None

        is_trial = self.is_trial_checkbox.isChecked()
        trial_end_date_val = self.trial_end_date_edit.date().toPython() if is_trial else None

        # Determine status based on trial checkbox
        status_val = SubscriptionStatus.TRIAL if is_trial else SubscriptionStatus(self.status_combo.currentText())

        # Get selected category (can be empty if nothing selected/available)
        selected_category = self.category_combo.currentText() or None

        data = {
            "name": name,
            "cost": self.cost_spinbox.value(),
            "currency": self.currency_edit.text().strip() or "USD",
            "billing_cycle": BillingCycle(self.billing_cycle_combo.currentText()),
            "start_date": self.start_date_edit.date().toPython(),
            "status": status_val,
            "category": selected_category, # Use combo box value
            "username": self.username_edit.text().strip() or None, # Get username
            "url": self.url_edit.text().strip() or None, # Get url
            "service_provider": self.service_provider_edit.text().strip() or None,
            "payment_method": self.payment_method_edit.text().strip() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "trial_end_date": trial_end_date_val,
        }
        return data