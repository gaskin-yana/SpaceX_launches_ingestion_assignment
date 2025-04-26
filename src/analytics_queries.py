import psycopg2
import logging
import os

# Load environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "spacex")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

def run_analytics_queries():
    """
    Runs analytics queries and logs their outputs.
    """
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()

        # 1. Launch Performance Over Time
        query_1 = """
        WITH launches_per_year AS (
            SELECT
                EXTRACT(YEAR FROM (raw_data->>'date_utc')::TIMESTAMP) AS launch_year,
                COUNT(*) AS total_launches,
                COUNT(*) FILTER (WHERE (raw_data->>'success')::BOOLEAN IS TRUE) AS successful_launches
            FROM raw_launches
            GROUP BY launch_year
        )
        SELECT
            launch_year,
            successful_launches,
            total_launches,
            ROUND((successful_launches::DECIMAL / total_launches) * 100, 2) AS success_rate_percentage
        FROM launches_per_year
        ORDER BY launch_year;
        """

        # 2. Top 5 Payload Masses
        query_2 = """
        SELECT
            id,
            raw_data->>'name' AS mission_name,
            (
                SELECT SUM((payload->>'mass_kg')::FLOAT)
                FROM jsonb_array_elements(raw_data->'payloads') AS payload(payload)
                WHERE (payload->>'mass_kg') IS NOT NULL
            ) AS total_payload_mass_kg
        FROM raw_launches
        ORDER BY total_payload_mass_kg DESC
        LIMIT 5;
        """

        # 3. Launch Delay Breakdown
        query_3 = """
        WITH parsed AS (
            SELECT
                EXTRACT(YEAR FROM (raw_data->>'date_utc')::TIMESTAMP) AS launch_year,
                (EXTRACT(EPOCH FROM (now() - (raw_data->>'date_utc')::TIMESTAMP)) / 3600) AS delay_hours
            FROM raw_launches
        )
        SELECT
            launch_year,
            ROUND(AVG(delay_hours), 2) AS average_delay_hours,
            ROUND(MAX(delay_hours), 2) AS max_delay_hours
        FROM parsed
        GROUP BY launch_year
        ORDER BY launch_year;
        """

        # 4. Launch Site Utilization
        query_4 = """
        SELECT
            raw_data->'launchpad' AS launch_site_id,
            COUNT(*) AS total_launches,
            ROUND(AVG(
                (
                    SELECT SUM((payload->>'mass_kg')::FLOAT)
                    FROM jsonb_array_elements(raw_data->'payloads') AS payload(payload)
                    WHERE (payload->>'mass_kg') IS NOT NULL
                )
            ), 2) AS average_payload_mass_kg
        FROM raw_launches
        GROUP BY launch_site_id
        ORDER BY total_launches DESC;
        """

        queries = [
            ("Launch Performance Over Time", query_1),
            ("Top 5 Payload Masses", query_2),
            ("Launch Delay Breakdown", query_3),
            ("Launch Site Utilization", query_4)
        ]

        for title, query in queries:
            logging.info(f"Running Analytics: {title}")
            print(f"\n=== {title} ===")
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            # Display results nicely
            print("\t".join(columns))
            for row in results:
                print("\t".join([str(col) for col in row]))

            logging.info(f"Completed analytics: {title}")

        conn.commit()

    except psycopg2.Error as db_error:
        logging.error(f"Database error while running analytics: {db_error}")

    except Exception as general_error:
        logging.error(f"Unexpected error while running analytics: {general_error}")

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as close_error:
            logging.warning(f"Warning while closing DB connection after analytics: {close_error}")
