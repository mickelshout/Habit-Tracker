# habit_tracker.py
import streamlit as st
import datetime
import json
import os

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
    ["Daily", "Weekly", "Monthly", "2 months", "3 months", "6 months"]
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
    order = {"Daily": 1, "Weekly": 2, "Monthly": 3,
             "2 months": 4, "3 months": 5, "6 months": 6}

    def habit_key(h):
        base_order = order.get(h["frequency"], 99)
        goal_met = h["progress"] >= h["goal"]
        # Put completed ones at bottom by adding 100
        return (base_order + (100 if goal_met else 0), h["name"].lower())

    return sorted(habits, key=habit_key)

# --- Display habits ---
if st.session_state.habits:
    st.subheader("📋 Your Habits")
    for i, habit in enumerate(sort_habits(st.session_state.habits)):
        progress_ratio = habit["progress"] / habit["goal"]
        progress_width = int(min(progress_ratio, 1) * 100)

        bar_color = "#4CAF50" if habit["progress"] <= habit["goal"] else "#FFD700"

        st.markdown(
            f"""
            <div class="habit-card">
                <div class="habit-title">{habit['name']}</div>
                <div class="habit-sub">{habit['frequency']}</div>
                <div class="progress-container">
                    <div class="progress-bar" style="width:{progress_width}%; background-color:{bar_color};"></div>
                </div>
                <div class="habit-sub">Progress: {habit['progress']} / {habit['goal']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("✅", key=f"done_{i}"):
                habit["progress"] += 1
                save_habits(st.session_state.habits)
                st.rerun()
        with col2:
            if st.button("➖", key=f"undo_{i}"):
                if habit["progress"] > 0:
                    habit["progress"] -= 1
                    save_habits(st.session_state.habits)
                    st.rerun()
        with col3:
            if st.button("🗑️", key=f"delete_{i}"):
                st.session_state.habits.remove(habit)
                save_habits(st.session_state.habits)
                st.rerun()
else:
    st.info("No habits yet. Add one from the sidebar!")
