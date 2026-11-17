
from database import get_db_connection

connection = get_db_connection()

if connection and connection.is_connected():
    print("SUCCESS: Python connected to MySQL!")
    print("Database:", connection.database)
    connection.close()
else:
    print("FAILED: Database connection not working.")
