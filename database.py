import sqlite3

conn = sqlite3.connect("chatbot.db")

cursor = conn.cursor()

# ===== RESPONSE TABLE =====

cursor.execute("""

CREATE TABLE IF NOT EXISTS responses (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    query TEXT NOT NULL,

    response TEXT NOT NULL
)

""")

# ===== CHAT LOG TABLE =====

cursor.execute("""

CREATE TABLE IF NOT EXISTS chat_logs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT,

    employee_id TEXT,

    department TEXT,

    user_query TEXT,

    bot_response TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

""")

conn.commit()

conn.close()

print("Database Ready")