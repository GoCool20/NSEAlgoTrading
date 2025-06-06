from pathlib import Path
import logging
from download_extract import download_today_bhavcopy
from processor import process_files

if __name__ == "__main__":
    # Ensure the bhavcopy_sessions folder exists
    Path("./bhavcopy_sessions").mkdir(exist_ok=True)

    # Download and extract the ZIP file from NSE
    dirs = download_today_bhavcopy()

    if dirs is None:
        logging.error("Download failed. Exiting.")
        exit(1)

    # Process the files in the extracted folder using our DB configuration (via db_config.json)
    extract_path = str(dirs["extract_path"])
    process_files(extract_path)
