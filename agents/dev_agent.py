from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm_dev as llm
from tools.file_ops import write_file
from tools.logger import log_task

def dev_agent(state: ProjectState) -> ProjectState:
    task_index = state["current_task_index"]
    current_task = state["wbs_tasks"][task_index]
    qa_feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)

    print(f"\n🟢 Dev Agent: Working on Task {task_index + 1}/{len(state['wbs_tasks'])}")
    print(f"   Task: {current_task}")

    feedback_section = ""
    if qa_feedback:
        feedback_section = f"""
The QA Agent reviewed your previous code and found these issues:
{qa_feedback}

Fix ALL issues before resubmitting.
"""

    prompt = f"""
You are a Senior Python Developer. Write a complete, fully functional app.py.

Project Architecture:
{state['architecture_schema']}

Current Task:
{current_task}

{feedback_section}

═══════════════════════════════════════════
STRICT RULES — violating any of these will cause the app to crash
═══════════════════════════════════════════

DATABASE RULES:
- Use ONLY sqlite3 (built-in). No SQLAlchemy, no ORM.
- Define ALL tables in a single create_tables(conn) function
- NEVER reference a column in INSERT/SELECT that is not in the CREATE TABLE statement
- Only use these columns for users: id, username, password, role, created_at, updated_at
- Only use these columns for tasks: id, title, description, due_date, status, assigned_to, created_at, updated_at
- status column default value is 'Pending'
- Hash passwords with hashlib.sha256(password.encode()).hexdigest()
- Users table MUST have UNIQUE constraint on username:
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )

CREATE TASK RULES:
- create_task() function MUST match EXACTLY the columns in the Tasks table
- CORRECT create_task pattern:
    def create_task(conn, title, description, due_date, assigned_to):
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            "INSERT INTO Tasks (title, description, due_date, status, assigned_to, created_at, updated_at) VALUES (?, ?, ?, 'Pending', ?, ?, ?)",
            (title, description, str(due_date), assigned_to, now, now)
        )
        conn.commit()
        return True, "Task created successfully!"
- CORRECT page_create_task pattern:
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
- NEVER pass a column that doesn't exist in the CREATE TABLE statement
- ALWAYS convert due_date to string with str(due_date) before inserting
- ALWAYS return (True, "message") or (False, "error") from create_task()
- NEVER call st.rerun() after creating a task — just show success message

REGISTER FORM RULES:
- The register() function MUST return a tuple (True, "message") or (False, "error"):
    def register(conn, username, password, role):
        try:
            c = conn.cursor()
            hashed = hashlib.sha256(password.encode()).hexdigest()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO Users (username, password, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                      (username, hashed, role, now, now))
            conn.commit()
            return True, "Registration successful!"
        except sqlite3.IntegrityError:
            return False, "Username already exists."
- NEVER call st.rerun() after registration — just show the success/error message
- CORRECT page_register pattern:
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

LOGIN FORM RULES:
- CORRECT page_login pattern:
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
                    st.success(f"Welcome, {{user[1]}}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

SESSION STATE RULES:
- ALWAYS initialize session state with this exact pattern at the top of main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
- NEVER use this pattern (it resets state on every rerun):
    st.session_state.x = value if "x" not in st.session_state else st.session_state.x

NAVIGATION RULES:
- ALWAYS use st.sidebar.selectbox() for navigation, NEVER st.sidebar.button()
- Before login show ONLY: ["Login", "Register"]
- After login show ONLY: ["View Tasks", "Create Task", "Update Task", "Delete Task", "Reports", "Logout"]

FORM RULES:
- ALWAYS place ALL st.text_input() and st.selectbox() BEFORE the st.button()
- NEVER place st.text_input() inside an if st.button(): block
- Every st.text_input(), st.selectbox(), st.date_input() MUST have a unique key= parameter
- Every st.button() MUST have a unique key= parameter
- Without unique key= parameters, Streamlit resets widget state on every rerun

UPDATE TASK FORM RULES:
- CORRECT page_update_task pattern:
    def page_update_task(conn):
        st.title("Update Task")
        tasks = get_tasks(conn)
        if not tasks:
            st.info("No tasks available to update.")
            return
        task_options = {{f"#{{t[0]}} — {{t[1]}}": t[0] for t in tasks}}
        selected = st.selectbox("Select Task", list(task_options.keys()), key="update_select")
        task_id = task_options[selected]
        task = get_task(conn, task_id)
        if task:
            title = st.text_input("Title", value=task[1], key=f"update_title_{{task_id}}")
            description = st.text_area("Description", value=task[2], key=f"update_desc_{{task_id}}")
            due_date = st.text_input("Due Date (YYYY-MM-DD)", value=task[3], key=f"update_due_{{task_id}}")
            status = st.selectbox("Status", ["Pending", "In Progress", "Completed"],
                                  index=["Pending", "In Progress", "Completed"].index(task[4])
                                  if task[4] in ["Pending", "In Progress", "Completed"] else 0,
                                  key=f"update_status_{{task_id}}")
            if st.button("Save Changes", key=f"btn_update_{{task_id}}"):
                update_task(conn, task_id, title, description, due_date, status)
                st.success("Task updated successfully!")
- Every widget key MUST include task_id to make it unique per task
- Without task_id in the key, switching tasks in dropdown won't update the form fields

DELETE CONFIRMATION RULES:
- NEVER nest st.button() inside another if st.button(): block
- CORRECT page_delete_task pattern:
    def page_delete_task(conn):
        st.title("Delete Task")
        tasks = get_tasks(conn)
        if not tasks:
            st.info("No tasks available to delete.")
            return
        if "confirm_delete" not in st.session_state:
            st.session_state.confirm_delete = False
        task_options = {{f"#{{t[0]}} — {{t[1]}}": t[0] for t in tasks}}
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

REPORTS PAGE RULES:
- Must show: total task count, completed count, pending count, overdue count, completion rate %
- Use st.metric() for the counts
- due_date is stored as a STRING in SQLite, so ALWAYS convert before comparing:
    today = datetime.today().strftime("%Y-%m-%d")
    overdue_tasks = len([t for t in tasks if t[3] and t[3] < today and t[4] != "Completed"])
- NEVER compare a string date with datetime.date.today() directly
- ALWAYS use st.progress() NOT st.progress_bar() — st.progress_bar() does not exist
- st.progress() accepts a float between 0.0 and 1.0 ONLY
- CORRECT: st.progress(completion_rate / 100)
- WRONG: st.progress(completion_rate) — will crash if rate > 1.0
- WRONG: st.progress_bar(completion_rate) — function does not exist

GENERAL RULES:
- Write the COMPLETE file every time
- All code in a single app.py file
- No placeholder comments like "# add code here"
- Use st.rerun() after login, logout, delete
- Use st.date_input() for due dates, not st.text_input()
- Task selection in Update/Delete must use st.selectbox() with task titles, never manual ID entry
- Always call main() at the bottom with: if __name__ == "__main__": main()

Respond with ONLY raw Python code. No explanation. No markdown fences.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    code = response.content.strip()

    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:])
    if code.endswith("```"):
        code = "\n".join(code.split("\n")[:-1])
    code = code.strip()

    usage = getattr(response, 'response_metadata', {}).get('token_usage', {})

    log_task(
        task_index=task_index,
        task_name=current_task,
        iteration=iteration + 1,
        status="dev_written",
        issues=[]
    )

    print(f"✅ Code written to generated_workspace/app.py ({len(code)} chars)")
    print(f"   🪙 Tokens — prompt: {usage.get('prompt_tokens', '?')}, completion: {usage.get('completion_tokens', '?')}, total: {usage.get('total_tokens', '?')}")

    write_file("app.py", code)

    return {
        **state,
        "code_files": {"app.py": code},
        "qa_feedback": "",
        "qa_passed": False,
        "iteration_count": iteration + 1
    }