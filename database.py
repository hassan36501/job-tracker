
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Akram@12345",
            database="job_tracker",
            port=3306
        )
        return connection

    except Error as e:
        print("Database connection error:", e)
        return None
