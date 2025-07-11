# Commute Tracker

A Python application that tracks public transit commute times between two locations using the Transit API and stores the results in Google BigQuery. Designed to run as a Cloud Run Job on Google Cloud Platform.

## Features

- Fetches estimated public transit durations between two configurable locations.
- Stores commute durations and metadata in a BigQuery table.
- Designed for scheduled or on-demand execution in a containerized environment.

## Requirements

- Python 3.11+
- Google Cloud Project with BigQuery enabled
- Transit API access token

## Setup

1. **Clone the repository**

2. **Configure environment variables**

   The following environment variables must be set (see `.github/workflows/deploy.yml` for deployment example):

   - `API_TOKEN` (Transit API token)
   - `LOCATION1_LAT`, `LOCATION1_LON` (Latitude/Longitude for location 1)
   - `LOCATION2_LAT`, `LOCATION2_LON` (Latitude/Longitude for location 2)
   - `TIMEZONE` (e.g., `America/Toronto`)
   - `PROJECT_ID` (Google Cloud project ID)

3. **Install dependencies**

   ```sh
   pip install -r requirements.txt
   ```

4. **Run locally**

   ```sh
   python commute-tracker/main.py
   ```

## Deployment

This project is designed to be deployed as a Cloud Run Job. See [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) for an example GitHub Actions workflow that builds and deploys the container.

### Build and Run with Docker

```sh
docker build -t commute-tracker .
docker run --env-file .env commute-tracker
```

## BigQuery Table Schema

The application writes commute data to a table named `transit_data.commute_times` in your GCP project. The schema includes:

- `direction` (STRING)
- `duration_sec` (FLOAT)
- `leave_time` (TIMESTAMP)
- `fetched_at` (TIMESTAMP)

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.