import mysql.connector
from config import DB_CONFIG
import os

def setup_db():
    try:
        # Connect without selecting the database initially
        config_no_db = DB_CONFIG.copy()
        if "database" in config_no_db:
            del config_no_db["database"]
            
        conn = mysql.connector.connect(**config_no_db)
        cursor = conn.cursor()
        
        sql_file_path = os.path.join("database", "mentorconnect.sql")
        
        if not os.path.exists(sql_file_path):
            print(f"Error: {sql_file_path} not found.")
            return

        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
            
        # Execute the entire setup script
        print("Executing database setup script...")
        cursor.execute(sql_script)
        while cursor.nextset():
            pass
            
        conn.commit()
        print("Database 'mentorconnect' and all tables setup successfully!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error setting up database: {e}")

if __name__ == "__main__":
    setup_db()
