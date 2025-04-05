# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (once initial development leads to a versioned release).

## [Unreleased]

### Added

-   Initialized Git repository.
-   Created initial project directory structure (`src`, `tests`, `docs`, `config`, `scripts/validation_logs`).
-   Set up Python virtual environment (`venv`).
-   Created `requirements.txt`.
-   Created initial context documents:
    -   `docs/ARCHITECTURE.md`
    -   `docs/CONVENTIONS.md`
    -   `docs/TOOLS.md`
    -   `docs/CHANGELOG.md`
    -   `docs/REFERENCES.md`
-   Added `.gitignore` file.
-   Implemented `Subscription` model in `src/models/subscription.py`.
-   Chosen JSON for data storage and documented in `ARCHITECTURE.md` and `TOOLS.md`.
-   Implemented `SubscriptionService` with CRUD operations in `src/services/subscription_service.py`.
-   Implemented `calculate_next_renewal` function using `python-dateutil` in `src/utils/date_utils.py`.
-   Added `python-dateutil` to `requirements.txt`.
-   Set up `pytest` framework: added to `requirements.txt`, created `tests/` directory structure and placeholder files.
-   Added `trial_end_date`, `service_provider`, `payment_method` fields to `Subscription` model (`src/models/subscription.py`).
-   Added `TRIAL` status to `SubscriptionStatus` enum.
-   Added logic to `Subscription.__post_init__` to manage `TRIAL` status based on `trial_end_date`.
-   Updated `SubscriptionService.update_subscription` to handle new fields and trial status logic.
-   Added `get_upcoming_events` method to `SubscriptionService` for notifications.
-   Updated `subscription_decoder` to handle `trial_end_date`.
-   Updated `SubscriptionService.add_subscription` and `_recalculate_all_renewal_dates` to handle `TRIAL` status correctly regarding `next_renewal_date`.
-   Added tests for trial features and upcoming events in `tests/services/test_subscription_service.py`.
-   Fixed various issues in date calculation and test assertions.
-   Added `customtkinter` dependency to `requirements.txt`.
-   Updated `docs/TOOLS.md` with `CustomTkinter` as the chosen GUI library.
-   Created initial GUI structure using CustomTkinter (`src/gui/app.py`, `src/gui/screens/main_screen.py`).
-   Created `main.py` entry point script.
-   Updated `docs/ARCHITECTURE.md` with GUI details.
-   Replaced `customtkinter` with `pysimplegui` in `requirements.txt`.
-   Updated `docs/TOOLS.md` and `docs/ARCHITECTURE.md` to reflect the switch to PySimpleGUI.
-   Refactored initial GUI code for PySimpleGUI.
-   Replaced `pysimplegui` with `PySide6` in `requirements.txt`.
-   Updated `docs/TOOLS.md` and `docs/ARCHITECTURE.md` to reflect the switch to PySide6.
-   Replaced `PySide6` with `PyQt6` in `requirements.txt`.
-   Added category and budget management functionality to `SubscriptionService`.
-   Implemented TUI interface using Textual framework.
-   Created TUI components: `CustomCalendarView`, `FinancialSummary`.
-   Created TUI dialogs: `AddEditDialog`, `ConfirmDialog`.
-   Implemented TUI main screen with subscription list and financial summary.
-   Added keyboard bindings to TUI for common actions.
-   Implemented TUI calendar view for upcoming renewals.
-   Updated main.py to support both GUI and TUI interfaces with user selection.
-   Added spending forecast and cost calculations to `SubscriptionService`.
-   Enhanced documentation with detailed comments and docstrings.
-   Comprehensive update of all documentation files to reflect current state.
-   **YYYY-MM-DD:** (LLM) Initialized project structure, Kivy GUI skeleton, and basic subscription display using RecycleView.
-   **YYYY-MM-DD:** (LLM) Implemented Add, Edit, and Delete functionality with Popups for user interaction.
-   **YYYY-MM-DD:** (LLM) Refactored Kivy GUI to use `TabbedPanel` for separating views (Subscriptions, Calendar, Financials, Notifications). Added placeholder content and logic for Financials summary and upcoming renewal Notifications.
-   **YYYY-MM-DD:** (LLM) Enhanced the Notifications tab to show upcoming renewals grouped by date for the next 30 days, replacing the need for a complex calendar widget installation.
-   **YYYY-MM-DD:** (LLM) Replaced Kivy GUI with Streamlit. Added `streamlit` dependency, updated documentation (`TOOLS.md`, `ARCHITECTURE.md`), and prepared for Streamlit app implementation in `src/gui/streamlit_app.py`.
-   Fix for BillingCycle enum by adding ANNUALLY as an alias to YEARLY for backward compatibility
-   Updated User Guide with detailed information about billing cycles and app workflow
-   Added comprehensive trial subscription support with trial end date tracking
-   Added subscription status management
-   Added helper methods for checking trials ending soon

### Changed

-   Refactored `calculate_next_renewal_date` in `src/utils/date_utils.py` to correctly handle dates equal to today.
-   Updated `SubscriptionService._load_subscriptions` to reliably call `_recalculate_all_renewal_dates`.
-   Updated tests using `populated_service` fixture to use dynamic date assertions.
-   Improved financial calculations in `SubscriptionService` to handle different billing cycles.
-   Enhanced subscription status management to properly handle transitions between statuses.
-   Refactored GUI implementation from CustomTkinter to PySimpleGUI to PyQt6 for better cross-platform support.
-   Refactored GUI implementation from Kivy to Streamlit for web-based interactive UI.
-   Refactored file naming to follow consistent snake_case conventions:
    -   Renamed SubscriptionService.py to subscription_service.py
    -   Renamed DateUtils.py to date_utils.py
-   Refactored code structure for improved maintainability:
    -   Added proper logging instead of print statements
    -   Improved error handling and logging
    -   Enhanced docstrings with proper formatting
    -   Added helper methods to simplify complex operations
    -   Made date calculation logic more robust
-   Updated tests to match new structure and naming

### Deprecated

-   Kivy GUI components (`src/gui/app.py`, `src/gui/subtrackerguiapp.kv`).

### Removed

-   Kivy dependency (will be removed from requirements.txt if no longer needed).

### Fixed

-   Corrected assertions in date-related tests to use dynamic calculations.
-   Fixed issue with subscription status not being properly updated when trial periods end.
-   Corrected budget calculation methods for more accurate financial tracking.
-   Resolved issue with renewal dates not being recalculated when billing cycle changes.
-   Fixed memory management issues in GUI components.
-   Fixed renewal date calculation bug for subscriptions without explicit date
-   Improved error handling for trial subscriptions

### Security

-   Added input validation to all user-facing inputs.
-   Implemented secure handling of settings and subscription data.
