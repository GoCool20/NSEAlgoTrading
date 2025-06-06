import requests
import zipfile
import io
from datetime import datetime, timedelta
import logging
from pathlib import Path

# ------------------------ Logging Setup ------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bhavcopy_download.log'),
        logging.StreamHandler()
    ]
)

# ------------------------ Session Directory ------------------------
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


# ------------------------ Bhavcopy Download ------------------------
def download_today_bhavcopy():
    dirs = create_session_directory()
    logging.info(f"Created new session directory: {dirs['base_path']}")

    # NSE holidays (update as needed)
    NSE_HOLIDAYS = [
        "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
        "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
        "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22",
        "2025-11-05", "2025-12-25"
    ]

    def get_previous_trading_day(current_date=None):
        if current_date is None:
            current_date = datetime.now().date()
        previous_day = current_date - timedelta(days=1)
        while previous_day.weekday() >= 5 or previous_day.strftime("%Y-%m-%d") in NSE_HOLIDAYS:
            previous_day -= timedelta(days=1)
        return previous_day

    last_trading_day = get_previous_trading_day()
    logging.info(f"Last trading day: {last_trading_day}")

    day = last_trading_day.strftime('%d')
    month = last_trading_day.strftime('%m')
    year_short = last_trading_day.strftime('%y')

    url = f"https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{day}{month}{year_short}.zip"

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.nseindia.com/'
    }

    try:
        logging.info(f"Attempting to download: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            zip_filename = dirs['zip_path'] / f"PR{day}{month}{year_short}.zip"
            with open(zip_filename, 'wb') as f:
                f.write(response.content)
            logging.info(f"Downloaded successfully to {zip_filename}")

            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                z.extractall(dirs['extract_path'])
                extracted_files = z.namelist()

            logging.info(f"Extracted {len(extracted_files)} files to {dirs['extract_path']}")
            for file in extracted_files:
                logging.info(f"Extracted: {file}")

            # Save session info into a text file
            session_info_file = dirs['base_path'] / "session_info.txt"
            with open(session_info_file, 'w') as f:
                f.write(f"Session ID: {dirs['session_id']}\n")
                f.write(f"Download URL: {url}\n")
                f.write(f"Download Time: {datetime.now()}\n")
                f.write(f"Files Extracted: {', '.join(extracted_files)}\n")

            return dirs  # Return directory info for further processing
        else:
            logging.error(f"File not found. Status: {response.status_code}")
    except Exception as e:
        logging.error(f"Error during download or extraction check your internet Connection try again: {e}")

    return None

