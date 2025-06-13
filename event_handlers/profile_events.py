from flask_socketio import emit
from extensions import db, socketio, cipher_suite
from models import UserProfile, SavedTraveler
from utils import log_event, is_valid_fullname, is_valid_phone, is_valid_passport
from auth import token_required


@socketio.on('get_my_profile')
@token_required
def handle_get_my_profile(payload, cleaned_data):
    profile = UserProfile.query.filter_by(user_id=payload['user_id']).first()
    profile_data = {}
    if profile:
        try:
            phone = cipher_suite.decrypt(profile.contact_phone_encrypted.encode()).decode()
        except Exception:
            phone = "Ошибка данных"
        profile_data = {'full_name': profile.full_name, 'birth_date': profile.birth_date, 'contact_phone': phone}
    emit('my_profile_data', {'profile': profile_data, 'is_filled': bool(profile)})


@socketio.on('update_my_profile')
@token_required
def handle_update_my_profile(payload, cleaned_data):
    user_id = payload['user_id']
    data = cleaned_data.get('profile')

    if not is_valid_fullname(data.get('fullName')) or not is_valid_phone(data.get('contactPhone')):
        return emit('profile_update_response', {'success': False, 'message': 'Пожалуйста, введите корректные данные.'})

    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)

    profile.full_name = data.get('fullName')
    profile.birth_date = data.get('birthDate')
    profile.contact_phone_encrypted = cipher_suite.encrypt(data.get('contactPhone').encode()).decode('utf-8')
    db.session.commit()

    log_event('INFO', 'profile_update', f"Пользователь {user_id} обновил свой профиль.")
    emit('profile_update_response', {'success': True, 'message': 'Профиль успешно сохранен!'})


@socketio.on('get_saved_travelers')
@token_required
def handle_get_saved_travelers(payload, cleaned_data):
    travelers = SavedTraveler.query.filter_by(user_id=payload['user_id']).all()
    travelers_list = []
    for t in travelers:
        try:
            phone = cipher_suite.decrypt(t.phone_encrypted.encode()).decode() if t.phone_encrypted else ''
            passport = cipher_suite.decrypt(t.passport_data_encrypted.encode()).decode()
        except Exception:
            phone, passport = "Ошибка данных", "Ошибка данных"
        travelers_list.append({'id': t.id, 'full_name': t.full_name, 'passport': passport, 'phone': phone})
    emit('saved_travelers_data', {'travelers': travelers_list})


@socketio.on('add_saved_traveler')
@token_required
def handle_add_saved_traveler(payload, cleaned_data):
    user_id = payload['user_id']
    data = cleaned_data.get('traveler')

    if not is_valid_fullname(data.get('fullName')) or not is_valid_passport(data.get('passport')) \
            or (data.get('phone') and not is_valid_phone(data.get('phone'))):
        return emit('error', {'message': 'Пожалуйста, введите корректные данные туриста.'})

    encrypted_passport = cipher_suite.encrypt(data.get('passport').encode()).decode('utf-8')
    phone_data = data.get('phone')
    encrypted_phone = cipher_suite.encrypt(phone_data.encode()).decode('utf-8') if phone_data else None

    new_traveler = SavedTraveler(
        user_id=user_id, full_name=data.get('fullName'),
        passport_data_encrypted=encrypted_passport,
        phone_encrypted=encrypted_phone
    )
    db.session.add(new_traveler)
    db.session.commit()
    log_event('INFO', 'add_traveler', f"Пользователь {user_id} добавил туриста.")
    emit('traveler_added_success', {'message': 'Турист успешно добавлен!'})


@socketio.on('update_saved_traveler')
@token_required
def handle_update_saved_traveler(payload, cleaned_data):
    user_id = payload['user_id']
    traveler_id = cleaned_data.get('traveler_id')
    data = cleaned_data.get('traveler')

    if not is_valid_fullname(data.get('fullName')) or not is_valid_passport(data.get('passport')) \
            or (data.get('phone') and not is_valid_phone(data.get('phone'))):
        return emit('error', {'message': 'Пожалуйста, введите корректные данные туриста.'})

    traveler = SavedTraveler.query.filter_by(id=traveler_id, user_id=user_id).first()
    if not traveler: return emit('error', {'message': 'Турист не найден.'})

    traveler.full_name = data.get('fullName')
    traveler.passport_data_encrypted = cipher_suite.encrypt(data.get('passport').encode()).decode('utf-8')
    phone = data.get('phone')
    traveler.phone_encrypted = cipher_suite.encrypt(phone.encode()).decode('utf-8') if phone else None

    db.session.commit()
    log_event('INFO', 'update_traveler', f"Пользователь {user_id} обновил туриста ID:{traveler_id}.")
    emit('traveler_updated_success', {'message': 'Данные туриста обновлены!'})


@socketio.on('delete_saved_traveler')
@token_required
def handle_delete_saved_traveler(payload, cleaned_data):
    user_id = payload['user_id']
    traveler_id = cleaned_data.get('traveler_id')
    traveler = SavedTraveler.query.filter_by(id=traveler_id, user_id=user_id).first()
    if traveler:
        db.session.delete(traveler)
        db.session.commit()
        log_event('INFO', 'delete_traveler', f"Пользователь {user_id} удалил туриста ID:{traveler_id}.")
        emit('traveler_deleted_success', {'message': 'Турист удален.'})
    else:
        emit('error', {'message': 'Турист не найден.'})
