from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from pymongo import MongoClient
from config import get_cipher_suite, Config

db = SQLAlchemy()
socketio = SocketIO()
cipher_suite = get_cipher_suite()

try:
    client = MongoClient(Config.MONGO_URI)
    client.server_info()
    mongo_db = client[Config.MONGO_DB_NAME]
    print("Успешное подключение к MongoDB.")
except Exception as e:
    print(f"Ошибка подключения к MongoDB: {e}")
    mongo_db = None
