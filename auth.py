import jwt
from flask import current_app
from flask_socketio import emit
from utils import log_event


def get_token_from_payload(payload):
    """Создает JWT токен из данных."""
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")


def token_required(f):
    """Декоратор для проверки наличия и валидности JWT токена у пользователя."""
    def decorated_function(*args, **kwargs):
        data = args[0] if args and isinstance(args[0], dict) else {}
        token = data.get('token')
        if not token:
            log_event('WARN', 'auth_fail', 'Попытка доступа к защищенной функции без токена.')
            return emit('error', {'message': 'Токен отсутствует. Пожалуйста, перезайдите в систему.'})
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            cleaned_data = data.copy()
            cleaned_data.pop('token', None)
            return f(payload, cleaned_data, **kwargs)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return emit('error', {'message': 'Недействительный или просроченный токен. Пожалуйста, перезайдите.'})
    return decorated_function


def admin_required(f):
    """Декоратор для проверки прав администратора."""
    def decorated_function(*args, **kwargs):
        data = args[0] if args and isinstance(args[0], dict) else {}
        token = data.get('token')
        if not token:
            return emit('admin_error', {'message': 'Токен отсутствует.'})
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            if payload.get('role') != 'admin':
                return emit('admin_error', {'message': 'Недостаточно прав.'})
            cleaned_data = data.copy()
            cleaned_data.pop('token', None)
            return f(payload, cleaned_data, **kwargs)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return emit('admin_error', {'message': 'Недействительный токен.'})
    return decorated_function