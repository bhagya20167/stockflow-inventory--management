


import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()


def get_db():
    """Create and return a MySQL database connection."""

    required = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            f"Missing database configuration: {', '.join(missing)}"
        )

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        connection_timeout=5,
    )


if __name__ == "__main__":
    connection = None
    cursor = None

    try:
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        database_name = cursor.fetchone()[0]
        print(f"Successfully connected to: {database_name}")

    except (Error, RuntimeError, ValueError):
        print(
            "Database connection failed. Check your database "
            "configuration and MySQL server."
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()




