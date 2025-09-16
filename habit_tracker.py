# habit_tracker.py
import streamlit as st
import datetime

st.set_page_config(page_title="Habit Tracker", page_icon="✅", layout="centered")

st.title("✨ Habit Tracker")

if "habits" not in st.session_state:
    st.session_state.habits = []

# Sidebar: Add new habit
st.sidebar.header("➕ Add a new habit")
name = st.sidebar.text_input("Habit name")
frequency = st.sidebar.selectbox("Frequency", ["Daily", "Weekly", "Monthly"])
goal = st.sidebar.number_input("Goal (times)", min_value=1, value=7)

if st.sidebar.button("Add Habit"):
    st.session_state.habits.append({
        "name": name,
        "frequency": frequency,
        "goal": goal,
        "progress": 0,
        "last_reset": datetime.date.today()
    })

# Reset habits if timeframe passed
today = datetime.date.today()
for habit in st.session_state.habits:
    reset = False
    if habit["frequency"] == "Daily" and habit["last_reset"] != today:
        reset = True
    elif habit["frequency"] == "Weekly" and today.isocalendar()[1] != habit["last_reset"].isocalendar()[1]:
        reset = True
    elif habit["frequency"] == "Monthly" and (today.month != habit["last_reset"].month or today.year != habit["last_reset"].year):
        reset = True

    if reset:
        habit["progress"] = 0
        habit["last_reset"] = today

# Show habits
if st.session_state.habits:
    st.subheader("📋 Your Habits")
    for i, habit in enumerate(st.session_state.habits):
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.markdown(f"**{habit['name']}**\n{habit['frequency']}")
        with col2:
            st.markdown(f"Progress: {habit['progress']} / {habit['goal']}")
        with col3:
            if st.button("✅ Done", key=f"done_{i}"):
                if habit["progress"] < habit["goal"]:
                    habit["progress"] += 1
else:
    st.info("No habits yet. Add one from the sidebar!")
