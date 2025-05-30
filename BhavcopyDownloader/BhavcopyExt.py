import requests
import zipfile
import io
from datetime import datetime, timedelta
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bhavcopy_download.log'),
        logging.StreamHandler()
    ]
)

def create_session_directory():
    """Create unique directory for each download session"""
    session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = Path(f"./bhavcopy_sessions/session_{session_time}")
    zip_path = base_path / "downloaded_zips"
    extract_path = base_path / "extracted_files"

    zip_path.mkdir(parents=True, exist_ok=True)
    extract_path.mkdir(parents=True, exist_ok=True)

    return {
        'base_path': base_path,
        'zip_path': zip_path,
        'extract_path': extract_path,
        'session_id': session_time
    }


def download_today_bhavcopy():
    dirs = create_session_directory()
    logging.info(f"Created new session directory: {dirs['base_path']}")

    from datetime import datetime, timedelta

    # Example list of NSE holidays (YYYY-MM-DD format)
    NSE_HOLIDAYS = [
        "2025-02-26",  # Mahashivratri (Wednesday)
        "2025-03-14",  # Holi (Friday)
        "2025-03-31",  # Id-Ul-Fitr (Ramadan Eid) (Monday)
        "2025-04-10",  # Shri Mahavir Jayanti (Thursday)
        "2025-04-14",  # Dr. Baba Saheb Ambedkar Jayanti (Monday)
        "2025-04-18",  # Good Friday (Friday)
        "2025-05-01",  # Maharashtra Day (Thursday)
        "2025-08-15",  # Independence Day / Parsi New Year (Friday)
        "2025-08-27",  # Shri Ganesh Chaturthi (Wednesday)
        "2025-10-02",  # Mahatma Gandhi Jayanti/Dussehra (Thursday)
        "2025-10-21",  # Diwali Laxmi Pujan (Tuesday)
        "2025-10-22",  # Balipratipada (Wednesday)
        "2025-11-05",  # Prakash Gurpurb Sri Guru Nanak Dev (Wednesday)
        "2025-12-25"  # Christmas (Thursday)
    ]

    def get_previous_trading_day(current_date=None):
        if current_date is None:
            current_date = datetime.now().date()

        previous_day = current_date - timedelta(days=1)

        while True:
            # Skip weekends (5=Saturday, 6=Sunday)
            if previous_day.weekday() >= 5:
                previous_day -= timedelta(days=1)
                continue

            # Skip holidays (check if date is in holiday list)
            if previous_day.strftime("%Y-%m-%d") in NSE_HOLIDAYS:
                previous_day -= timedelta(days=1)
                continue

            break  # Found the last trading day

        return previous_day

    last_trading_day = get_previous_trading_day()
    print("Last trading day:", last_trading_day)




    # Extract day, month, and year
    D = last_trading_day.day
    year_short = last_trading_day.strftime("%y")
    month = last_trading_day.strftime("%m")

    #constructing the URL
    url = f"https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{D}{month}{year_short}.zip"

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.nseindia.com/'
    }

    try:
        logging.info(f"Attempting to download: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # Saving the zip file with timestamp
            zip_filename = dirs['zip_path'] / f"PR{D}{month}{year_short}.zip"
            with open(zip_filename, 'wb') as f:
                f.write(response.content)
            logging.info(f"Downloaded successfully to {zip_filename}")

            # Extracting the zip file
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Extracting all files to the extraction directory
                z.extractall(dirs['extract_path'])
                extracted_files = z.namelist()

            logging.info(f"Extracted {len(extracted_files)} files to {dirs['extract_path']}")
            for file in extracted_files:
                logging.info(f"Extracted: {file}")

            # Writing a session info file
            with open(dirs['base_path'] / "session_info.txt", 'w') as f:
                f.write(f"Session ID: {dirs['session_id']}\n")
                f.write(f"Download URL: {url}\n")
                f.write(f"Download Time: {datetime.now()}\n")
                f.write(f"Files Extracted: {', '.join(extracted_files)}\n")

        else:
            logging.error(f"File not found. Status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error occurred: {e}")
    except zipfile.BadZipFile as e:
        logging.error(f"Invalid ZIP file: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Creating main sessions directory if it doesn't exist
    Path("./bhavcopy_sessions").mkdir(exist_ok=True)
    download_today_bhavcopy()