# Developer Guide: SubTracker

This document provides comprehensive information for developers working on the SubTracker project. It covers setup, architecture, component details, and contribution guidelines.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Architecture](#project-architecture)
4. [Key Components](#key-components)
5. [Working with Models](#working-with-models)
6. [Service Layer](#service-layer)
7. [GUI Development](#gui-development)
8. [TUI Development](#tui-development)
9. [Testing Guidelines](#testing-guidelines)
10. [Common Development Tasks](#common-development-tasks)
11. [Troubleshooting](#troubleshooting)

## Getting Started

### Project Overview

SubTracker is a subscription management application designed to help users track and manage their recurring subscriptions. The application features both a graphical user interface (GUI) using PyQt6 and a text-based user interface (TUI) using Textual.

### Prerequisites

- Python 3.10 or higher
- Git
- Pip
- Virtual environment tool (venv)

## Development Environment

### Setting Up Development Environment

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd SubTracker
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Unix/MacOS
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Running Tests**
   ```bash
   pytest
   ```

5. **Running the Application**
   ```bash
   python main.py
   ```

### Recommended Development Tools

- **Code Editor**: VSCode with Python extension
- **Linting**: Flake8/Ruff (to be added in future)
- **Formatting**: Black (to be added in future)
- **Type Checking**: MyPy (to be added in future)

## Project Architecture

SubTracker follows a layered architecture with clear separation of concerns. For a detailed view of the architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

### Directory Structure

```
project-root/
├── src/
│   ├── gui/         # GUI implementation using PyQt6
│   ├── tui/         # TUI implementation using Textual
│   ├── services/    # Business logic and data services
│   ├── models/      # Data models
│   ├── utils/       # Utility functions
│   └── data/        # Data-related modules
├── tests/           # Test files mirroring src structure
├── docs/            # Documentation
├── config/          # Configuration files
└── scripts/         # Utility scripts
```

## Key Components

### Main Entry Point

The `main.py` file serves as the application entry point. It presents users with a choice between GUI and TUI interfaces, then launches the appropriate interface.

```python
def main():
    """Present the choice menu and launch the selected interface."""
    while True:
        print("\n--- SubTracker ---")
        print("Choose an interface to launch:")
        print("  1: Textual User Interface (TUI)")
        print("  2: Graphical User Interface (GUI)")
        print("  Q: Quit")

        choice = input("Enter your choice (1, 2, or Q): ").strip().upper()

        if choice == '1':
            run_tui()
            break
        elif choice == '2':
            launch_gui()
            break
        elif choice == 'Q':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")
```

## Working with Models

### Subscription Model

The core data model is the `Subscription` class defined in `src/models/subscription.py`. It is implemented as a Python dataclass with proper validation in the `__post_init__` method.

```python
@dataclass
class Subscription:
    """Represents a single subscription entry."""
    name: str
    cost: float
    billing_cycle: BillingCycle
    start_date: date
    # ... other fields ...

    def __post_init__(self):
        """Validate data after initialization."""
        if not self.name or self.cost is None or self.cost < 0:
            raise ValueError("Name, cost, or cost is negative.")
        # ... other validation ...
```

### Working with Enums

The model uses `BillingCycle` and `SubscriptionStatus` enums for type safety. Use these enums instead of string literals:

```python
# Correct:
subscription = Subscription(
    name="Netflix",
    cost=9.99,
    billing_cycle=BillingCycle.MONTHLY,
    status=SubscriptionStatus.ACTIVE,
    start_date=date.today()
)

# Incorrect:
subscription = Subscription(
    name="Netflix",
    cost=9.99,
    billing_cycle="monthly",  # Don't use string literals
    status="active",          # Don't use string literals
    start_date=date.today()
)
```

## Service Layer

### SubscriptionService

The `SubscriptionService` class (`src/services/subscription_service.py`) serves as the central component for all business logic. It handles:

- CRUD operations for subscriptions
- Data persistence to/from JSON
- Budget tracking and calculations
- Category management
- Date calculations for renewals

Key methods include:

```python
# Get all subscriptions
subscriptions = service.get_all_subscriptions()

# Add a new subscription (returns the ID)
sub_id = service.add_subscription(subscription)

# Update an existing subscription
success = service.update_subscription(subscription)

# Delete a subscription
success = service.delete_subscription(sub_id)

# Get upcoming renewal events
events = service.get_upcoming_events(days_ahead=30)

# Get monthly/yearly costs
monthly_cost = service.get_monthly_cost()
yearly_cost = service.get_yearly_cost()
```

### JSON Persistence

The service implements custom JSON encoding/decoding to handle Python-specific types like dates and enums. If you need to add new fields to the `Subscription` model, update the `SubscriptionEncoder.default()` and `subscription_decoder()` methods.

## GUI Development

### PyQt6 Structure

The GUI is implemented using PyQt6 with a clear separation between components:

1. **Main Application (`src/gui/app.py`)**: Sets up `QApplication` and main window
2. **Main Window (`MainWindow` class)**: Top-level window containing the main screen
3. **Main Screen (`src/gui/screens/MainScreen.py`)**: Central widget with primary UI

### Adding a New Widget

To add a new widget to the GUI:

1. If it's a reusable component, add it to `src/gui/components/`
2. If it's screen-specific, add it to the appropriate screen file
3. Connect signals and slots for event handling
4. Update the UI layout to include the new widget

Example of adding a widget to MainScreen:

```python
# In src/gui/screens/MainScreen.py
def _setup_ui(self):
    # ... existing code ...

    # Add a new button
    self.refresh_button = QPushButton("Refresh")
    self.refresh_button.clicked.connect(self._refresh_data)
    self.button_layout.addWidget(self.refresh_button)

    # ... existing code ...

def _refresh_data(self):
    """Handle refresh button click."""
    self._update_subscription_list()
    self._update_financial_summary()
```

## TUI Development

### Textual Framework

The TUI is built using Textual, which provides a modern approach to terminal interfaces:

1. **TUI Application (`src/tui/app.py`)**: Sets up the `App` class and screen management
2. **Main Screen (`src/tui/screens/MainScreen.py`)**: Primary interface for the TUI
3. **Custom Widgets (`src/tui/components/`)**: Reusable TUI widgets
4. **Dialogs (`src/tui/dialogs/`)**: Popup dialogs for actions like add/edit

### Adding a New Component

To create a new TUI component:

1. Subclass the appropriate Textual base class (e.g., `Widget`, `Screen`)
2. Implement the `compose()` method to define the component structure
3. Add CSS styling in `app.tcss` if needed
4. Add event handlers for user interactions

Example of creating a custom widget:

```python
from textual.widgets import Static
from textual.reactive import reactive

class StatusWidget(Static):
    """A widget that displays subscription status information."""

    # Reactive variable that automatically updates the display
    status_count = reactive(0)

    def on_mount(self):
        """Called when widget is added to the app."""
        self.update_status()

    def update_status(self):
        """Update the status display."""
        self.update(f"Active subscriptions: {self.status_count}")

    def watch_status_count(self, old_count: int, new_count: int):
        """Called when status_count changes."""
        self.update_status()
```

### Styling TUI Components

Textual uses a CSS-like syntax for styling. Add styles to `src/tui/app.tcss`:

```css
StatusWidget {
    background: $boost;
    color: $text;
    padding: 1 2;
    border: solid $primary;
}
```

## Testing Guidelines

### Writing Tests

Tests are located in the `tests/` directory, mirroring the structure of `src/`. Follow these guidelines:

1. Test files should be named `test_*.py`
2. Test functions should be named `test_*`
3. Use fixtures for common setup (e.g., creating a service with test data)
4. Test one functionality per test function
5. Include both normal cases and edge cases

Example test:

```python
import pytest
from datetime import date, timedelta
from src.models.subscription import Subscription, BillingCycle, SubscriptionStatus

def test_calculate_next_renewal_date_monthly():
    """Test calculating next renewal for monthly subscription."""
    # Arrange
    start_date = date.today() - timedelta(days=15)
    sub = Subscription(
        name="Test Sub",
        cost=10.0,
        billing_cycle=BillingCycle.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        start_date=start_date
    )

    # Act
    from src.utils.date_utils import calculate_next_renewal_date
    next_date = calculate_next_renewal_date(sub.start_date, sub.billing_cycle)

    # Assert
    expected_date = start_date + timedelta(days=30)
    assert next_date == expected_date
```

### Running Tests

- Run all tests: `pytest`
- Run tests from a specific file: `pytest tests/utils/test_date_utils.py`
- Run a specific test: `pytest tests/utils/test_date_utils.py::test_calculate_next_renewal_date_monthly`

## Common Development Tasks

### Adding a New Subscription Field

1. Add the field to the `Subscription` dataclass in `src/models/subscription.py`
2. Update `SubscriptionEncoder.default()` in `src/services/subscription_service.py` to handle the new field
3. Update `subscription_decoder()` to decode the field from JSON
4. Update the GUI form in `src/gui/screens/AddEditDialog.py` (or similar) to include the new field
5. Update the TUI form in `src/tui/dialogs/AddEditDialog.py` to include the new field
6. Add validation logic if needed
7. Update tests to include the new field

### Adding a New Feature

1. Start by updating the appropriate service method or creating a new one
2. Write tests for the new functionality
3. Update the GUI to expose the feature to users
4. Update the TUI to expose the feature to users
5. Document the feature in appropriate documentation files

## Troubleshooting

### Common Issues

1. **PyQt6 Installation Errors**
   - Ensure you have the necessary system libraries installed
   - On Linux: `sudo apt-get install libgl1-mesa-glx`
   - Consider using a prebuilt wheel: `pip install --only-binary=:all: PyQt6`

2. **JSON Parsing Errors**
   - Check that custom types (dates, enums) are properly encoded/decoded
   - Ensure backward compatibility with older data files

3. **Date Calculation Issues**
   - Use the `dateutil` library for complex date arithmetic
   - Be careful with month-end dates and leap years

### Getting Help

If you encounter issues not covered in this guide:

1. Check the project issue tracker
2. Review the relevant documentation files
3. Search for similar issues in PyQt6 or Textual documentation
4. Create a new issue with detailed information about the problem
