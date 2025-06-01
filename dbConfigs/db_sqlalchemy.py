from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from db_interface import DatabaseInterface

class SQLAlchemyDatabase(DatabaseInterface):
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def connect(self):
        self.engine = create_engine(self.connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_data(self, data):
        session = self.Session()
        user = User(**data)
        session.add(user)
        session.commit()
        session.close()



