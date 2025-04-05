"""
Streamlit GUI for SubTracker.

This script provides the main graphical user interface using the Streamlit framework.
"""

from re import sub
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import uuid # For potential key generation if needed
from streamlit_calendar import calendar # Import the calendar component

# Adjust import paths based on your project structure
import sys
import os

# Add the project root to the Python path to allow importing from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.services.subscription_service import SubscriptionService
    from src.models.subscription import Subscription, BillingCycle, SubscriptionStatus
except ImportError as e:
    st.error(f"Error importing SubTracker modules: {e}. Make sure the script is run from the project root or the PYTHONPATH is set correctly.")
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="SubTracker Dashboard",
    layout="wide", # Use wide layout
    initial_sidebar_state="collapsed" # Sidebar is not used but keep the setting
)

# --- Service Initialization ---
# Ensure the service uses the correct data path relative to the project root
DATA_DIR = os.path.join(project_root, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
DATA_PATH = os.path.join(DATA_DIR, 'subscriptions.json')

# Initialize session state variables
if 'editing_sub_id' not in st.session_state:
    st.session_state.editing_sub_id = None
if 'deleting_sub_id' not in st.session_state:
    st.session_state.deleting_sub_id = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'show_edit_form' not in st.session_state:
    st.session_state.show_edit_form = False
if 'budgets' not in st.session_state:
    st.session_state.budgets = {}
if 'categories' not in st.session_state:
    st.session_state.categories = []

@st.cache_resource # Cache the service object across reruns
def get_subscription_service():
    """Initializes and returns the SubscriptionService instance."""
    try:
        return SubscriptionService(data_path=DATA_PATH)
    except Exception as e:
        st.error(f"Failed to initialize SubscriptionService: {e}")
        st.stop()

service = get_subscription_service()

# --- Helper Functions ---
def format_subscription_for_display(sub: Subscription) -> dict:
    """Formats a Subscription object into a dictionary for display in DataFrame."""
    return {
        'ID': sub.id,
        'Name': sub.name,
        'Cost': sub.cost, # Keep raw cost for calculations
        'Currency': sub.currency, # Keep currency
        'BillingCycle': sub.billing_cycle, # Keep enum for calculations
        'Cost Display': f"{sub.currency} {sub.cost:.2f}", # Formatted cost for display
        'Cycle Display': sub.billing_cycle.name.capitalize(), # Formatted cycle for display
        'Next Renewal': sub.next_renewal_date.strftime("%Y-%m-%d") if sub.next_renewal_date else "N/A",
        'Status': sub.status, # Keep enum
        'Status Display': sub.status.name.capitalize(), # Formatted status
        'Category': sub.category or "Uncategorized",
        'Start Date': sub.start_date.strftime("%Y-%m-%d") if sub.start_date else "-",
        'URL': sub.url or "-",
        # Add other relevant fields from the Subscription model if needed
    }

def refresh_data():
    """Clears relevant caches and potentially reruns parts of the app."""
    # In Streamlit, data usually refreshes on rerun.
    # If using st.cache_data for subscriptions, clear it here.
    # st.cache_data.clear()
    # Use experimental_rerun instead of rerun if available and needed
    st.rerun()

def toggle_add_form():
    """Toggle the display of the add subscription form."""
    st.session_state.show_add_form = not st.session_state.show_add_form
    # If showing add form, make sure edit form is hidden
    if st.session_state.show_add_form:
        st.session_state.show_edit_form = False
        st.session_state.editing_sub_id = None
    st.rerun()

def toggle_edit_form(sub_id=None):
    """Toggle the display of the edit subscription form."""
    if sub_id is not None:
        st.session_state.editing_sub_id = sub_id
        st.session_state.show_edit_form = True
        # Hide add form when showing edit form
        st.session_state.show_add_form = False
    else:
        st.session_state.show_edit_form = False
        st.session_state.editing_sub_id = None
    st.rerun()

# --- New Helper Function: Calculate Monthly Cost ---
def calculate_monthly_cost(cost: float, cycle: BillingCycle) -> float:
    """Calculates the approximate monthly cost based on the billing cycle."""
    monthly_cost = 0.0 # Default value
    if cycle == BillingCycle.MONTHLY:
        monthly_cost = cost
        # Removed annual_cost calculation as it's not used here
    elif cycle == BillingCycle.YEARLY:
        monthly_cost = cost / 12
    elif cycle == BillingCycle.WEEKLY:
        # Approximate monthly cost (assuming ~4.33 weeks per month)
        monthly_cost = cost * (52 / 12)
    elif cycle == BillingCycle.QUARTERLY:
        monthly_cost = cost / 3
    elif cycle == BillingCycle.BI_ANNUALLY:
        monthly_cost = cost / 24
    elif cycle == BillingCycle.OTHER:
        monthly_cost = 0.0 # Explicitly set for clarity
    # No need for else, covered by default

    return monthly_cost # Return the calculated value

# --- New Helper Function: Get Unique Categories ---
def get_unique_categories(subscriptions: list[Subscription]) -> list[str]:
    """Extracts unique categories from a list of subscriptions."""
    # Use session state categories as the base, add any from current subs
    cats = set(st.session_state.get('categories', []))
    for sub in subscriptions:
        if sub.category:
            cats.add(sub.category)
    sorted_cats = sorted(list(cats))
    # Update session state if different
    if st.session_state.get('categories') != sorted_cats:
        st.session_state.categories = sorted_cats
    return sorted_cats

# --- Main App Layout ---
st.title("📊 SubTracker Dashboard")

st.markdown("Manage your subscriptions efficiently.")

# Fetch subscriptions early, as multiple sections need it
all_subs = service.get_all_subscriptions()
active_subs = [sub for sub in all_subs if sub.status == SubscriptionStatus.ACTIVE]

# Get unique categories
unique_categories = get_unique_categories(all_subs)

# --- Notifications & Calendar Section ---
st.header("🔔 Notifications & Calendar")

notifications_area = st.container() # Placeholder for text notifications

# --- Budget Warnings ---
budget_warnings = []
category_monthly_costs = defaultdict(float)
for sub in active_subs: # Only consider active subs for budget calculation
    monthly_cost = calculate_monthly_cost(sub.cost, sub.billing_cycle)
    category_monthly_costs[sub.category] += monthly_cost

for category, total_cost in category_monthly_costs.items():
    budget = st.session_state.budgets.get(category)
    if budget is not None and budget > 0 and total_cost > budget: # Check if budget is set and exceeded
        budget_warnings.append(
            f"Budget Exceeded for **{category}**: Monthly cost is **{total_cost:.2f}**, budget is **{budget:.2f}**."
        )

# --- Upcoming Renewals ---
upcoming_renewals = []
today = date.today()
renewal_threshold = today + timedelta(days=7) # Notify for renewals within 7 days

for sub in active_subs: # Check active subscriptions for upcoming renewals
    if sub.next_renewal_date and today <= sub.next_renewal_date <= renewal_threshold:
        days_left = (sub.next_renewal_date - today).days
        day_str = "day" if days_left == 1 else "days"
        upcoming_renewals.append(
            f"**{sub.name}** renews in **{days_left} {day_str}** (on {sub.next_renewal_date.strftime('%Y-%m-%d')})."
        )

# --- Display Notifications ---
with notifications_area:
    if budget_warnings:
        st.subheader("Budget Alerts")
        for warning in budget_warnings:
            st.warning(warning)
    else:
        st.info("✅ All categories are within budget.")

    st.markdown("---") # Separator

    if upcoming_renewals:
        st.subheader("Upcoming Renewals (Next 7 Days)")
        for renewal in upcoming_renewals:
            st.info(renewal)
    else:
        st.info("No immediate renewals in the next 7 days.")

# --- Calendar Display (Kept for visual overview) ---
st.subheader("📅 Renewal Calendar")

# Prepare events for the calendar
calendar_events = []
calendar_events.extend(
    {
        "title": sub.name,
        "color": "#FF6347",  # Example color (Tomato), customize as needed
        "start": sub.next_renewal_date.isoformat(),
        "end": sub.next_renewal_date.isoformat(),  # Make it an all-day event
        "resourceId": sub.id,  # Optional: Link event to subscription ID
    }
    for sub in all_subs
    if sub.next_renewal_date
)
# Calendar options (customize as needed)
# Reference: https://github.com/im-perativa/streamlit-calendar?tab=readme-ov-file#options
calendar_options = {
    "height": 400, # Set calendar height in pixels
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay",
    },
    "initialView": "dayGridMonth",
    "resourceGroupField": "id", # Corresponds to 'resourceId' in events
    "editable": False, # Set to True if you want drag-and-drop editing
    "selectable": True,
}

# Custom CSS for the calendar (optional, example to make it fit better)
calendar_css = """
    .fc-event-past {
        opacity: 0.8;
    }
    .fc-event-time {
        font-style: italic;
    }
    .fc-event-title {
        font-weight: 700;
    }
    .fc-toolbar-title {
        font-size: 1.5rem;
    }
"""

# Render the calendar
# Note: The calendar might return data on interaction (e.g., date click)
calendar_widget_state = calendar(
    events=calendar_events,
    options=calendar_options,
    custom_css=calendar_css,
    key="renewal_calendar" # Unique key for the component
)

# Optional: Display details based on calendar interaction
# if calendar_widget_state.get("eventClick"):
#    clicked_event_title = calendar_widget_state["eventClick"]["event"]["title"]
#    st.info(f"Clicked on: {clicked_event_title}")

st.divider() # Add a separator

# --- Budget Overview Section ---
st.header("💰 Budget Overview")

if not unique_categories:
    st.info("Add subscriptions with categories to set budgets.")
else:
    budget_cols = st.columns(3) # Adjust number of columns as needed
    for col_idx, category in enumerate(unique_categories):
        with budget_cols[col_idx % len(budget_cols)]:
            st.subheader(f"{category}")
            total_monthly = category_monthly_costs.get(category, 0.0)
            st.metric(label="Current Monthly Total", value=f"{total_monthly:.2f}")

            # Use number input for setting budget, retrieve from session state
            current_budget = st.session_state.budgets.get(category, 0.0)
            new_budget = st.number_input(
                f"Set Budget for {category}",
                min_value=0.0,
                value=current_budget,
                step=10.0,
                key=f"budget_input_{category}", # Unique key per category
                format="%.2f"
            )
            # Update session state if the budget changed
            if new_budget != current_budget:
                st.session_state.budgets[category] = new_budget
                st.rerun() # Rerun to reflect budget change immediately in notifications
            st.markdown("<hr>", unsafe_allow_html=True) # Visual separator between categories in columns
st.divider() # Add a separator

# --- Display Subscriptions Section ---
# Combine header and Add button
col_header, col_add_button = st.columns([0.8, 0.2])
with col_header:
    st.header("Subscriptions List") # Renamed for clarity
with col_add_button:
    st.write("") # Add space for alignment
    st.write("")
    if st.button("➕ Add New Subscription", key="add_btn", use_container_width=True):
        # Toggle the add form visibility
        toggle_add_form()

if not all_subs:
    st.info("No subscriptions found. Add one using the button above!")
else:
    # --- Subscription Rows ---
    # Session state initialization moved to top of the file
    sub_to_delete_confirmed = None # Track confirmed deletion outside loop

    # Prepare data for DataFrame display (optional, but can be cleaner)
    display_data = []
    for sub in all_subs:
        sub_data = format_subscription_for_display(sub)
        display_data.append({
            'Status': sub_data['Status Display'],
            'Name': sub_data['Name'],
            'Cost': sub_data['Cost Display'],
            'Cycle': sub_data['Cycle Display'],
            'Next Renewal': sub_data['Next Renewal'],
            'Category': sub_data['Category'],
            'Start Date': sub_data['Start Date'],
            'ID': sub.id # Keep ID for actions
        })

    df_display = pd.DataFrame(display_data)

    # Display using st.columns for layout control with buttons
    # Headers first
    cols = st.columns([1, 3, 2, 1, 2, 1.5, 1.5, 0.5, 0.5]) # Adjusted column widths
    headers = ['Status', 'Name', 'Cost', 'Cycle', 'Next Renewal', 'Category', 'Start Date', 'Edit', 'Del']
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")
    st.divider() # Visual separator for header

    # Rows with data and action buttons
    for index, row in df_display.iterrows():
        sub_id = row['ID']
        current_sub = next((s for s in all_subs if s.id == sub_id), None) # Get the original Subscription object
        if not current_sub: continue # Skip if somehow not found

        cols = st.columns([1, 3, 2, 1, 2, 1.5, 1.5, 0.5, 0.5]) # Same widths as header

        # Status dropdown (remains similar)
        current_status = current_sub.status
        status_options = list(SubscriptionStatus)
        status_display = {
            SubscriptionStatus.ACTIVE: "🟢 Active",
            SubscriptionStatus.INACTIVE: "🟠 Inactive",
            SubscriptionStatus.CANCELLED: "🔴 Cancelled",
            SubscriptionStatus.TRIAL: "🔵 Trial"
        }
        status_index = status_options.index(current_status)
        new_status_display = cols[0].selectbox(
            "Status",
            options=[status_display[status] for status in status_options],
            index=status_index,
            key=f"status_select_{sub_id}",
            label_visibility="collapsed"
        )
        selected_status_index = list(status_display.values()).index(new_status_display)
        selected_status = list(status_display.keys())[selected_status_index]

        if selected_status != current_status:
            if service.update_subscription(sub_id, {'status': selected_status}):
                st.toast(f"Updated status for '{current_sub.name}' to {selected_status.name}")
                st.rerun()
            else:
                st.error(f"Failed to update status for '{current_sub.name}'.")

        # Display other data
        cols[1].write(row['Name'])
        cols[2].write(row['Cost'])
        cols[3].write(row['Cycle'])
        cols[4].write(row['Next Renewal'])
        cols[5].write(row['Category'])
        cols[6].write(row['Start Date'])

        # Edit Button
        if cols[7].button("✏️", key=f"edit_{sub_id}", help="Edit Subscription"):
            toggle_edit_form(sub_id)

        # Delete Button / Confirmation
        if st.session_state.get('deleting_sub_id') == sub_id:
            if cols[8].button("✅ Confirm", key=f"confirm_delete_{sub_id}", help="Confirm Deletion"):
                if service.delete_subscription(sub_id):
                    st.toast(f"Subscription '{current_sub.name}' deleted.")
                    refresh_data() # Rerun to update list
                else:
                    st.error("Failed to delete subscription.")
                st.session_state.deleting_sub_id = None # Reset deletion state
            if st.button("❌ Cancel", key=f"cancel_delete_{sub_id}"): # Add a cancel button nearby or handle differently
                 st.session_state.deleting_sub_id = None
                 st.rerun()
        else:
            if cols[8].button("🗑️", key=f"delete_{sub_id}", help="Delete Subscription"):
                st.session_state.deleting_sub_id = sub_id
                st.rerun() # Rerun to show confirmation

        st.markdown("---", unsafe_allow_html=False) # Separator between rows

# --- Add Subscription Form ---
if st.session_state.show_add_form:
    st.header("➕ Add New Subscription")
    with st.form("add_subscription_form"):
        name = st.text_input("Subscription Name*", key="add_name")
        cost = st.number_input("Cost per cycle*", min_value=0.0, format="%.2f", key="add_cost")
        currency = st.text_input("Currency", value="USD", key="add_currency")
        billing_cycle = st.selectbox("Billing Cycle*", options=[e for e in BillingCycle], format_func=lambda x: x.name.capitalize(), key="add_cycle")

        # Category Selection with Add New
        current_categories = get_unique_categories(all_subs) # Ensure list is up-to-date
        category_options = sorted(current_categories) + ["Add New Category..."]
        selected_category_option = st.selectbox("Category", options=category_options, key="add_category_select")

        new_category_name = ""
        if selected_category_option == "Add New Category...":
            new_category_name = st.text_input("Enter New Category Name", key="add_new_category_name")

        start_date = st.date_input("Start Date*", value=datetime.today(), key="add_start_date")
        status = st.selectbox("Status", options=[e for e in SubscriptionStatus], format_func=lambda x: x.name.capitalize(), key="add_status")
        url = st.text_input("URL", key="add_url")
        username = st.text_input("Username/Email", key="add_username")
        notes = st.text_area("Notes", key="add_notes")

        submitted = st.form_submit_button("Add Subscription")
        if submitted:
            # Determine the category to save
            final_category = new_category_name if selected_category_option == "Add New Category..." and new_category_name else selected_category_option

            if not name or cost is None or billing_cycle is None or start_date is None or not final_category or final_category == "Add New Category...":
                st.error("Please fill in all required fields, including a valid category.")
            else:
                # Convert date to date object if it's datetime
                if isinstance(start_date, datetime):
                    start_date = start_date.date()

                new_sub_data = {
                    'name': name,
                    'cost': float(cost),
                    'billing_cycle': billing_cycle,
                    'start_date': start_date,
                    'category': final_category,
                    'status': status,
                    'currency': currency,
                    'url': url or None,
                    'username': username or None,
                    'notes': notes,
                    # Add other fields as necessary, e.g., next_renewal_date calculation might be needed
                }
                # Add the new subscription via the service
                try:
                    # Create a Subscription object from the dictionary
                    new_sub_obj = Subscription(**new_sub_data)
                    if service.add_subscription(new_sub_obj): # Pass the Subscription object
                        st.success(f"Subscription '{name}' added successfully!")
                        # If a new category was added, update the session state list
                        if new_category_name and new_category_name not in st.session_state.categories:
                             st.session_state.categories.append(new_category_name)
                             st.session_state.categories.sort() # Keep it sorted
                        st.session_state.show_add_form = False # Hide form
                        refresh_data() # Rerun to update the list and categories
                    else:
                        st.error("Failed to add subscription.")
                except Exception as e:
                    st.error(f"Error adding subscription: {e}")

# --- Edit Subscription Form ---
if st.session_state.show_edit_form and st.session_state.editing_sub_id:
    st.header("✏️ Edit Subscription")
    sub_to_edit = service.get_subscription_by_id(st.session_state.editing_sub_id)

    if sub_to_edit:
        with st.form("edit_subscription_form"):
            # Pre-fill form with existing data
            name = st.text_input("Subscription Name*", value=sub_to_edit.name, key="edit_name")
            cost = st.number_input("Cost per cycle*", min_value=0.0, value=sub_to_edit.cost, format="%.2f", key="edit_cost")
            currency = st.text_input("Currency", value=sub_to_edit.currency, key="edit_currency")

            # Find the index for the current billing cycle
            cycle_options = list(BillingCycle)
            current_cycle_index = cycle_options.index(sub_to_edit.billing_cycle) if sub_to_edit.billing_cycle in cycle_options else 0
            billing_cycle = st.selectbox("Billing Cycle*", options=cycle_options, index=current_cycle_index, format_func=lambda x: x.name.capitalize(), key="edit_cycle")

            # Category Selection with Add New for Edit Form
            current_categories = get_unique_categories(all_subs) # Ensure list is up-to-date
            category_options = sorted(current_categories) + ["Add New Category..."]
            # Find index for current category, default to 0 if not found or is None
            try:
                current_category_index = category_options.index(sub_to_edit.category) if sub_to_edit.category in category_options else 0
            except ValueError:
                 current_category_index = 0 # Handle case where category might not be in list (e.g. deleted)

            selected_category_option = st.selectbox("Category", options=category_options, index=current_category_index, key="edit_category_select")

            new_category_name = ""
            if selected_category_option == "Add New Category...":
                new_category_name = st.text_input("Enter New Category Name", key="edit_new_category_name")

            # Convert date object to datetime for date_input if needed, or ensure it works with date
            start_date_value = sub_to_edit.start_date or datetime.today().date()
            start_date = st.date_input("Start Date*", value=start_date_value, key="edit_start_date")

            # Find index for current status
            status_options = list(SubscriptionStatus)
            current_status_index = status_options.index(sub_to_edit.status) if sub_to_edit.status in status_options else 0
            status = st.selectbox("Status", options=status_options, index=current_status_index, format_func=lambda x: x.name.capitalize(), key="edit_status")

            url = st.text_input("URL", value=sub_to_edit.url or "", key="edit_url")
            username = st.text_input("Username/Email", value=sub_to_edit.username or "", key="edit_username")
            notes = st.text_area("Notes", value=sub_to_edit.notes or "", key="edit_notes")

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Update Subscription")
            with col2:
                cancelled = st.form_submit_button("Cancel", type="secondary")

            if submitted:
                # Determine the category to save
                final_category = new_category_name if selected_category_option == "Add New Category..." and new_category_name else selected_category_option

                if not name or cost is None or billing_cycle is None or start_date is None or not final_category or final_category == "Add New Category...":
                    st.error("Please fill in all required fields, including a valid category.")
                else:
                    # Convert date to date object if necessary
                    if isinstance(start_date, datetime):
                        start_date = start_date.date()

                    updated_data = {
                        'name': name,
                        'cost': float(cost),
                        'billing_cycle': billing_cycle,
                        'start_date': start_date,
                        'category': final_category,
                        'status': status,
                        'currency': currency,
                        'url': url or None,
                        'username': username or None,
                        'notes': notes,
                        # Update other fields as necessary
                    }
                    if service.update_subscription(st.session_state.editing_sub_id, updated_data):
                        st.success(f"Subscription '{name}' updated successfully!")
                        # If a new category was added, update the session state list
                        if new_category_name and new_category_name not in st.session_state.categories:
                             st.session_state.categories.append(new_category_name)
                             st.session_state.categories.sort()
                        st.session_state.show_edit_form = False # Hide form
                        st.session_state.editing_sub_id = None
                        refresh_data() # Rerun to update list
                    else:
                        st.error("Failed to update subscription.")
            if cancelled:
                 st.session_state.show_edit_form = False # Hide form
                 st.session_state.editing_sub_id = None
                 st.rerun()

    else:
        st.error("Subscription to edit not found.")
        st.session_state.show_edit_form = False
        st.session_state.editing_sub_id = None

# --- Footer ---
st.divider()
st.markdown("--- SubTracker --- Developed with Streamlit ---")
