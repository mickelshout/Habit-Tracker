# habit_tracker.py
import streamlit as st
import datetime
import json
import os
import calendar


def get_deadline(habit):
    today = datetime.date.today()
    last_reset = datetime.date.fromisoformat(habit["last_reset"])

    if habit["frequency"] == "Daily":
        return today

    elif habit["frequency"] == "Weekly":
        # ISO weeks: Monday start → deadline is Sunday
        weekday = today.weekday()  # Monday=0 ... Sunday=6
        return today + datetime.timedelta(days=(6 - weekday))

    elif habit["frequency"] in ["2 weeks", "3 weeks"]:
        n_weeks = int(habit["frequency"].split()[0])
        return last_reset + datetime.timedelta(weeks=n_weeks)

    elif habit["frequency"] == "Monthly":
        # End of this month
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        return datetime.date(today.year, today.month, days_in_month)

    elif "months" in habit["frequency"].lower():
        n_months = int(habit["frequency"].split()[0])
        # Add n months to last_reset
        new_month = (last_reset.month - 1 + n_months) % 12 + 1
        new_year = last_reset.year + (last_reset.month - 1 + n_months) // 12
        days_in_month = calendar.monthrange(new_year, new_month)[1]
        return datetime.date(new_year, new_month, days_in_month)

    else:
        return None

def format_deadline(habit):
    if habit["frequency"] == "Daily":
        return None  # no deadline for daily

    deadline = get_deadline(habit)
    if not deadline:
        return None

    today = datetime.date.today()
    delta_days = (deadline - today).days

    if delta_days < 0:
        return "expired"
    elif delta_days == 0:
        return "today"
    elif delta_days == 1:
        return "tomorrow"
    elif delta_days < 30:
        return f"in {delta_days} days"
    else:
        return deadline.strftime("%-m/%-d")  # e.g. 9/21 (no year)


DATA_FILE = "habits.json"

# --- Helpers ---
def load_habits():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_habits(habits):
    with open(DATA_FILE, "w") as f:
        json.dump(habits, f, indent=4, default=str)

def reset_if_needed(habit):
    today = datetime.date.today()
    last_reset = datetime.date.fromisoformat(habit["last_reset"])
    reset = False

    if habit["frequency"] == "Daily" and last_reset != today:
        reset = True
    elif habit["frequency"] == "Weekly" and today.isocalendar()[1] != last_reset.isocalendar()[1]:
        reset = True
    elif habit["frequency"] in ["2 weeks", "3 weeks"]:
        n_weeks = int(habit["frequency"].split()[0])
        week_diff = (today - last_reset).days // 7
        if week_diff >= n_weeks:
            reset = True
    elif habit["frequency"] == "Monthly" and (today.month != last_reset.month or today.year != last_reset.year):
        reset = True
    elif "months" in habit["frequency"].lower():
        # Parse number of months
        n_months = int(habit["frequency"].split()[0])
        month_diff = (today.year - last_reset.year) * 12 + (today.month - last_reset.month)
        if month_diff >= n_months:
            reset = True

    if reset:
        habit["progress"] = 0
        habit["last_reset"] = str(today)

    return habit

# --- Page setup ---
st.set_page_config(page_title="Habit Tracker", page_icon="✅", layout="centered")
st.title("✨ Habit Tracker")

# Custom CSS
st.markdown(
    """
    <style>
    .habit-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 10px;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.06);
        transition: all 0.2s ease-in-out;
    }
    .habit-card:hover {
        box-shadow: 0px 4px 10px rgba(0,0,0,0.12);
    }
    .habit-title {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 2px;
    }
    .habit-sub {
        color: #666;
        font-size: 12px;
        margin-bottom: 6px;
    }
    .progress-container {
        height: 8px;
        width: 100%;
        background-color: #eee;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 6px;
    }
    .progress-bar {
        height: 100%;
        transition: width 0.3s;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Data ---
if "habits" not in st.session_state:
    st.session_state.habits = load_habits()

st.session_state.habits = [reset_if_needed(h) for h in st.session_state.habits]
save_habits(st.session_state.habits)

# Sidebar: Add new habit
st.sidebar.header("➕ Add a new habit")
name = st.sidebar.text_input("Habit name")

frequency = st.sidebar.selectbox(
    "Frequency",
    ["Daily", "Weekly", "2 weeks", "3 weeks", "Monthly", "2 months", "3 months", "6 months"]
)
goal = st.sidebar.number_input("Goal (times)", min_value=1, value=7)

if st.sidebar.button("Add Habit"):
    new_habit = {
        "name": name,
        "frequency": frequency,
        "goal": goal,
        "progress": 0,
        "last_reset": str(datetime.date.today())
    }
    st.session_state.habits.append(new_habit)
    save_habits(st.session_state.habits)
    st.rerun()

# --- Sorting helper ---
def sort_habits(habits):
    order = {
        "Daily": 1, "Weekly": 2, "2 weeks": 3, "3 weeks": 4,
        "Monthly": 5, "2 months": 6, "3 months": 7, "6 months": 8
    }

    def habit_key(h):
        base_order = order.get(h["frequency"], 99)
        goal_met = h["progress"] >= h["goal"]
        # Sort order:
        # 1. Frequency (low → high)
        # 2. Goal size (high → low → so we negate it)
        # 3. Name alphabetically
        return (
            base_order + (100 if goal_met else 0),
            -h["goal"],
            h["name"].lower()
        )

    return sorted(habits, key=habit_key)

# Sidebar filter
view_filter = st.sidebar.selectbox(
    "Show habits",
    ["All", "Daily", "Weekly", "Monthly"]
)

# --- Display habits ---
if st.session_state.habits:
    st.subheader("📋 Your Habits")
    # Apply filter
    if view_filter != "All":
        if view_filter == "Daily":
            habits_to_show = [h for h in st.session_state.habits if h["frequency"] == "Daily"]
        elif view_filter == "Weekly":
            habits_to_show = [h for h in st.session_state.habits if "week" in h["frequency"].lower()]
        elif view_filter == "Monthly":
            habits_to_show = [h for h in st.session_state.habits if "month" in h["frequency"].lower()]
    else:
        habits_to_show = st.session_state.habits

    for i, habit in enumerate(sort_habits(habits_to_show)):
        progress_ratio = habit["progress"] / habit["goal"]
        progress_width = int(min(progress_ratio, 1) * 100)

        # Colors
        bar_color = "#4CAF50" if habit["progress"] <= habit["goal"] else "#FFD700"
        card_opacity = "0.4" if habit["progress"] >= habit["goal"] else "1.0"

        # Render card with inline buttons
        card = st.container()
        with card:
            col_main, col_btns = st.columns([8, 2])  # wider main, smaller buttons col

            # Left side: habit info
            with col_main:
                deadline_str = format_deadline(habit)
                deadline_html = f" — Deadline: {deadline_str}" if deadline_str else ""

                st.markdown(
                    f"""
                    <div class="habit-card" style="opacity:{card_opacity};">
                        <div class="habit-title">{habit['name']}</div>
                        <div class="habit-sub">{habit['frequency']}{deadline_html}</div>
                        <div class="progress-container">
                            <div class="progress-bar" style="width:{progress_width}%; background-color:{bar_color};"></div>
                        </div>
                        <div class="habit-sub">Progress: {habit['progress']} / {habit['goal']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Right side: buttons centered vertically
            with col_btns:
                st.write("")  # spacer
                st.write("")  # spacer
                bcol1, bcol2, bcol3 = st.columns([1, 1, 1], gap="small")
                with bcol1:
                    if st.button("✅", key=f"done_{i}", help="Mark done"):
                        habit["progress"] += 1
                        save_habits(st.session_state.habits)
                        st.rerun()
                with bcol2:
                    if st.button("➖", key=f"undo_{i}", help="Undo"):
                        if habit["progress"] > 0:
                            habit["progress"] -= 1
                            save_habits(st.session_state.habits)
                            st.rerun()
                with bcol3:
                    if st.button("🗑️", key=f"delete_{i}", help="Delete"):
                        st.session_state.habits.remove(habit)
                        save_habits(st.session_state.habits)
                        st.rerun()

else:
    st.info("No habits yet. Add one from the sidebar!")
