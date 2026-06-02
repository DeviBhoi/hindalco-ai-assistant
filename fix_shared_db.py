import sqlite3

conn = sqlite3.connect("shared_data.db")
cursor = conn.cursor()

cursor.execute(
    "ALTER TABLE queries ADD COLUMN created_date TEXT"
)

conn.commit()
conn.close()

print("created_date column added")