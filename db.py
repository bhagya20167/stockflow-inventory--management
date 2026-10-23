
import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()


def get_db():
    """Create and return a secure MySQL database connection."""

    required = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            f"Missing database configuration: {', '.join(missing)}"
        )

    
    config = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "28790")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "connection_timeout": 10,
        "ssl_disabled": False,
    }


    # Verify the server certificate when a CA certificate path is provided.
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        config["ssl_ca"] = ssl_ca
        config["ssl_verify_cert"] = True
        config["ssl_verify_identity"] = True

    return mysql.connector.connect(**config)


if __name__ == "__main__":
    connection = None
    cursor = None

    try:
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        database_name = cursor.fetchone()[0]
        print(f"Successfully connected to: {database_name}")

    except (Error, RuntimeError, ValueError) as error:
        print(f"Database connection failed: {error}")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()





