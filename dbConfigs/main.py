from save_data import get_database

# Example Data
data = {"name": "Gokul", "email": "shindegokul@gmail.com"}

db = get_database()
db.connect()
db.save_data(data)
