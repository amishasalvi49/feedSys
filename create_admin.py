from werkzeug.security import generate_password_hash
from db_config import get_db_connection
import mysql.connector

connection = None
cursor = None

try:
    connection = get_db_connection()
    cursor = connection.cursor()

    password_hash = generate_password_hash("director123")

    cursor.execute(
        """INSERT INTO users
        (full_name, email, password_hash, role, department_id)
        VALUES (%s, %s, %s, %s, %s)""",
        ("Director Admin", "director@college.com", password_hash, "director", None)
    )

    connection.commit()

    print("SUCCESS: Director account created successfully")

except mysql.connector.Error as error:
    print("MYSQL ERROR:", error)

except Exception as error:
    print("PYTHON ERROR:", error)

finally:
    if cursor:
        cursor.close()
    if connection:
        connection.close()