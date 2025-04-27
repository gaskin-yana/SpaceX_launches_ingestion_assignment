import json
import os
import random
from datetime import datetime

import requests
import psycopg2
import logging
import sys

from sql.analytics_queries import run_analytics_queries

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
    #TODO add a real launch masses based on payloads ID by fetching data from https://api.spacexdata.com/v4/payloads/{payload_id}
    """
    Using generated data for POC for launch masses and launch start delay.
    (SpaceX API/latest does not provide full mass or delay data by default)
    :return: launch_data dict with simulated data for launch masses and launch start delay
    """
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        logging.info("Successfully fetched latest launch data from SpaceX API.")
        launch_data = response.json()
        launch_data['fetched_at_timestamp'] = datetime.utcnow().isoformat()
        # Inject simulated payload mass
        num_payloads = len(launch_data.get('payloads', []))
        simulated_mass = num_payloads * random.uniform(2000, 6000)  # random per payload
        launch_data["simulated_total_payload_mass_kg"] = round(simulated_mass, 2)

        # Inject simulated delay in minutes (0 to 120 minutes)
        simulated_delay = random.uniform(0, 120)
        launch_data["simulated_delay_minutes"] = round(simulated_delay, 2)

        return launch_data

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
            error_message = f"Missing or empty required field: {field}"
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
            fetched_at_timestamp TIMESTAMP,
            simulated_total_payload_mass_kg INTEGER,
            simulated_delay_minutes INTEGER, 
            raw_data JSONB
        );
        """)

        cursor.execute("""
            INSERT INTO raw_launches (id, raw_data, simulated_total_payload_mass_kg, simulated_delay_minutes, fetched_at_timestamp)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            RETURNING id;
        """, (
            launch_data["id"],
            json.dumps(launch_data),
            launch_data['simulated_total_payload_mass_kg'],
            launch_data['simulated_delay_minutes'],
            launch_data['fetched_at_timestamp']
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
        logging.error(f"Database error: {db_error}")
        success_status = False

    except Exception as general_error:
        logging.error(f"Unexpected error: {general_error}")
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

def create_aggregation_view():
    """
    Creates or refreshes the launch_aggregates_view to calculate metrics from raw_launches table.
    """
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()

        # Drop the view if it exists first!
        cursor.execute("DROP VIEW IF EXISTS launch_aggregates_view;")

        aggregation_view_query = """
                CREATE VIEW launch_aggregates_view AS
                WITH parsed AS (
                    SELECT
                        id,
                        (raw_data->>'success')::BOOLEAN AS success,
                        simulated_total_payload_mass_kg,
                        simulated_delay_minutes
                    FROM raw_launches
                )
                SELECT
                    COUNT(*) AS total_launches,
                    COUNT(*) FILTER (WHERE success IS TRUE) AS total_successful_launches,
                    AVG(simulated_total_payload_mass_kg) AS average_payload_mass,
                    AVG(simulated_delay_minutes) AS average_launch_delay_minutes
                FROM parsed;
                """

        cursor.execute(aggregation_view_query)
        conn.commit()
        logging.info("Aggregation view launch_aggregates_view created successfully.")

    except psycopg2.Error as db_error:
        logging.error(f"Database error while creating aggregation view: {db_error}")

    except Exception as general_error:
        logging.error(f"Unexpected error while creating aggregation view: {general_error}")

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as close_error:
            logging.warning(f"Warning while closing DB connection after creating view: {close_error}")


def main():
    launch_data = fetch_latest_launch()
    if launch_data and validate_launch_data(launch_data):
        success_status = insert_into_postgres(launch_data)
        if success_status:
            logging.info("Ingestion finished successfully.")
        else:
            logging.warning("Launch data already exists. No insertion needed.")
        create_aggregation_view()
        run_analytics_queries()
        sys.exit(0)
    else:
        logging.error("Launch data invalid or fetch failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
