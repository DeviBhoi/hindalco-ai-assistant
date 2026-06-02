import sqlite3

conn = sqlite3.connect("shared_data.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    query TEXT,
    created_date TEXT,
    status TEXT DEFAULT 'Pending'
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")