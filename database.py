import sqlite3

def save_history(username, prediction, score, skills):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO history (username, prediction, score, skills)
        VALUES (?, ?, ?, ?)
    """, (username, prediction, score, ",".join(skills)))

    conn.commit()
    conn.close()


def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            prediction TEXT,
            score REAL,
            skills TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("Database setup complete 🚀")


if __name__ == "__main__":
    init_db()