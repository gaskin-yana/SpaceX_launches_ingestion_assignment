import json
import os
import requests
import psycopg2
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingestion.log'),
        logging.StreamHandler(sys.stdout)  # <== Add this!
    ]
)
# Load environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "spacex")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

API_URL = "https://api.spacexdata.com/v4/launches/latest"

def fetch_latest_launch():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        logging.info("Successfully fetched latest launch data from SpaceX API.")
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching launch data: {e}")
        return None


def validate_launch_data(launch_data, required_fields=['id']):
    """
    Validates critical fields in the launch data.
    - required_fields: list with critical fields
    Returns True if data is valid, False otherwise.
    """

    for field in required_fields:
        if field not in launch_data or not launch_data[field]:
            error_message = f"❌ Missing or empty required field: {field}"
            print(error_message)               # Show in console
            logging.error(error_message)        # Also log to file
            return False
    return True


def insert_into_postgres(launch_data):
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()

        # Ensure the raw_launches table exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_launches (
            id TEXT PRIMARY KEY,
            raw_data JSONB
        );
        """)

        cursor.execute("""
            INSERT INTO raw_launches (id, raw_data)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (
            launch_data["id"],
            json.dumps(launch_data)
        ))
        try:
            inserted_id = cursor.fetchone()
        except:
            inserted_id = None

        if inserted_id:
            logging.info(f"Launch {inserted_id[0]} inserted into database.")
            success_status = True
        else:
            logging.info(f"Launch {launch_data['id']} already exists in {POSTGRES_DB} database.")
            success_status = False

        conn.commit()

    except psycopg2.Error as db_error:
        logging.error(f"❌ Database error: {db_error}")
        success_status = False

    except Exception as general_error:
        logging.error(f"❌ Unexpected error: {general_error}")
        success_status = False

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as close_error:
            logging.warning(f"Warning while closing DB connection: {close_error}")

        return success_status

def main():
    launch_data = fetch_latest_launch()
    if launch_data and validate_launch_data(launch_data):
        success_status = insert_into_postgres(launch_data)
        if success_status:
            logging.info("Ingestion part is finished successfully.")

        else:
            logging.warning("Launch data invalid or fetch failed. Skipping ingestion.")

if __name__ == "__main__":
    main()
