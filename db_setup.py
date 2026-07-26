import mysql.connector
from config import DB_CONFIG
import os

def setup_db():
    conn = None
    try:
        # First, try connecting with the database specified in DB_CONFIG
        print(f"Connecting to database '{DB_CONFIG.get('database')}'...")
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Successfully connected directly to the database.")
    except Exception as e:
        print(f"Could not connect directly to database '{DB_CONFIG.get('database')}' due to: {e}")
        print("Attempting to connect without database to create it...")
        # Fallback: connect without a database and attempt to create it
        config_no_db = DB_CONFIG.copy()
        if "database" in config_no_db:
            del config_no_db["database"]
            
        try:
            conn_temp = mysql.connector.connect(**config_no_db)
            cursor_temp = conn_temp.cursor()
            db_name = DB_CONFIG.get('database', 'mentorconnect')
            cursor_temp.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"Database '{db_name}' created successfully (or already existed).")
            cursor_temp.close()
            conn_temp.close()
            
            # Now reconnect with the database
            conn = mysql.connector.connect(**DB_CONFIG)
            print("Successfully connected to the database after creation.")
        except Exception as err:
            print(f"Failed to create database or reconnect: {err}")
            return

    try:
        cursor = conn.cursor()
        sql_file_path = os.path.join("database", "mentorconnect.sql")
        
        if not os.path.exists(sql_file_path):
            print(f"Error: {sql_file_path} not found.")
            return

        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
            
        # Execute the setup script statement by statement
        print("Executing database setup script statement by statement...")
        statements = sql_script.split(";")
        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue
            
            # Skip database creation or selection statements to use the current connection's database
            if statement.upper().startswith("CREATE DATABASE") or statement.upper().startswith("USE "):
                print(f"Skipping database/use statement: {statement[:50]}...")
                continue
                
            try:
                cursor.execute(statement)
            except Exception as stmt_err:
                print(f"Error executing statement:\n{statement[:100]}...\nError: {stmt_err}")
                raise stmt_err
            
        conn.commit()
        print("Database tables and data setup successfully!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error setting up database: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_db()

