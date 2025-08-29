# Scraper Control Panel

This is a Flask-based web application that provides a user interface for running various web scrapers and viewing the collected data.

## Features

- **Web-based UI**: A simple and clean interface to manage and run scrapers.
- **Multiple Scrapers**: Supports scraping from:
    - Google Maps API
    - Headless Google Maps
    - Facebook
    - Wikipedia (Test)
- **Live Log Streaming**: View the real-time output of scrapers as they run.
- **Persistent Storage**: Scraped data is saved to a PostgreSQL database.
- **Results Viewer**: A dedicated page to view all scraped data with filtering options.
- **Data Filtering**: Filter results by search term, business name/title, address, and data source.
- **XLSX Export**: Download the filtered results as an XLSX file.
- **Database Purge**: An admin feature to easily clear all scraped data.

## Setup and Installation

### Prerequisites

- Python 3.x
- PostgreSQL Server

### 1. Install Dependencies

Navigate to the `control_panel_server` directory and install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Configure the Application

Open `app.py` and edit the configuration section:

- **Google Maps API Key**:
  Replace `"YOUR_API_KEY_HERE"` with your actual Google Maps API key.

  ```python
  # PASTE YOUR GOOGLE MAPS API KEY HERE
  API_KEY = "YOUR_API_KEY_HERE"
  ```

- **PostgreSQL Database**:
  Update the `DB_CONFIG` dictionary with your PostgreSQL connection details.

  ```python
  # PostgreSQL Configuration
  DB_CONFIG = {
      "host": "127.0.0.1",
      "port": "5432",
      "database": "scrape_details",
      "user": "scrape_bot",
      "password": "your_password"
  }
  ```

### 3. Set up the PostgreSQL Database

You need to create the database and user in PostgreSQL that you specified in `DB_CONFIG`.

Example using `psql`:

```sql
-- Create a new user (role)
CREATE ROLE scrape_bot WITH LOGIN PASSWORD 'your_password';

-- Create the database
CREATE DATABASE scrape_details;

-- Grant all privileges on the new database to the new user
GRANT ALL PRIVILEGES ON DATABASE scrape_details TO scrape_bot;
```

The application will automatically create the necessary tables when it starts for the first time.

## How to Run the Application

1.  Make sure your PostgreSQL server is running.
2.  Navigate to the `control_panel_server` directory.
3.  Run the Flask application:

    ```bash
    python app.py
    ```

4.  Open your web browser and go to `http://127.0.0.1:8005`.

## How to Use

1.  **Select a Scraper**: From the main page, choose a scraper from the dropdown menu.
2.  **Enter Inputs**: Provide the required inputs for the selected scraper (e.g., a search query for Google Maps, a URL for Facebook).
3.  **Run the Scraper**: Click the "Scrape" button. The live logs will appear in the box below, showing the scraper's progress.
4.  **View Results**: Click on the "View Results" tab to see the data that has been collected.
5.  **Filter Data**: Use the filter inputs at the top of the results page to search and filter the data. Click "Apply Filters" to see the changes.
6.  **Download Data**: Click the "Download XLSX" button. A popup will appear asking for your email. After providing it, the download of an XLSX file containing the currently filtered results will begin.
