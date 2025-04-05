import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCalendarWidget, QLabel
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QTextCharFormat, QColor, QBrush
from typing import List, Dict

class CalendarView(QWidget):
    """Widget to display a calendar, potentially highlighting event dates."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)

        # Placeholder for event display
        self.event_label = QLabel("Select a date to view details.")
        self.event_label.setWordWrap(True)

        self.layout.addWidget(self.calendar)
        self.layout.addWidget(self.event_label)

        # Connect signal
        self.calendar.selectionChanged.connect(self.display_date_info)

        # Placeholder for event data (e.g., {QDate: ["Event 1", "Event 2"]})
        self.event_dates: Dict[QDate, List[str]] = {}
        # Define a format for highlighting event dates
        self.highlight_format = QTextCharFormat()
        # Example: Light blue background, bold text
        self.highlight_format.setBackground(QBrush(QColor("lightblue")))
        self.highlight_format.setFontWeight(700) # Bold

        self.setLayout(self.layout)

    def set_event_dates(self, events: Dict[QDate, List[str]]):
        """Sets the dates with events and applies highlighting."""
        # Reset previous formatting first to handle removed events
        default_format = QTextCharFormat() # Default/empty format
        valid_dates = self.calendar.findChildren(QDate) # Get all dates currently rendered if needed
        start_date = self.calendar.minimumDate()
        end_date = self.calendar.maximumDate()
        current_date = start_date
        while current_date <= end_date:
            # Check if the date is currently visible/rendered before resetting, if needed
            # For simplicity, resetting all possible dates in range
            self.calendar.setDateTextFormat(current_date, default_format)
            current_date = current_date.addDays(1)


        self.event_dates = events
        # Apply the highlight format to each event date
        for date in self.event_dates.keys():
            self.calendar.setDateTextFormat(date, self.highlight_format)

        # No longer need explicit updateCells() here, setDateTextFormat handles updates.
        # This requires subclassing QCalendarWidget or using QTextCharFormat
        # self.calendar.updateCells() # Trigger potential repaint <-- Removed

    def display_date_info(self):
        """Displays information for the selected date."""
        selected_date = self.calendar.selectedDate()
        if selected_date in self.event_dates:
            events_str = "\n".join(self.event_dates[selected_date])
            self.event_label.setText(f"Events on {selected_date.toString()}:\n{events_str}")
        else:
            self.event_label.setText(f"No events scheduled for {selected_date.toString()}.")

