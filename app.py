from flask import Flask
from config import Config
from extensions import db, socketio
from database_setup import setup_database


def create_app(config_class=Config):
    """
    Создает и конфигурирует экземпляр приложения Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    socketio.init_app(app)

    from routes import pages
    app.register_blueprint(pages)

    from event_handlers import general_events
    from event_handlers import auth_events
    from event_handlers import profile_events
    from event_handlers import catalog_events
    from event_handlers import booking_events
    from event_handlers import admin_events

    return app


app = create_app()

if __name__ == '__main__':
    setup_database(app)

    print("Запуск сервера...")
    try:
        socketio.run(
            app,
            debug=True,
            host='0.0.0.0',
            port=5001,
            allow_unsafe_werkzeug=True,
            ssl_context='adhoc'
        )
    except ImportError:

        print("=" * 60)
        print("ПРЕДУПРЕЖДЕНИЕ: Не удалось запустить HTTPS. Библиотека pyOpenSSL не установлена.")
        print("Чтобы включить HTTPS, выполните: pip install pyOpenSSL")
        print("Запуск в обычном HTTP режиме...")
        print("=" * 60)
        socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)