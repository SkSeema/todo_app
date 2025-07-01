# todo_app.py (Final with Profile Fix, Voice Input, Theme Switch, and Category/Priority Bug Fix)
import streamlit as st
import sqlite3
import hashlib
import speech_recognition as sr
import plotly.express as px
from streamlit_calendar import calendar
from datetime import datetime, date

# ------------------- Page Style -------------------
st.set_page_config(layout="centered")

DEFAULT_THEME = "#fef6fb"
BACKGROUND_COLORS = {
    "Light Pink": "#fef6fb",
    "Lavender": "#f3f0ff",
    "Sky Blue": "#e6f7ff",
    "Mixed Pastels": "linear-gradient(to right, #fef6fb, #e6f7ff)"
}

if "theme" not in st.session_state:
    st.session_state.theme = "Light Pink"

bg_color = BACKGROUND_COLORS.get(st.session_state.theme, DEFAULT_THEME)

st.markdown(f"""
    <style>
    body, .stApp {{
        background: {bg_color};
    }}
    .centered {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    .title-text {{
        text-align: center;
        font-size: 2.2em;
        color: #6c5ce7;
    }}
    .task-box {{
        border: 2px solid #dcd6f7;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #fff;
    }}
    .task-controls {{
        display: flex;
        gap: 10px;
        margin-top: 5px;
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------- DB Setup -------------------
conn = sqlite3.connect('todo_users.db', check_same_thread=False, timeout=10)
c = conn.cursor()

def create_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    name TEXT, email TEXT, password TEXT,
                    dob TEXT DEFAULT '',
                    xp INTEGER DEFAULT 0,
                    streak INTEGER DEFAULT 0,
                    last_login TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    email TEXT, task TEXT, category TEXT,
                    priority TEXT, progress INTEGER,
                    status TEXT, date TEXT, duedate TEXT)''')
    conn.commit()

# ------------------- Utility Functions -------------------
def listen_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak now")
        audio = recognizer.listen(source, phrase_time_limit=5)
    try:
        return recognizer.recognize_google(audio)
    except:
        return ""

# ------------------- Task Operations -------------------
def get_tasks(email):
    c.execute('SELECT rowid, task, category, priority, progress, status, date, duedate FROM tasks WHERE email=?', (email,))
    return c.fetchall()

def add_task(email, task, category, priority, progress, duedate):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO tasks (email, task, category, priority, progress, status, date, duedate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
              (email, task, category, priority, progress, 'Pending', now, duedate))
    conn.commit()

def update_task(task_id, task, category, priority, progress, duedate):
    c.execute('UPDATE tasks SET task=?, category=?, priority=?, progress=?, duedate=? WHERE rowid=?',
              (task, category, priority, progress, duedate, task_id))
    conn.commit()

def delete_task(task_id):
    c.execute('DELETE FROM tasks WHERE rowid=?', (task_id,))
    conn.commit()

def mark_complete(task_id):
    c.execute('UPDATE tasks SET status="Completed" WHERE rowid=?', (task_id,))
    conn.commit()

# ------------------- Main -------------------
def main():
    create_tables()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        dashboard(st.session_state.user_name, st.session_state.user_email)
        return

    st.markdown('<div class="centered"><div class="title-text">📝 To-Do List</div>', unsafe_allow_html=True)
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Register":
        st.subheader("Register")
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        confirm = st.text_input("Confirm Password", type='password')

        if st.button("Register"):
            if password == confirm:
                hashed = hashlib.sha256(password.encode()).hexdigest()
                c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed))
                conn.commit()
                st.success("Registered Successfully! Please Login")
            else:
                st.warning("Passwords do not match")

    elif choice == "Login":
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            hashed = hashlib.sha256(password.encode()).hexdigest()
            c.execute('SELECT * FROM users WHERE email=? AND password=?', (email, hashed))
            user = c.fetchone()
            if user:
                st.session_state.logged_in = True
                st.session_state.user_name = user[0]
                st.session_state.user_email = user[1]
                st.session_state.page = "add"
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------- Dashboard -------------------
def dashboard(name, email):
    st.sidebar.header("☰ Settings")
    nav = st.sidebar.radio("Navigate", ["Tasks", "Calendar View", "Profile", "Theme", "Logout"])

    if nav == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    st.markdown(f"<h2 style='text-align:center;'>📝 To-Do List</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align:center;'>Welcome, {name} 👋</h4>", unsafe_allow_html=True)

    if nav == "Calendar View":
        st.subheader("📅 Your Calendar")
        tasks = get_tasks(email)
        events = []
        for t in tasks:
            color = "#2ecc71" if t[5] == "Completed" else "#e74c3c"
            events.append({"title": t[1], "start": t[7], "end": t[7], "color": color})
        calendar(events=events, options={"editable": False})

    elif nav == "Profile":
        st.subheader("👤 Profile Info")
        c.execute('SELECT name, dob FROM users WHERE email=?', (email,))
        data = c.fetchone()
        name_val = st.text_input("Name", value=data[0] if data else "")
        dob_val = st.date_input("Date of Birth", value=datetime.strptime(data[1], "%Y-%m-%d").date() if data and data[1] else date(2000, 1, 1), min_value=date(2000, 1, 1))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Profile"):
                c.execute('UPDATE users SET name=?, dob=? WHERE email=?', (name_val, str(dob_val), email))
                conn.commit()
                st.success("Profile saved successfully")
        with col2:
            if st.button("🔁 Update Profile"):
                c.execute('UPDATE users SET name=?, dob=? WHERE email=?', (name_val, str(dob_val), email))
                conn.commit()
                st.success("Profile updated successfully")

    elif nav == "Theme":
        st.subheader("🎨 Choose Theme")
        theme = st.selectbox("Select Theme", list(BACKGROUND_COLORS.keys()))
        if st.button("Apply Theme"):
            st.session_state.theme = theme
            st.rerun()

    else:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("➕ Add New Task"):
                st.session_state.page = "add"
        with col2:
            if st.button("📋 Your Tasks"):
                st.session_state.page = "list"
        with col3:
            if st.button("📊 Analytics"):
                st.session_state.page = "analytics"

        page = st.session_state.get("page", "add")

        if page == "add":
            st.subheader("➕ Add Task")
            col1, col2 = st.columns([2, 1])
            if "spoken_text" not in st.session_state:
                st.session_state.spoken_text = ""
            with col1:
                task = st.text_input("Task", value=st.session_state.spoken_text, key="task_input")
            with col2:
                if st.button("🎤 Speak"):
                    spoken = listen_voice()
                    st.session_state.spoken_text = spoken
                    st.rerun()
            category = st.selectbox("Category", ["📘 Study", "🛒 Shopping/Grocery", "🏡 Personal/Other"])
            priority = st.selectbox("Priority", ["🔴 High", "🟡 Medium", "🟢 Low"])
            progress = st.slider("Progress", 0, 100, 0)
            duedate = st.date_input("Due Date")
            if st.button("Add Task") and st.session_state.spoken_text:
                add_task(email, st.session_state.spoken_text, category, priority, progress, str(duedate))
                st.success("Task Added!")
                st.session_state.spoken_text = ""
                st.rerun()

        elif page == "list":
            st.subheader("📋 Your Tasks")
            tasks = get_tasks(email)
            for t in tasks:
                task_id, task, category, priority, progress, status, date_created, duedate = t
                with st.expander(f"{task} ({status})"):
                    new_task = st.text_input("Edit Task", value=task, key=f"etask{task_id}")
                    categories = ["📘 Study", "🛒 Shopping/Grocery", "🏡 Personal/Other"]
                    priorities = ["🔴 High", "🟡 Medium", "🟢 Low"]
                    new_category = st.selectbox("Edit Category", categories, index=categories.index(category) if category in categories else 0, key=f"ecat{task_id}")
                    new_priority = st.selectbox("Edit Priority", priorities, index=priorities.index(priority) if priority in priorities else 0, key=f"epri{task_id}")
                    new_progress = st.slider("Progress", 0, 100, value=progress, key=f"eprog{task_id}")
                    new_duedate = st.date_input("Due Date", value=datetime.strptime(duedate, '%Y-%m-%d').date(), key=f"edate{task_id}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Complete", key=f"c{task_id}"):
                            mark_complete(task_id)
                            st.rerun()
                    with col2:
                        if st.button("✏ Save", key=f"s{task_id}"):
                            update_task(task_id, new_task, new_category, new_priority, new_progress, str(new_duedate))
                            st.rerun()
                    with col3:
                        if st.button("🗑 Delete", key=f"d{task_id}"):
                            delete_task(task_id)
                            st.rerun()

        elif page == "analytics":
            st.subheader("📊 Analytics")
            tasks = get_tasks(email)
            total = len(tasks)
            done = sum(1 for t in tasks if t[5] == "Completed")
            pending = total - done
            if total:
                df = {"Status": ["Completed", "Pending"], "Count": [done, pending]}
                fig = px.bar(df, x="Status", y="Count", color="Status", title="Task Completion")
                st.plotly_chart(fig)

# ------------------- Entry -------------------
if __name__ == '__main__':
    main()
