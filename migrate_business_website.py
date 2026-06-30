import sqlite3

try:
    conn = sqlite3.connect("leadforge.db")
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE business_profiles ADD COLUMN website TEXT;")
    conn.commit()
    print("Successfully added website column to business_profiles table!")
except sqlite3.OperationalError as e:
    print(f"Operational warning (possibly column already exists): {e}")
finally:
    conn.close()
