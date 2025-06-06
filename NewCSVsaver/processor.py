import os
import re
import csv
import logging
from models import (
    Base, BcRecord, BhRecord, CorpBondRecord, EtfRecord, GlRecord, HlRecord,
    McapRecord, PdRecord, PrRecord, SmeRecord, TtRecord
)
from db_adapter import get_connection_string, SQLAlchemyAdapter

# -----------------------
# Logging Setup
# -----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -----------------------
# File Type Configuration
# -----------------------
# (You can optionally remove the "unique_keys" since they're no longer used.)
FILE_TYPE_CONFIG = [
    {"prefix": "Bc", "parser": "csv", "delimiter": ",", "model": "BcRecord"},
    {"prefix": "bh", "parser": "csv", "delimiter": ",", "model": "BhRecord",
     "column_map": {"high/low": "high_low"}},
    {"prefix": "corpbond", "parser": "csv", "delimiter": ",", "model": "CorpBondRecord"},
    {"prefix": "etf", "parser": "csv", "delimiter": ",", "model": "EtfRecord",
     "column_map": {
         "previous_close_price": "prev_close_price",
         "52_week_high": "week_52_high",
         "52_week_low": "week_52_low"
     }},
    {"prefix": "Gl", "parser": "csv", "delimiter": ",", "model": "GlRecord",
     "column_map": {
         "gain_loss": "gain_or_loss",
         "close_pric": "close_price",
         "prev_cl_pr": "prev_close_price",
         "percent_cg": "percent_change"
     }},
    {"prefix": "HL", "parser": "csv", "delimiter": ",", "model": "HlRecord"},
    {"prefix": "MCAP", "parser": "csv", "delimiter": ",", "model": "McapRecord",
     "column_map": {
         "face_value(rs.)": "face_value",
         "close_price_paid_up_value(rs.)": "close_price",
         "market_cap(rs.)": "market_cap"
     }},
    {"prefix": "Pd", "parser": "csv", "delimiter": ",", "model": "PdRecord"},
    {"prefix": "Pr", "parser": "csv", "delimiter": ",", "model": "PrRecord"},
    {"prefix": "sme", "parser": "csv", "delimiter": ",", "model": "SmeRecord"},
    {"prefix": "Tt", "parser": "csv", "delimiter": ",", "model": "TtRecord"}
]

# -----------------------
# Model Mapping
# -----------------------
MODEL_MAPPING = {
    "BcRecord": BcRecord,
    "BhRecord": BhRecord,
    "CorpBondRecord": CorpBondRecord,
    "EtfRecord": EtfRecord,
    "GlRecord": GlRecord,
    "HlRecord": HlRecord,
    "McapRecord": McapRecord,
    "PdRecord": PdRecord,
    "PrRecord": PrRecord,
    "SmeRecord": SmeRecord,
    "TtRecord": TtRecord
}


# -----------------------
# Parser Classes
# -----------------------
class BaseParser:
    def parse(self, file_path, file_def):
        raise NotImplementedError


class CsvParser(BaseParser):
    def parse(self, file_path, file_def):
        results = []
        delimiter = file_def.get("delimiter", ",")
        with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            for row in reader:
                results.append(row)
        return results


def get_parser(parser_type):
    if parser_type == "csv":
        return CsvParser()
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")


# -----------------------
# Helper: Rename, Clean, and Convert Row Keys
# -----------------------
def process_row_keys(row, file_def):
    """
    Cleans header keys and converts numeric fields:
    - Converts keys to lowercase, trims whitespace, replaces spaces and slashes with underscores.
    - Applies column mapping if provided.
    - Converts empty strings to None for numeric fields.
    """
    cleaned = {}
    column_map = file_def.get("column_map", {})
    numeric_fields = {"close_price", "prev_close_price", "percent_change", "face_value", "market_cap"}

    for k, v in row.items():
        if k is None:
            continue
        key = str(k).strip().lower().replace(" ", "_").replace("/", "_")
        if key in column_map:
            key = column_map[key]
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                cleaned[key] = None
                continue
            if key in numeric_fields:
                try:
                    cleaned[key] = float(v)
                except ValueError:
                    cleaned[key] = None
            else:
                cleaned[key] = v
        else:
            cleaned[key] = v
    return cleaned


# -----------------------
# File Matching Helper
# -----------------------
def match_file(file_name, file_types):
    """
    Returns the configuration entry from FILE_TYPE_CONFIG whose prefix matches the given file name.
    Expects the filename to start with a prefix followed by 6 or 8 digits.
    """
    for file_def in file_types:
        prefix = file_def["prefix"]
        pattern = rf"^{re.escape(prefix)}\d{{6,8}}"
        if re.match(pattern, file_name, re.IGNORECASE):
            return file_def
    return None


# -----------------------
# Process Files Routine without Duplicate Check
# -----------------------
def process_files(directory, db_config_path="db_config.json"):
    connection_string = get_connection_string(db_config_path)
    db_adapter = SQLAlchemyAdapter(connection_string)

    # Ensure required tables exist before processing.
    Base.metadata.create_all(db_adapter.engine)

    for file_name in os.listdir(directory):
        if file_name.startswith("."):
            continue

        file_def = match_file(file_name, FILE_TYPE_CONFIG)
        if not file_def:
            logging.info(f"Skipping file {file_name}: no matching configuration")
            continue

        parser = get_parser(file_def["parser"])
        file_path = os.path.join(directory, file_name)
        logging.info(f"Processing file {file_name} using parser {file_def['parser']}")

        try:
            raw_data = parser.parse(file_path, file_def)
            model_name = file_def["model"]
            model_class = MODEL_MAPPING.get(model_name)
            if not model_class:
                logging.error(f"No model found for '{model_name}'")
                continue

            instances = []
            for row in raw_data:
                try:
                    row_cleaned = process_row_keys(row, file_def)
                    instance = model_class(**row_cleaned)
                    db_adapter.session.add(instance)
                    instances.append(instance)
                except Exception as row_e:
                    logging.error(f"Error creating {model_name} instance: {row_e} -- Row data: {row}")

            if instances:
                try:
                    db_adapter.session.commit()
                    logging.info(f"Inserted {len(instances)} new {model_name} records from file {file_name}")
                except Exception as bulk_e:
                    logging.error(f"Bulk insert error for file {file_name}: {bulk_e}")
                    db_adapter.session.rollback()
                    # Optionally, you can add a fallback mechanism here for individual inserts.
            else:
                logging.info(f"No valid data found in {file_name} to insert.")
        except Exception as e:
            logging.error(f"Error processing file {file_name}: {e}")
            db_adapter.session.rollback()
