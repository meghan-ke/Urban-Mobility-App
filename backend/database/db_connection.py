import mysql.connector
from mysql.connector import Error
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_connection():
    """
    Create a connection to the MySQL database using credentials from config.py
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        if connection.is_connected():
            print(f"Successfully connected to MySQL database: {DB_NAME}")
            return connection
            
    except Error as error:
        raise RuntimeError(f"MySQL connection failed: {error}")

def close_connection(connection):
    """
    Close the database connection
    """
    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection closed")
