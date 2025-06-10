import pytest
from app import create_app, db, socketio
from config import Config
from database_setup import setup_database


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


@pytest.fixture(scope='function')
def client():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        setup_database(app)

        test_client = socketio.test_client(app)

        yield test_client

        db.session.remove()
        db.drop_all()