import sqlite3

# -------------------------
# CREATE USERS TABLE
# -------------------------
def init_auth_db():

    conn = sqlite3.connect(
        "users.db",
        check_same_thread=False,
        timeout=30
    )

    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()

# -------------------------
# REGISTER USER
# -------------------------
def register_user(username, password):

    conn = sqlite3.connect(
        "users.db",
        check_same_thread=False,
        timeout=30
    )

    c = conn.cursor()

    try:

        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()

    except Exception as e:
        print(e)

    finally:
        conn.close()

# -------------------------
# LOGIN USER
# -------------------------
def login_user(username, password):

    conn = sqlite3.connect(
        "users.db",
        check_same_thread=False,
        timeout=30
    )

    c = conn.cursor()

    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = c.fetchone()

    conn.close()

    return user