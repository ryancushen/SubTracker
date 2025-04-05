# src/tui/components/FinancialSummary.py
from typing import TYPE_CHECKING, List, Dict, Tuple
from datetime import date, timedelta

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Vertical

if TYPE_CHECKING:
    from ...services.subscription_service import SubscriptionService

class FinancialSummary(Widget):
    """A widget to display financial summary information."""

    DEFAULT_CSS = """
    FinancialSummary {
        height: auto; /* Size based on content */
        border: round $accent;
        padding: 1;
        margin-top: 1; /* Space above this section */
    }
    FinancialSummary > Static {
        margin-bottom: 1; /* Space below each static line/section */
    }
    FinancialSummary .summary-title {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
     FinancialSummary .section-title {
        text-style: bold underline;
     }
     FinancialSummary .content {
         /* Style for the content text if needed */
         margin-left: 2; /* Indent content */
         height: auto; /* Allow content to wrap */
     }
     FinancialSummary .error {
         color: $error;
     }
     FinancialSummary .placeholder {
         color: $text-muted;
         margin-left: 2;
     }
    """

    def __init__(self, service: "SubscriptionService", name: str | None = None, id: str | None = None, classes: str | None = None):
        # Pass arguments by keyword to super()
        super().__init__(name=name, id=id, classes=classes)
        self.service = service
        # Use Static widgets to display the data. Query them later.
        self._category_cost_display = Static(id="category-cost", classes="content", markup=False)
        self._forecast_display = Static(id="forecast", classes="content", markup=False)
        self._alerts_display = Static(id="alerts", classes="content", markup=False)


    def compose(self) -> ComposeResult:
        yield Static("Financial Summary", classes="summary-title")
        with Vertical():
            yield Static("Monthly Cost per Category:", classes="section-title")
            yield self._category_cost_display
            yield Static("Spending Forecast (Next 30 Days):", classes="section-title")
            yield self._forecast_display
            yield Static("Budget Alerts:", classes="section-title")
            yield self._alerts_display

    def on_mount(self) -> None:
        """Initial refresh when the widget is added."""
        self.refresh_summary()

    def refresh_summary(self) -> None:
        """Fetches data from the service and updates the display."""
        self.log("Refreshing financial summary...")

        # --- Cost per Category ---
        try:
            costs = self.service.calculate_cost_per_category(period='monthly')
            if costs:
                 # Format similar to GUI: Category Name    $ Amount
                 # Find max category name length for alignment
                max_len = max((len(cat) for cat in costs.keys()), default=0) + 2 # Add padding
                cost_text_lines = [
                    f"{cat:<{max_len}} ${amount:.2f}"
                    for cat, amount in sorted(costs.items())
                ]
                self._category_cost_display.update("\n".join(cost_text_lines))
                self._category_cost_display.remove_class("placeholder", "error")
            else:
                self._category_cost_display.update("No active subscriptions found.")
                self._category_cost_display.add_class("placeholder")
                self._category_cost_display.remove_class("error")
        except Exception as e:
            self._category_cost_display.update(f"Error: {e}")
            self._category_cost_display.add_class("error")
            self.log.error(f"Error calculating cost per category: {e}")

        # --- Spending Forecast ---
        try:
            today = date.today()
            forecast_end_date = today + timedelta(days=30)
            forecast_total = self.service.calculate_spending_forecast(start_date=today, end_date=forecast_end_date)
            self._forecast_display.update(f"Total cost: ${forecast_total:.2f}")
            self._forecast_display.remove_class("placeholder", "error")
        except Exception as e:
            self._forecast_display.update(f"Error: {e}")
            self._forecast_display.add_class("error")
            self.log.error(f"Error calculating spending forecast: {e}")

        # --- Budget Alerts ---
        try:
            alerts = self.service.check_budget_alerts()
            if alerts:
                self._alerts_display.update("\n".join(alerts))
                self._alerts_display.remove_class("placeholder", "error")
            else:
                self._alerts_display.update("No budget alerts.")
                self._alerts_display.add_class("placeholder")
                self._alerts_display.remove_class("error")
        except Exception as e:
            self._alerts_display.update(f"Error: {e}")
            self._alerts_display.add_class("error")
            self.log.error(f"Error checking budget alerts: {e}")