# SubTracker User Guide

This guide provides comprehensive instructions for using the SubTracker application to manage your subscriptions effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interfaces](#interfaces)
   - [GUI Interface](#gui-interface)
   - [TUI Interface](#tui-interface)
3. [Managing Subscriptions](#managing-subscriptions)
   - [Adding a Subscription](#adding-a-subscription)
   - [Editing a Subscription](#editing-a-subscription)
   - [Deleting a Subscription](#deleting-a-subscription)
4. [Features](#features)
   - [Financial Summary](#financial-summary)
   - [Calendar View](#calendar-view)
   - [Categories](#categories)
   - [Budget Management](#budget-management)
   - [Notifications](#notifications)
5. [Billing Cycles](#billing-cycles)
6. [Subscription Status](#subscription-status)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Keyboard Shortcuts](#keyboard-shortcuts)

## Getting Started

### Installation

1. Ensure you have Python 3.10 or higher installed on your system.
2. Clone or download the SubTracker repository.
3. Create and activate a virtual environment (recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### First Launch

1. Run the application:
   ```
   python main.py
   ```
2. Choose your preferred interface:
   - Option 1: Textual User Interface (TUI)
   - Option 2: Graphical User Interface (GUI)
   - Option Q: Quit

## Interfaces

SubTracker offers two interface options to accommodate different user preferences and environments.

### GUI Interface

The Graphical User Interface provides a web-based experience powered by Streamlit.

#### GUI Layout

The GUI dashboard is organized into several main sections:

1. **Notifications & Calendar**
   - Budget alerts for categories exceeding their budget limits
   - Upcoming renewals within the next 7 days
   - Calendar view displaying subscription renewal dates

2. **Budget Overview**
   - Monthly costs per category
   - Budget setting controls for each category
   - Visual indicators for budget status

3. **Subscriptions List**
   - Table view of all subscriptions
   - Quick status updates through dropdown selectors
   - Edit and delete actions
   - Add new subscription button

#### GUI Navigation

- **Subscription Management**: Add, edit, and delete subscriptions from the list view
- **Status Updates**: Change subscription status directly from the dropdown in the list
- **Budget Controls**: Set category budgets using the input fields in the Budget Overview section
- **Calendar View**: Navigate between months and view upcoming renewals

### TUI Interface

The Text-based User Interface provides a keyboard and mouse-driven experience optimized for terminal use.

#### TUI Navigation

- **Keyboard Navigation**: Navigate between elements using Tab/Shift+Tab or arrow keys.
- **Mouse Navigation**: The TUI is fully navigatable with the mouse - click on buttons, links, and form elements directly.
- **Keyboard Shortcuts**: Quick access to common functions (a: Add, e: Edit, d: Delete, r: Refresh, q: Quit).

#### TUI Layout

The TUI is organized into two main sections:

1. **Left Panel**: Subscription list with add, edit, and delete buttons.
2. **Right Panel**:
   - **Calendar View**: Monthly view of upcoming renewals.
   - **Financial Summary**: Overview of your subscription costs.

## Managing Subscriptions

### Adding a Subscription

#### In GUI

1. Click the "➕ Add New Subscription" button on the main screen.
2. Fill in the subscription details in the form:
   - **Name**: The service name (required)
   - **Cost**: The amount charged per billing cycle (required)
   - **Currency**: The currency code (default: USD)
   - **Billing Cycle**: How often you are charged (required)
   - **Category**: Type of service (select from dropdown or add new)
   - **Start Date**: When the subscription began (required)
   - **Status**: Current subscription status
   - **Additional Fields**: URL, username, notes
3. Click "Add Subscription" to save the new subscription.

#### In TUI

1. Press 'a' or click the "Add" button.
2. Navigate through the form fields using Tab or arrow keys.
3. Enter the required information (marked with *).
4. Press Ctrl+S or click "Save" to save the subscription.

### Editing a Subscription

#### In GUI

1. Locate the subscription you want to edit in the list.
2. Click the "✏️" (edit) button in the same row.
3. Modify the details in the edit form.
4. Click "Update Subscription" to save your changes.

#### In TUI

1. Select a subscription from the list using arrow keys or by clicking on it.
2. Press 'e' or click the "Edit" button.
3. Navigate through and modify the form fields.
4. Press Ctrl+S or click "Save" to save your changes.

### Deleting a Subscription

#### In GUI

1. Locate the subscription you want to delete in the list.
2. Click the "🗑️" (delete) button in the same row.
3. Click "✅ Confirm" to confirm deletion or "❌ Cancel" to cancel.

#### In TUI

1. Select a subscription from the list.
2. Press 'd' or click the "Delete" button.
3. Confirm the deletion in the confirmation dialog.

## Features

### Financial Summary

The financial summary provides an overview of your subscription situation:

- **Monthly Cost per Category**: Breakdown of spending by category.
- **Total Monthly Cost**: Sum of all active subscriptions converted to monthly amounts.
- **Budget Alerts**: Notifications when you exceed your budget limits.

### Calendar View

The calendar view shows upcoming renewal dates for your subscriptions.

- Subscriptions are displayed on their renewal dates
- Navigate between months using the calendar controls
- View day, week, or month layouts
- Renewal dates are color-coded for visibility

### Categories

Categories help you organize subscriptions by type and analyze spending patterns.

#### Managing Categories

- The application comes with default categories (Software, Streaming, Utilities, Other)
- Add new categories when creating or editing a subscription
- Assign subscriptions to categories to track spending by type
- Set budget limits per category

### Budget Management

Set spending limits to monitor and control your subscription costs.

#### Setting Budgets

1. Navigate to the Budget Overview section
2. Find the category you want to set a budget for
3. Enter the monthly budget amount in the input field
4. Budget changes take effect immediately and update alerts

### Notifications

The application provides two types of notifications:

1. **Budget Alerts**: Warnings when a category exceeds its budget limit
2. **Renewal Notifications**: Information about subscriptions renewing in the next 7 days

## Billing Cycles

SubTracker supports various billing cycles to accommodate different subscription types:

- **Monthly**: Billed once per month (e.g., Netflix, Spotify)
- **Yearly/Annually**: Billed once per year (e.g., Amazon Prime, domain registrations)
- **Quarterly**: Billed once every three months
- **Weekly**: Billed once per week (e.g., certain newspaper subscriptions)
- **Bi-Annually**: Billed once every two years (e.g., some domain registrations)
- **Other**: Custom billing cycles not covered by standard options

The application automatically converts all costs to monthly amounts for budget tracking and comparison.

## Subscription Status

Subscriptions can have the following statuses:

- **Active**: Currently active and being charged
- **Inactive**: Temporarily paused but not cancelled
- **Cancelled**: Permanently cancelled
- **Trial**: In a trial period

Active subscriptions are included in budget calculations and renewal notifications.

## Configuration

SubTracker stores its settings in `config/settings.json`. Key configuration options include:

- **data_path**: Location of the subscription data file.
- **categories**: List of available subscription categories.
- **budget**: Budget settings for global and per-category limits.

## Troubleshooting

### Common Issues

#### Data Not Saving

- Ensure you have write permissions to the data file location.
- Check for disk space issues.
- Verify the application has closed properly after previous sessions.

#### Interface Display Problems

- **GUI**: Ensure your system meets the minimum requirements for Streamlit.
- **TUI**: Verify your terminal supports colors and has sufficient size.

### Data Backup

It's recommended to periodically back up your subscription data file (`data/subscriptions.json` by default).

## Keyboard Shortcuts

### GUI Shortcuts

The GUI primarily uses mouse navigation through the Streamlit interface.

### TUI Shortcuts

- **a**: Add subscription
- **e**: Edit selected subscription
- **d**: Delete selected subscription
- **r**: Refresh data
- **d**: Toggle dark mode
- **q**: Quit
- **Tab/Shift+Tab**: Navigate between elements
- **Arrow keys**: Navigate within lists and forms
- **Enter**: Select or activate
- **Escape**: Cancel or back
- **Ctrl+S**: Save form (in dialogs)