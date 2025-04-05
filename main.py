"""
SubTracker - Subscription Management Application

This is the entry point for the SubTracker application, which offers both a
text-based (TUI) and graphical (GUI) interface for managing subscriptions.
Users can track, manage, and analyze their recurring subscriptions through
either interface based on their preference.

Usage:
    python main.py

The application will present a menu allowing users to choose their preferred
interface or exit the application.
"""

import argparse
import os
import subprocess
import sys
import traceback # Import traceback

from src.services.subscription_service import SubscriptionService, DEFAULT_DATA_PATH, DEFAULT_SETTINGS_PATH
# Import the GUI entry point
from src.gui.app import run_gui # Corrected import name
# Import the TUI App class directly
from src.tui.app import SubTrackerApp

def run_tui():
    """
    Launches the Textual TUI application directly.

    This function initializes and runs the SubTrackerApp instance, which provides
    a text-based user interface for the application. Any exceptions that occur
    during execution are caught and their tracebacks are printed to help with debugging.

    Returns:
        None
    """
    print("Launching TUI...")
    try:
        # Instantiate and run the app directly
        app = SubTrackerApp()
        app.run()
        print("TUI finished.") # Add a message for clean exit
    except Exception as e:
        # Print the full traceback if an error occurs
        print("\n--- TUI Error ---")
        traceback.print_exc()
        print("-----------------")

def launch_gui():
    """
    Launches the PyQt GUI application.

    This function initializes the SubscriptionService and passes it to the GUI
    application. Any exceptions that occur during execution are caught and
    their tracebacks are printed to help with debugging.

    Returns:
        None
    """
    print("Launching GUI...")
    try:
        # Instantiate the service for the GUI
        service = SubscriptionService()
        # Call the imported run_gui function correctly
        run_gui(service) # Call the imported GUI function with the service
        print("GUI finished.")
    except Exception as e:
        print("\n--- GUI Error ---")
        traceback.print_exc()
        print("-----------------")

def main():
    """
    Presents the choice menu and launches the selected interface.

    This function displays a menu that allows the user to choose between
    the TUI and GUI interfaces, or to quit the application. It continues
    to prompt until a valid choice is made.

    Returns:
        None
    """
    while True:
        print("\n--- SubTracker ---")
        print("Choose an interface to launch:")
        print("  1: Textual User Interface (TUI)")
        print("  2: Graphical User Interface (GUI)")
        print("  Q: Quit")

        choice = input("Enter your choice (1, 2, or Q): ").strip().upper()

        if choice == '1':
            run_tui()
            break # Exit after launching
        elif choice == '2':
            launch_gui()
            break # Exit after launching
        elif choice == 'Q':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()