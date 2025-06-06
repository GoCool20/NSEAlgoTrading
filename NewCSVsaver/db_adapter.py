import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_connection_string(config_path="db_config.json"):
    """
    Reads the database configuration and builds the SQLAlchemy connection string.
    """
    with open(config_path, "r") as f:
        config = json.load(f)

    db_type = config.get("db_type")

    if db_type == "sqlite":
        db_path = config["sqlite"]["db_path"]
        return f"sqlite:///{db_path}"
    elif db_type == "mysql":
        mysql_conf = config["mysql"]
        user = mysql_conf["user"]
        password = mysql_conf["password"]
        host = mysql_conf["host"]
        port = mysql_conf["port"]
        database = mysql_conf["database"]
        # Make sure to install a MySQL driver, e.g., pymysql (`pip install pymysql`)
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    elif db_type == "oracle":
        oracle_conf = config["oracle"]
        user = oracle_conf["user"]
        password = oracle_conf["password"]
        dsn = oracle_conf["dsn"]
        # Requires cx_Oracle (`pip install cx_Oracle`)
        return f"oracle+cx_oracle://{user}:{password}@{dsn}"
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

class SQLAlchemyAdapter:
    """
    SQLAlchemy adapter for managing connection and bulk inserts.
    """
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def bulk_insert(self, model_class, objects):
        self.session.bulk_save_objects(objects)
        self.session.commit()
        print(f"Inserted {len(objects)} rows into {model_class.__tablename__}")
