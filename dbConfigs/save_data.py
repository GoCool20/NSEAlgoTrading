from db_sqlalchemy import SQLAlchemyDatabase
from db_config import load_config

def get_database():
    config = load_config()
    db_type = config["db_type"]

    if db_type == "sqlite":
        path = config["sqlite"]["db_path"]
        return SQLAlchemyDatabase(f"sqlite:///{path}")
    elif db_type == "mysql":
        mysql = config["mysql"]
        return SQLAlchemyDatabase(f"mysql+pymysql://{mysql['user']}:{mysql['password']}@{mysql['host']}:{mysql['port']}/{mysql['database']}")
    elif db_type == "oracle":
        oracle = config["oracle"]
        return SQLAlchemyDatabase(f"oracle+cx_oracle://{oracle['user']}:{oracle['password']}@{oracle['dsn']}")
    else:
        raise ValueError("Unsupported DB type")
