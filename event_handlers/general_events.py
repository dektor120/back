from flask import request
from flask_socketio import emit
from extensions import db, socketio, cipher_suite
from models import ContactRequest, Country
from utils import log_event, is_valid_fullname, is_valid_phone


@socketio.on('connect')
def handle_connect():
    log_event('INFO', 'connection_established', f'Клиент подключился с IP: {request.remote_addr}', ip=request.remote_addr)


@socketio.on('submit_contact_request')
def handle_submit_contact_request(data):
    full_name = data.get('fullName')
    phone = data.get('phone')
    source = data.get('source')

    if not is_valid_fullname(full_name) or not is_valid_phone(phone) or not source:
        return emit('contact_request_response', {'success': False, 'message': 'Пожалуйста, заполните все поля корректно.'})

    encrypted_phone = cipher_suite.encrypt(phone.encode()).decode('utf-8')
    new_request = ContactRequest(full_name=full_name, phone_encrypted=encrypted_phone, source=source)
    db.session.add(new_request)
    db.session.commit()

    log_event('INFO', 'contact_request_new', f'Новая заявка от {full_name}, источник: {source}')
    emit('contact_request_response', {'success': True, 'message': 'Спасибо за вашу заявку! Мы скоро с вами свяжемся.'})
    # Уведомляем администраторов о новой заявке
    socketio.emit('new_contact_request_admin', room='admin_room')


@socketio.on('get_main_page_data')
def handle_get_main_page_data(data):
    try:
        popular_countries = Country.query.limit(6).all()
        countries_list = [{'id': c.id, 'name': c.name} for c in popular_countries]
        emit('main_page_data', {'countries': countries_list})
    except Exception as e:
        log_event('ERROR', 'get_main_page_data_fail', f"Ошибка при получении данных для главной: {e}")
