# SubTracker

A comprehensive subscription management application that helps users track, manage, and analyse their recurring subscriptions through both GUI and TUI interfaces.

## Overview

SubTracker is designed to help you take control of your subscriptions by providing a unified platform to:

- Track all your recurring subscriptions in one place
- Monitor upcoming renewal dates
- Analyze spending by category
- Set budget limits and receive alerts
- Access your data through either a graphical or text-based interface

## Features

- **Dual Interfaces**: Choose between a graphical user interface (GUI) built with PyQt6 or a text-based user interface (TUI) built with Textual
- **Subscription Management**: Add, view, edit, and delete subscriptions with detailed information
- **Financial Tracking**: Monitor monthly/yearly costs, view spending by category, and set budgets
- **Renewal Notifications**: See upcoming renewals in a calendar view
- **Data Persistence**: All data is stored locally in JSON format for privacy and control
- **Customization**: Define custom categories and tailor the application to your needs

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/subtracker.git
   cd subtracker
   ```
2. Create and activate a virtual environment (recommended):

   ```
   python -m venv .venv

   # On Windows
   .\.venv\Scripts\activate

   # On macOS/Linux
   source .venv/bin/activate
   ```
3. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

## Usage

Launch the application:

```
python main.py
```

This will present a menu where you can choose between:

1. Textual User Interface (TUI)
2. Graphical User Interface (GUI)

### GUI Interface

The graphical interface provides a user-friendly experience with:

- Dashboard overview of subscription costs and upcoming renewals
- List view with all subscription details
- Form-based editors for adding and modifying subscriptions
- Visual charts for spending analysis

### TUI Interface

The text-based interface offers an efficient command-line experience with:

- Keyboard-driven navigation
- List view of all subscriptions
- Form-based editors for adding and modifying data
- Calendar view of upcoming renewals
- Text-based charts for spending analysis

## Configuration

SubTracker stores its configuration in the `config/settings.json` file, which includes:

- Path to the data file
- List of subscription categories
- Budget settings

The default data file location is `subscriptions.json` in the application's root directory.

## Documentation

For more detailed information, please refer to the documentation:

- [User Guide](docs/USER_GUIDE.md) - Detailed instructions for using the application
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Information for developers working with the codebase
- [Architecture Document](docs/ARCHITECTURE.md) - Overview of the application's architecture
- [Tools Document](docs/TOOLS.md) - Information about the tools and libraries used

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt6 for the GUI framework
- Textual for the TUI framework
- All contributors who have helped shape this project
