from dataclasses import dataclass
import os
import pytz
import requests
import time
import logging
from datetime import datetime
from google.cloud import bigquery


# Transit API configuration
API_TOKEN = os.getenv("TRANSIT_API_TOKEN")
API_URL = "https://api.transitapp.com/v3"
ESTIMATE_DURATION_ENDPOINT = f"{API_URL}/public/estimate_plan_duration"

# Location coordinates and timezone
LOCATION1_LAT = os.getenv("LOCATION1_LAT")
LOCATION1_LON = os.getenv("LOCATION1_LON")
LOCATION2_LAT = os.getenv("LOCATION2_LAT")
LOCATION2_LON = os.getenv("LOCATION2_LON")
TZ = os.getenv("TZ", "America/Toronto")

# Google Cloud BigQuery configuration
PROJECT_ID = os.getenv("PROJECT_ID")
BQ_TABLE = f"{PROJECT_ID}.transit_data.commute_times"
client = bigquery.Client(project=PROJECT_ID)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

@dataclass
class Trip:
    from_lat: float
    from_lon: float
    to_lat: float
    to_lon: float
    departure_time: float
    duration: float = None
    transport_type: str = None

    def set_trip_duration(self) -> None:
        url = ESTIMATE_DURATION_ENDPOINT
        headers = {
            "Authorization": f"Bearer {API_TOKEN}"
        }
        params = {
            "from_lat": self.from_lat,
            "from_lon": self.from_lon,
            "to_lat": self.to_lat,
            "to_lon": self.to_lon,
            "leave_time": int(self.departure_time.timestamp()),
            "mode": "transit"
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Error: {response.status_code} - {response.text}")
            return None

        data = response.json()

        self.duration = data.get("duration")
        self.transport_type = data.get("type")


def store_duration(direction, duration, departure_time):
    table = BQ_TABLE
    row = {
        "direction": direction,
        "duration_sec": duration,
        "leave_time": departure_time.isoformat(),
        "fetched_at": get_current_time(),
    }
    client.insert_rows_json(table, [row])


def get_current_time() -> float:
    """
    Get the current time in the specified timezone.
    
    Returns:
        float: Current time in Unix timestamp format.
    """
    return datetime.now(pytz.timezone(TZ)).timestamp()


def main():
    now = get_current_time()

    # LOCATION1 ➜ LOCATION2
    trip1 = Trip(
        from_lat=float(LOCATION1_LAT),
        from_lon=float(LOCATION1_LON),
        to_lat=float(LOCATION2_LAT),
        to_lon=float(LOCATION2_LON),
        departure_time=now
    )

    trip1.set_trip_duration()

    if trip1.duration:
        store_duration("location1_to_location2", trip1.duration, now)

    # LOCATION2 ➜ LOCATION1
    trip2 = Trip(
        from_lat=float(LOCATION2_LAT),
        from_lon=float(LOCATION2_LON),
        to_lat=float(LOCATION1_LAT),
        to_lon=float(LOCATION1_LON),
        departure_time=now
    )

    trip2.set_trip_duration()
    
    if trip2.duration:
        store_duration("location2_to_location1", trip2.duration, now)


if __name__ == "__main__":
    main()
