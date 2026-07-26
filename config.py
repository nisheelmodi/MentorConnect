import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# MentorConnect Database Configuration
# ==========================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "mentorconnect"),
    "port": int(os.getenv("DB_PORT", 3306))
}


# ==========================================
# Create Database Connection
# ==========================================

def get_db_connection():
    """
    Creates and returns a MySQL database connection.
    Returns None if connection fails.
    """

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            print("[INFO] Database Connected Successfully.")
            return connection

    except Error as e:
        print(f"[DATABASE ERROR] {e}")

    return None


# ==========================================
# Close Database Connection
# ==========================================

def close_connection(connection):
    """
    Safely closes the database connection.
    """

    try:
        if connection and connection.is_connected():
            connection.close()
            print("[INFO] Database Connection Closed.")

    except Error as e:
        print(f"[CLOSE ERROR] {e}")