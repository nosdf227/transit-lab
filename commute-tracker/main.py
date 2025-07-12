from dataclasses import dataclass
import os
import pytz
import requests
import logging
from datetime import datetime
from google.cloud import bigquery


# Transit API configuration
API_TOKEN = os.getenv("TRANSIT_API_TOKEN")
API_URL = "https://api.transitapp.com/v3"
ESTIMATE_DURATION_ENDPOINT = f"{API_URL}/public/plan"

# Location coordinates and timezone
LOCATION1_NAME = os.getenv("LOCATION1_NAME", "Location_1")
LOCATION1_LAT = os.getenv("LOCATION1_LAT")
LOCATION1_LON = os.getenv("LOCATION1_LON")
LOCATION2_NAME = os.getenv("LOCATION2_NAME", "Location_2")
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
    start_time: float
    end_time: float
    duration: float = None
    transport_type: str = None
    _raw_trip_data: dict = None

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
            "num_result": 1,
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Error: {response.status_code} - {response.text}")
            return None

        self._raw_trip_data = response.json()["results"][0]

        self.duration = self._raw_trip_data.get("duration")
        self.start_time = self._raw_trip_data.get("start_time")
        self.end_time = self._raw_trip_data.get("end_time")
        self.transport_type = self._raw_trip_data.get("type")
    
    def __str__(self):
        return (f"Trip from ({self.from_lat}, {self.from_lon}) to "
                f"({self.to_lat}, {self.to_lon}) will have a duration of {self.duration} "
                f"seconds and transport type '{self.transport_type}'")


def store_duration(direction: str, duration: float, start_time: float, end_time: float, current_time: float) -> None:
    table = BQ_TABLE
    row = {
        "direction_name": direction,
        "duration_sec": duration,
        "start_time": start_time,
        "end_time": end_time,
        "tmsp": current_time,
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
    )

    trip1.set_trip_duration()

    if trip1.duration:
        logger.info(trip1)
        store_duration(
            direction=f"{LOCATION1_NAME}_to_{LOCATION2_NAME}",
            duration=trip1.duration,
            start_time=trip1.start_time,
            end_time=trip1.end_time,
            current_time=now,
        )

    # LOCATION2 ➜ LOCATION1
    trip2 = Trip(
        from_lat=float(LOCATION2_LAT),
        from_lon=float(LOCATION2_LON),
        to_lat=float(LOCATION1_LAT),
        to_lon=float(LOCATION1_LON),
    )

    trip2.set_trip_duration()

    if trip2.duration:
        logger.info(trip2)
        store_duration(
            direction=f"{LOCATION2_NAME}_to_{LOCATION1_NAME}",
            duration=trip2.duration,
            start_time=trip2.start_time,
            end_time=trip2.end_time,
            current_time=now
        )


if __name__ == "__main__":
    main()
