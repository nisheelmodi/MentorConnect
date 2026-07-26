import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# MentorConnect Database Configuration
# ==========================================

def _get_bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DB_CONFIG = {
    "host": os.getenv("DB_HOST") or os.getenv("MYSQLHOST") or "localhost",
    "user": os.getenv("DB_USER") or os.getenv("MYSQLUSER") or "root",
    "password": os.getenv("DB_PASSWORD") if os.getenv("DB_PASSWORD") is not None else (os.getenv("MYSQLPASSWORD") or ""),
    "database": os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE") or "mentorconnect",
    "port": int(os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or "3306"),
}

if _get_bool_env("DB_SSL_DISABLED", False):
    DB_CONFIG["ssl_disabled"] = True
elif os.getenv("DB_SSL_CA"):
    DB_CONFIG["ssl"] = {"ca": os.getenv("DB_SSL_CA")}


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