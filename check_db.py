# save as check_db.py in Agentic_CRUD folder
import sqlite3

conn = sqlite3.connect("tasks.db")
c = conn.cursor()

print("=== Tables ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(c.fetchall())

print("\n=== Users ===")
try:
    c.execute("SELECT * FROM Users")
    users = c.fetchall()
    if users:
        for u in users:
            print(u)
    else:
        print("No users found")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Tasks ===")
try:
    c.execute("SELECT * FROM Tasks")
    tasks = c.fetchall()
    if tasks:
        for t in tasks:
            print(t)
    else:
        print("No tasks found")
except Exception as e:
    print(f"Error: {e}")

conn.close()