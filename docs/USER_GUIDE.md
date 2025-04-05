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
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Keyboard Shortcuts](#keyboard-shortcuts)

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

The Graphical User Interface provides a traditional point-and-click experience with visual elements.

#### GUI Navigation

- **Main Window**: The central hub displaying your subscriptions and summary information.
- **Menu Bar**: Access to file operations and application exit.
- **Status Bar**: Shows application status and messages.

#### GUI Layout

The GUI is organized into two main sections:

1. **Left Panel**: Subscription list with add, edit, and delete buttons.
2. **Right Panel**:
   - **Calendar View**: Visual representation of upcoming renewal dates.
   - **Financial Summary**: Overview of monthly costs per category, spending forecast, and budget alerts.

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

1. Click the "Add" button on the main screen.
2. Fill in the subscription details in the form:
   - **Name**: The service name (required)
   - **Cost**: The amount charged per billing cycle (required)
   - **Billing Cycle**: How often you are charged (required)
   - **Start Date**: When the subscription began (required)
   - **Category**: Type of service (select from dropdown or add new)
   - **Status**: Current subscription status
   - **Additional Fields**: URL, username, notes, etc.
3. Click "Save" to add the subscription.

#### In TUI

1. Press 'a' or click the "Add" button.
2. Navigate through the form fields using Tab or arrow keys.
3. Enter the required information (marked with *).
4. Press Ctrl+S or click "Save" to save the subscription.

### Editing a Subscription

#### In GUI

1. Select the subscription you want to edit from the list.
2. Click the "Edit" button or double-click the subscription item.
3. Modify the details in the edit form.
4. Click "Save" to update the subscription.

#### In TUI

1. Select a subscription from the list using arrow keys or by clicking on it.
2. Press 'e' or click the "Edit" button.
3. Navigate through and modify the form fields.
4. Press Ctrl+S or click "Save" to save your changes.

### Deleting a Subscription

#### In GUI

1. Select the subscription you want to delete.
2. Click the "Delete" button.
3. Confirm the deletion in the dialog box.

#### In TUI

1. Select a subscription from the list.
2. Press 'd' or click the "Delete" button.
3. Confirm the deletion in the confirmation dialog.

## Features

### Financial Summary

The financial summary provides an overview of your subscription situation:

- **Monthly Cost per Category**: Breakdown of spending by category.
- **Spending Forecast**: Upcoming expenses in the next 30 days.
- **Budget Alerts**: Notifications when you exceed your budget limits.

#### In GUI

The financial summary is displayed in the right panel of the main screen with text displays for each section.

#### In TUI

The financial summary is displayed in the right panel of the main screen with information about monthly costs and upcoming expenses.

### Calendar View

The calendar view shows upcoming renewal dates for your subscriptions.

#### In GUI

- The calendar is displayed in the right panel of the main screen.
- Dates with subscription renewals are highlighted.
- Hover over highlighted dates to see subscription details.

#### In TUI

- The calendar is displayed in the right panel of the main screen.
- Dates with subscription renewals are highlighted.
- Select a highlighted date to see subscription details.

### Categories

Categories help you organize subscriptions by type and analyze spending patterns.

#### Managing Categories

The application comes with default categories (Software, Streaming, Utilities, Other) and allows you to assign categories to subscriptions.

### Budget Management

Set spending limits to monitor and control your subscription costs.

#### Setting Budgets

The application allows you to set global and per-category budget limits, which are used to generate budget alerts in the Financial Summary.

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

- **GUI**: Ensure your system meets the minimum requirements for PyQt6.
- **TUI**: Verify your terminal supports colors and has sufficient size.

### Data Backup

It's recommended to periodically back up your subscription data file (`subscriptions.json` by default).

## Keyboard Shortcuts

### GUI Shortcuts

The GUI primarily uses mouse navigation, but you can use standard keyboard shortcuts:

- **Enter**: Activate the selected button
- **Tab/Shift+Tab**: Navigate between form fields
- **Space**: Toggle checkboxes/radio buttons
- **Alt+F4**: Exit the application

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