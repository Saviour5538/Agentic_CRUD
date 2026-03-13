import streamlit as st
import sqlite3
import hashlib
import datetime

def create_tables(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS Tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            assigned_to INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS Task_History (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES Tasks (id)
        )
    """)
    conn.commit()

def register(conn, username, password, role):
    try:
        c = conn.cursor()
        hashed = hashlib.sha256(password.encode()).hexdigest()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO Users (username, password, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                  (username, hashed, role, now, now))
        conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."

def login(conn, username, password):
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id, username FROM Users WHERE username = ? AND password = ?", (username, hashed))
    user = c.fetchone()
    return user

def create_task(conn, title, description, due_date, assigned_to):
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO Tasks (title, description, due_date, status, assigned_to, created_at, updated_at) VALUES (?, ?, ?, 'Pending', ?, ?, ?)",
        (title, description, str(due_date), assigned_to, now, now)
    )
    conn.commit()
    return True, "Task created successfully!"

def get_tasks(conn):
    c = conn.cursor()
    c.execute("SELECT id, title, description, due_date, status FROM Tasks")
    tasks = c.fetchall()
    return tasks

def get_task(conn, task_id):
    c = conn.cursor()
    c.execute("SELECT id, title, description, due_date, status FROM Tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    return task

def update_task(conn, task_id, title, description, due_date, status):
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE Tasks SET title = ?, description = ?, due_date = ?, status = ?, updated_at = ? WHERE id = ?",
              (title, description, due_date, status, now, task_id))
    conn.commit()

def delete_task(conn, task_id):
    c = conn.cursor()
    c.execute("DELETE FROM Tasks WHERE id = ?", (task_id,))
    conn.commit()

def page_register(conn):
    st.title("Register")
    username = st.text_input("Username", key="reg_username")
    password = st.text_input("Password", type="password", key="reg_password")
    role = st.selectbox("Role", ["user", "admin"], key="reg_role")
    if st.button("Register", key="btn_register"):
        if not username or not password:
            st.error("All fields are required.")
        else:
            success, msg = register(conn, username, password, role)
            if success:
                st.success("Registration successful! Please go to Login.")
            else:
                st.error(msg)

def page_login(conn):
    st.title("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="btn_login"):
        if not username or not password:
            st.error("Please enter credentials.")
        else:
            user = login(conn, username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]
                st.success(f"Welcome, {user[1]}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

def page_create_task(conn):
    st.title("Create Task")
    title = st.text_input("Title", key="create_title")
    description = st.text_area("Description", key="create_desc")
    due_date = st.date_input("Due Date", key="create_due_date")
    if st.button("Create Task", key="btn_create_task"):
        if not title:
            st.error("Title is required.")
        else:
            ok, msg = create_task(conn, title, description, str(due_date), st.session_state.user_id)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

def page_update_task(conn):
    st.title("Update Task")
    tasks = get_tasks(conn)
    if not tasks:
        st.info("No tasks available to update.")
        return
    task_options = {f"#{t[0]} — {t[1]}": t[0] for t in tasks}
    selected = st.selectbox("Select Task", list(task_options.keys()), key="update_select")
    task_id = task_options[selected]
    task = get_task(conn, task_id)
    if task:
        title = st.text_input("Title", value=task[1], key=f"update_title_{task_id}")
        description = st.text_area("Description", value=task[2], key=f"update_desc_{task_id}")
        due_date = st.date_input("Due Date", value=datetime.datetime.strptime(task[3], "%Y-%m-%d").date(), key=f"update_due_{task_id}")
        status = st.selectbox("Status", ["Pending", "In Progress", "Completed"],
                              index=["Pending", "In Progress", "Completed"].index(task[4])
                              if task[4] in ["Pending", "In Progress", "Completed"] else 0,
                              key=f"update_status_{task_id}")
        if st.button("Save Changes", key=f"btn_update_{task_id}"):
            update_task(conn, task_id, title, description, str(due_date), status)
            st.success("Task updated successfully!")

def page_delete_task(conn):
    st.title("Delete Task")
    tasks = get_tasks(conn)
    if not tasks:
        st.info("No tasks available to delete.")
        return
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
    task_options = {f"#{t[0]} — {t[1]}": t[0] for t in tasks}
    selected = st.selectbox("Select Task", list(task_options.keys()), key="delete_select")
    if st.button("Delete Task", key="btn_delete"):
        st.session_state.confirm_delete = True
    if st.session_state.confirm_delete:
        st.warning("Are you sure you want to delete this task?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete", key="btn_confirm_delete"):
                delete_task(conn, task_options[selected])
                st.session_state.confirm_delete = False
                st.rerun()
        with col2:
            if st.button("Cancel", key="btn_cancel_delete"):
                st.session_state.confirm_delete = False
                st.rerun()

def page_reports(conn):
    st.title("Reports")
    tasks = get_tasks(conn)
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t[4] == "Completed"])
    pending_tasks = len([t for t in tasks if t[4] == "Pending"])
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    overdue_tasks = len([t for t in tasks if t[3] and t[3] < today and t[4] != "Completed"])
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    st.metric("Total Tasks", total_tasks)
    st.metric("Completed Tasks", completed_tasks)
    st.metric("Pending Tasks", pending_tasks)
    st.metric("Overdue Tasks", overdue_tasks)
    st.progress(completion_rate / 100)

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False

    conn = sqlite3.connect("tasks.db")
    create_tables(conn)

    if not st.session_state.logged_in:
        navigation = st.sidebar.selectbox("Navigation", ["Login", "Register"])
        if navigation == "Login":
            page_login(conn)
        elif navigation == "Register":
            page_register(conn)
    else:
        navigation = st.sidebar.selectbox("Navigation", ["View Tasks", "Create Task", "Update Task", "Delete Task", "Reports", "Logout"])
        if navigation == "View Tasks":
            tasks = get_tasks(conn)
            for task in tasks:
                st.write(f"Title: {task[1]}, Description: {task[2]}, Due Date: {task[3]}, Status: {task[4]}")
        elif navigation == "Create Task":
            page_create_task(conn)
        elif navigation == "Update Task":
            page_update_task(conn)
        elif navigation == "Delete Task":
            page_delete_task(conn)
        elif navigation == "Reports":
            page_reports(conn)
        elif navigation == "Logout":
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

if __name__ == "__main__":
    main()