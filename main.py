"""
SubTracker - Subscription Management Application

This is the entry point for the SubTracker application, which offers both a
text-based (TUI) and Streamlit web-based interface for managing subscriptions.
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
import platform
from typing import Optional

from src.services.subscription_service import SubscriptionService, DEFAULT_DATA_PATH, DEFAULT_SETTINGS_PATH
# Import the TUI App class directly
from src.tui.app import SubTrackerApp

# Add project root to sys.path to allow imports from src
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
        from src.tui.app import SubTrackerTUIApp # Assuming this is your TUI entry point
        app = SubTrackerTUIApp()
        app.run()
        print("TUI finished.") # Add a message for clean exit
    except ImportError:
        print("Error: Could not import the TUI application.")
        print("Ensure Textual is installed and the TUI code exists in src/tui/.")
    except Exception as e:
        print(f"An error occurred while running the TUI: {e}")

def launch_streamlit_gui():
    """
    Launches the Streamlit GUI application.

    This function uses subprocess to run the Streamlit app.

    Returns:
        None
    """
    print("Launching Streamlit GUI...")
    try:
        # Get the path to the streamlit app
        streamlit_app_path = os.path.join(project_root, "src", "gui", "streamlit_app.py")

        # Run the streamlit app using subprocess
        process = subprocess.Popen(["streamlit", "run", streamlit_app_path])

        # Wait for the process to complete
        process.wait()

        print("Streamlit GUI finished.")
    except Exception as e:
        print("\n--- Streamlit GUI Error ---")
        traceback.print_exc()
        print("--------------------------")

def main(interface_arg: Optional[str] = None):
    """
    Handles launching the application based on command-line argument or interactive menu.

    Args:
        interface_arg: The interface type ('tui' or 'streamlit') passed via command line.

    Returns:
        None
    """
    if interface_arg:
        if interface_arg == "tui":
            run_tui()
        elif interface_arg == "streamlit":
            launch_streamlit_gui()
        else:
            print(f"Invalid interface argument: {interface_arg}. Defaulting to TUI.")
            run_tui()
        return # Exit after launching based on arg

    # --- Interactive Menu (if no argument) --- #
    while True:
        print("\n--- SubTracker ---")
        print("Choose an interface to launch:")
        print("  1: Textual User Interface (TUI)")
        print("  2: Streamlit GUI")
        print("  Q: Quit")

        choice = input("Enter your choice (1, 2, or Q): ").strip().upper()

        if choice == '1':
            run_tui()
            break # Exit after launching
        elif choice == '2':
            launch_streamlit_gui()
            break # Exit after launching
        elif choice == 'Q':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="SubTracker - Subscription Management Application")
    parser.add_argument("--interface", type=str, choices=['tui', 'streamlit'], help="Specify the interface to launch (tui or streamlit)")
    args = parser.parse_args()

    main(interface_arg=args.interface)