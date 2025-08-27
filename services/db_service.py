import mysql.connector
from config import Config

def get_db_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

# --- User Management Functions ---
def create_user(username, email, hashed_password): # Modified to accept email
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as err:
        print(f"Error creating user: {err}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, username, email, password FROM users WHERE username = %s", (username,)) # Added email to select
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching user by username: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email): # New function to check for existing email
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, username, email, password FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching user by email: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# --- Chat Session Functions (Modified for User ID) ---
def create_new_chat_session_for_user(user_id, title="New Chat"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s)", (user_id, title,))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating new chat session for user {user_id}: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def save_message(session_id, sender, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO chat_messages (session_id, sender, content) VALUES (%s, %s, %s)",
            (session_id, sender, content)
        )
        conn.commit()
    except Exception as e:
        print(f"Error saving message: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_chat_sessions_for_user(user_id): # New function to get user-specific sessions
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, title, created_at FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching chat sessions for user {user_id}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Keep get_chat_sessions for potential admin use, or remove if not needed
def get_chat_sessions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, title, created_at FROM chat_sessions ORDER BY created_at DESC")
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching all chat sessions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_messages_for_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT sender, content, timestamp FROM chat_messages WHERE session_id = %s ORDER BY timestamp ASC",
            (session_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching messages for session {session_id}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def delete_chat_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting chat session {session_id}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_session_title(session_id, new_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE chat_sessions SET title = %s WHERE id = %s", (new_title, session_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating session title {session_id}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


