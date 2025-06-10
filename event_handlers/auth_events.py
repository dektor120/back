import jwt
from datetime import datetime, timedelta
from flask import current_app
from flask_socketio import emit
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, socketio
from models import User, UserProfile
from utils import log_event, is_valid_login, is_valid_email, is_valid_password


@socketio.on('register')
def handle_register(data):
    """Обрабатывает регистрацию нового пользователя."""
    login = data.get('login')
    email = data.get('email')
    password = data.get('password')

    if not is_valid_login(login):
        return emit('register_response', {'success': False, 'message': 'Логин должен быть 5-20 символов и содержать только латиницу, цифры и подчеркивание.'})
    if not is_valid_email(email):
        return emit('register_response', {'success': False, 'message': 'Некорректный формат email.'})
    if not is_valid_password(password):
        return emit('register_response', {'success': False, 'message': 'Пароль должен быть не менее 6 символов.'})

    if User.query.filter((User.login == login) | (User.email == email)).first():
        return emit('register_response', {'success': False, 'message': 'Пользователь с таким логином или email уже существует.'})

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(login=login, email=email, password_hash=hashed_password, role='client')
    db.session.add(new_user)
    db.session.commit()

    log_event('INFO', 'register_success', f"Пользователь {login} успешно зарегистрирован.")
    emit('register_response', {'success': True, 'message': 'Регистрация прошла успешно! Теперь вы можете войти.'})


@socketio.on('login')
def handle_login(data):
    """Обрабатывает вход пользователя в систему."""
    login = data.get('login')
    password = data.get('password')
    user = User.query.filter_by(login=login).first()

    if user and check_password_hash(user.password_hash, password):
        profile_filled = UserProfile.query.filter_by(user_id=user.id).first() is not None
        token = jwt.encode({
            'user_id': user.id, 'login': user.login, 'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        log_event('INFO', 'login_success', f"Успешный вход для: {login}", user_id=user.id)
        emit('login_response', {'success': True, 'token': token, 'profile_filled': profile_filled, 'role': user.role})
    else:
        log_event('WARN', 'login_fail', f"Неудачная попытка входа для: {login}")
        emit('login_response', {'success': False, 'message': 'Неверный логин или пароль.'})