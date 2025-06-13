import os
from cryptography.fernet import Fernet

basedir = os.path.abspath(os.path.dirname(__file__))


def get_cipher_suite():
    key_file = 'secret.key'
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
    else:
        with open(key_file, 'rb') as f:
            key = f.read()
    return Fernet(key)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my-super-secret-key!'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MONGO_URI = 'mongodb://localhost:27017/'
    MONGO_DB_NAME = 'tur_service_db'


