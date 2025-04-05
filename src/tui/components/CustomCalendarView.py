# src/tui/components/CustomCalendarView.py
import calendar
from datetime import date, timedelta
from typing import Set, Optional # Added Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual import events # Import events module
from textual.message import Message
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import Button, Label, Static

class CustomCalendarView(Widget):
    """A custom calendar view widget."""

    DEFAULT_CSS = """
    CustomCalendarView {
        border: round $accent;
        padding: 0 1;
        height: auto; /* Adjust height based on content */
        min-width: 30; /* Ensure minimum width for 7 columns */
        /* width: 28;  Approx width based on 7 days * ~4 chars  */
    }

    #calendar-header {
        width: 100%;
        padding: 1 0;
        align: center middle;
        height: 3; /* Fixed height for header */
    }

    #calendar-header Button {
        min-width: 3; /* Ensure buttons are clickable */
        width: auto;
        height: 1;
        margin: 0 1;
        border: none;
    }

    #month-year-label {
        width: 1fr; /* Take remaining space */
        text-align: center;
        text-style: bold;
    }

    #calendar-grid {
        grid-size: 7; /* Define 7 columns implicitly */
        /* grid-rows: auto auto auto auto auto auto; Removed explicit rows */
        grid-gutter: 1;
        height: auto;
    }

    #calendar-grid Static {
        width: 100%;
        /* height: 1;  Removed fixed height */
        text-align: center;
    }

    #calendar-grid .day-label { /* Target specific day labels */
        width: 100%;
        /* height: 1; Ensure no fixed height */
        text-align: center;
        color: $text-muted;
        text-style: bold;
        /* margin-bottom: 1; Removed margin */
    }

    #calendar-grid .day-cell {
        background: $panel-darken-1;
        border: round $background; /* Subtle border */
    }

    #calendar-grid .day-cell:hover {
        background: $accent-darken-1;
    }

    #calendar-grid .day-cell.other-month {
        color: $text-muted;
        background: $panel; /* Less emphasis */
        border: blank;
    }
     #calendar-grid .day-cell.other-month:hover {
        background: $panel-lighten-1;
    }


    #calendar-grid .day-cell.today {
        border: round $warning; /* Highlight today */
        /* background: $warning-background 20%; */ /* Commented out due to undefined variable */
    }

    #calendar-grid .day-cell.highlighted {
        background: $success; /* Highlight specific dates */
        color: $text;
        text-style: bold;
        border: round $success-darken-2;
    }
     #calendar-grid .day-cell.highlighted:hover {
        background: $success-darken-1;
    }

    #calendar-grid .day-cell.empty {
        background: $panel;
        border: blank;
    }
    """

    # --- Custom Message for Date Selection ---
    class DateSelected(Message):
        """Posted when a date is selected in the calendar."""
        def __init__(self, selected_date: date) -> None:
            super().__init__()
            self.date = selected_date

    # --- Reactive Variables ---
    current_year: var[int] = var(date.today().year)
    current_month: var[int] = var(date.today().month)
    highlighted_dates: var[Set[date]] = var(set()) # type: ignore

    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None):
        # Pass arguments by keyword to super()
        super().__init__(name=name, id=id, classes=classes)
        self._day_labels = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] # Or start Sunday based on locale?
        self._calendar_grid: Optional[Grid] = None # Query later

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button("<", id="prev-month", name="prev"),
            Label(self._get_month_year_str(), id="month-year-label"),
            Button(">", id="next-month", name="next"),
            id="calendar-header"
        )
        yield Grid(id="calendar-grid")

    def on_mount(self) -> None:
        """Build the calendar when the widget is mounted."""
        self._calendar_grid = self.query_one("#calendar-grid", Grid)
        self._build_calendar()

    def _get_month_year_str(self) -> str:
        """Returns Month Year string (e.g., 'July 2024')."""
        # Use a specific date within the month to get the name
        dt = date(self.current_year, self.current_month, 1)
        return dt.strftime("%B %Y")

    def _build_calendar(self) -> None:
        """Rebuilds the calendar grid display."""
        if not self._calendar_grid:
            return

        self.log(f"Building calendar for {self.current_year}-{self.current_month:02d}")
        self.query_one("#month-year-label", Label).update(self._get_month_year_str())

        # Clear children of the existing grid
        if self._calendar_grid is not None:
            self._calendar_grid.remove_children()

        # Populate the grid directly (synchronously) now that IDs are unique
        self.log("Populating calendar grid synchronously...")

        # Add Day Labels (Mo, Tu, ...) to the existing grid using Label widget
        for day_label in self._day_labels:
             label_widget = Label(day_label, classes="day-label")
             label_widget.styles.column_span = 1
             self._calendar_grid.mount(label_widget)

        # Get calendar data
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        today = date.today()

        # Add Day Cells
        for week_idx, week in enumerate(cal):
            for day_idx, day_num in enumerate(week):
                if day_num == 0:
                    # Use unique ID including year/month
                    cell = Static("", classes="day-cell empty", id=f"empty-{self.current_year}-{self.current_month}-w{week_idx}-d{day_idx}")
                else:
                    cell_date = date(self.current_year, self.current_month, day_num)
                    # Use unique ID including year/month
                    cell = Static(str(day_num), classes="day-cell", id=f"day-{self.current_year}-{self.current_month}-{cell_date.isoformat()}")
                    cell.set_class(cell_date == today, "today")
                    cell.set_class(cell_date in self.highlighted_dates, "highlighted")

                cell.styles.column_span = 1
                self._calendar_grid.mount(cell)

    def _change_month(self, delta: int) -> None:
        """Moves to the previous/next month."""
        current_dt = date(self.current_year, self.current_month, 1)
        new_month = current_dt.month + delta
        new_year = current_dt.year
        if new_month > 12:
            new_month = 1
            new_year += 1
        elif new_month < 1:
            new_month = 12
            new_year -= 1
        self.current_year = new_year
        self.current_month = new_month

    # --- Watchers to trigger rebuild ---
    def watch_current_year(self, old_year: int, new_year: int) -> None:
        if self.is_mounted: self._build_calendar()
    def watch_current_month(self, old_month: int, new_month: int) -> None:
        if self.is_mounted: self._build_calendar()
    def watch_highlighted_dates(self, old_dates: Set[date], new_dates: Set[date]) -> None:
        # Note: This rebuild doesn't strictly need deferral unless highlight changes happen very rapidly
        if self.is_mounted: self._build_calendar()

    # --- Event Handlers --- (Refined on_click) ---
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle month navigation."""
        if event.button.id == "prev-month":
            self._change_month(-1)
        elif event.button.id == "next-month":
            self._change_month(1)
        event.stop()

    def on_click(self, event: events.Click) -> None:
        """Handle clicks within the calendar view."""
        self.log(f"Click event received at ({event.x}, {event.y}), Type: {type(event)}")
        try:
            # Get the widget directly under the mouse click coordinates
            clicked_widget = self.get_widget_at(event.x, event.y)
            self.log(f"Widget identified at click position: {clicked_widget} (Type: {type(clicked_widget)})" )

            # Check if a widget was found and if it's a Static instance
            if isinstance(clicked_widget, Static):
                # Safely get the widget's ID
                widget_id = getattr(clicked_widget, 'id', None)
                self.log(f"Clicked Static widget ID: {widget_id}")

                # Check if the ID matches our day cell pattern (updated)
                if widget_id and widget_id.startswith(f"day-{self.current_year}-{self.current_month}-"):
                    # Extract date from ID (updated)
                    prefix = f"day-{self.current_year}-{self.current_month}-"
                    date_str = widget_id[len(prefix):] # Get the part after the dynamic prefix
                    selected_date = date.fromisoformat(date_str)
                    self.log(f"Confirmed click on day cell: {selected_date}")
                    # Post the custom message
                    self.post_message(self.DateSelected(selected_date))
                    event.stop() # Stop the event from propagating further
                elif widget_id and widget_id.startswith(f"empty-{self.current_year}-{self.current_month}-"):
                     self.log("Clicked on an empty day cell placeholder.")
                     event.stop()
                else:
                    self.log(f"Clicked Static widget, but ID '{widget_id}' doesn't match day pattern.")
            elif clicked_widget is self:
                 self.log("Click occurred on the CustomCalendarView background itself.")
            elif clicked_widget and clicked_widget.id == "calendar-grid":
                 self.log("Click occurred on the calendar grid container.")
            else:
                # Log if the widget wasn't a Static instance or was None
                self.log("Click did not hit a recognizable Static day cell.")

        except Exception as e:
            # Catch potential errors during widget lookup or date parsing
            self.log.error(f"Error processing click event at ({event.x}, {event.y}): {e}", exc_info=True)

    # --- Public method to update highlights ---
    def set_highlighted_dates(self, dates: Set[date]) -> None:
        """Sets the dates to be highlighted."""
        self.highlighted_dates = dates