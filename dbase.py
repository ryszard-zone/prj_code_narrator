import sqlite3

def create_connection(db_name="historia.db"):
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(db_name)
    return conn

def create_table(conn):
    """Create the 'historia' table if it doesn't exist."""
    with conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS historia (
            id INTEGER PRIMARY KEY,
            code_input TEXT NOT NULL,
            description TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

def insert_history(conn, code_input, description):
    """Insert a new record into the 'historia' table."""
    with conn:
        conn.execute('''
        INSERT INTO historia (code_input, description) 
        VALUES (?, ?)
        ''', (code_input, description))

def fetch_history(conn):
    """Fetch all records from the 'historia' table."""
    cursor = conn.cursor()
    cursor.execute('SELECT id, code_input, description, timestamp FROM historia ORDER BY timestamp DESC')
    return cursor.fetchall()

def trim_history(conn, max_entries=20):
    """Ensure that the 'historia' table has at most `max_entries` rows, keeping the latest ones."""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM historia')
    total_entries = cursor.fetchone()[0]
    if total_entries > max_entries:
        # Calculate how many rows to delete
        rows_to_delete = total_entries - max_entries
        # Delete the oldest entries
        cursor.execute('''
        DELETE FROM historia WHERE id IN (
            SELECT id FROM historia ORDER BY timestamp ASC LIMIT ?
        )
        ''', (rows_to_delete,))
        conn.commit()
