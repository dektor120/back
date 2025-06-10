from flask import request
from flask_socketio import emit
from datetime import datetime, date as date_type, timedelta

from extensions import db, socketio, mongo_db, cipher_suite
from models import *
from utils import log_event, get_hotel_occupancy_on_dates
from auth import admin_required
from .catalog_events import handle_get_hotels, handle_get_tours_for_client  


@socketio.on('join_admin_room')
@admin_required
def handle_join_admin_room(payload, cleaned_data):
    """Присоединяет администратора к специальной комнате для получения уведомлений."""
    if request.sid:
        socketio.join_room('admin_room', request.sid)
    log_event('INFO', 'admin_join', f"Админ {payload['login']} присоединился к комнате уведомлений.")


@socketio.on('get_admin_dashboard_data')
@admin_required
def handle_get_admin_dashboard_data(payload, cleaned_data):
    """Отправляет данные для главной страницы админ-панели."""
    new_requests = ContactRequest.query.filter_by(is_completed=False).order_by(ContactRequest.created_at.desc()).all()
    new_requests_list = []
    for r in new_requests:
        try:
            phone = cipher_suite.decrypt(r.phone_encrypted.encode()).decode()
        except Exception:
            phone = "Ошибка данных"
        new_requests_list.append({'id': r.id, 'full_name': r.full_name, 'phone': phone, 'source': r.source,
                                  'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')})

    completed_requests = ContactRequest.query.filter_by(is_completed=True).order_by(
        ContactRequest.created_at.desc()).limit(15).all()
    completed_requests_list = []
    for r in completed_requests:
        try:
            phone = cipher_suite.decrypt(r.phone_encrypted.encode()).decode()
        except Exception:
            phone = "Ошибка данных"
        completed_requests_list.append({'id': r.id, 'full_name': r.full_name, 'phone': phone, 'source': r.source,
                                        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')})

    all_bookings = db.session.query(Booking, User.login).join(User).order_by(Booking.created_at.desc()).limit(20).all()
    bookings_list = []
    for booking, login in all_bookings:
        st = ScheduledTour.query.get(booking.scheduled_tour_id)
        tt = TourTemplate.query.get(st.tour_template_id) if st else None
        bookings_list.append({'id': booking.id, 'user_login': login, 'tour_name': tt.name if tt else 'Тур удален',
                              'status': booking.status})

    emit('admin_dashboard_data', {
        'requests': new_requests_list,
        'completed_requests': completed_requests_list,
        'bookings': bookings_list
    })


@socketio.on('complete_request')
@admin_required
def handle_complete_request(payload, cleaned_data):
    """Помечает заявку на обратный звонок как выполненную."""
    req = ContactRequest.query.get(cleaned_data.get('request_id'))
    if req:
        req.is_completed = True
        db.session.commit()
        log_event('INFO', 'request_completed', f"Админ {payload['login']} обработал заявку {req.id}")
        handle_get_admin_dashboard_data(payload, {})  # Обновляем данные на панели


@socketio.on('add_hotel')
@admin_required
def handle_add_hotel(payload, cleaned_data):
    sql_data = cleaned_data.get('hotel_sql')
    mongo_data = cleaned_data.get('hotel_mongo')
    new_hotel = Hotel(**sql_data)
    db.session.add(new_hotel);
    db.session.commit()
    mongo_data['_id'] = new_hotel.id
    mongo_db.hotel_details.insert_one(mongo_data)
    emit('admin_success', {'message': 'Отель успешно добавлен!'})
    handle_get_hotels({})


@socketio.on('update_hotel')
@admin_required
def handle_update_hotel(payload, cleaned_data):
    hotel_id = cleaned_data.get('hotel_id')
    sql_data = cleaned_data.get('hotel_sql')
    mongo_data = cleaned_data.get('hotel_mongo')
    Hotel.query.filter_by(id=hotel_id).update(sql_data)
    db.session.commit()
    mongo_db.hotel_details.update_one({'_id': hotel_id}, {'$set': mongo_data}, upsert=True)
    emit('admin_success', {'message': 'Отель успешно обновлен!'})
    handle_get_hotels({})


@socketio.on('delete_hotel')
@admin_required
def handle_delete_hotel(payload, cleaned_data):
    hotel_id = cleaned_data.get('hotel_id')
    if TourTemplate.query.filter_by(hotel_id=hotel_id).first():
        return emit('admin_error', {'message': 'Нельзя удалить отель, используемый в шаблонах туров.'})
    hotel = Hotel.query.get(hotel_id)
    if hotel:
        db.session.delete(hotel);
        db.session.commit()
        mongo_db.hotel_details.delete_one({'_id': hotel_id})
        emit('admin_success', {'message': 'Отель удален.'})
        handle_get_hotels({})
    else:
        emit('admin_error', {'message': 'Отель не найден.'})



@socketio.on('get_admin_data')
@admin_required
def handle_get_admin_data(payload, cleaned_data):
    """Отправляет админу все справочники для его форм."""
    try:
        countries = Country.query.order_by(Country.name).all()
        cities = City.query.order_by(City.name).all()
        hotels = Hotel.query.order_by(Hotel.name).all()
        tour_templates = TourTemplate.query.order_by(TourTemplate.name).all()
        emit('admin_dictionaries', {
            'countries': [{'id': c.id, 'name': c.name} for c in countries],
            'cities': [{'id': c.id, 'name': c.name, 'country_id': c.country_id} for c in cities],
            'hotels': [{'id': h.id, 'name': h.name, 'city_id': h.city_id} for h in hotels],
            'tour_templates': [
                {'id': tt.id, 'name': tt.name, 'hotel_id': tt.hotel_id, 'duration_days': tt.duration_days} for tt in
                tour_templates]
        })
    except Exception as e:
        log_event('ERROR', 'get_admin_data_fail', f"Ошибка при получении админ. данных: {e}")


@socketio.on('get_template_details')
@admin_required
def handle_get_template_details(payload, cleaned_data):
    """Получает детали шаблона (описание) из MongoDB."""
    details = mongo_db.tour_template_details.find_one({'_id': int(cleaned_data.get('template_id'))})
    emit('template_details_data', {'itinerary': details.get('itinerary', '') if details else ''})


@socketio.on('add_tour_template')
@admin_required
def handle_add_tour_template(payload, cleaned_data):
    sql_data = cleaned_data.get('template_sql')
    mongo_data = cleaned_data.get('template_mongo')
    new_template = TourTemplate(**sql_data)
    db.session.add(new_template);
    db.session.commit()
    mongo_data['_id'] = new_template.id
    mongo_db.tour_template_details.insert_one(mongo_data)
    emit('admin_success', {'message': 'Шаблон тура успешно создан!'})


@socketio.on('update_tour_template')
@admin_required
def handle_update_tour_template(payload, cleaned_data):
    template_id = cleaned_data.get('template_id')
    sql_data = cleaned_data.get('template_sql')
    mongo_data = cleaned_data.get('template_mongo')
    TourTemplate.query.filter_by(id=template_id).update(sql_data)
    db.session.commit()
    mongo_db.tour_template_details.update_one({'_id': template_id}, {'$set': mongo_data}, upsert=True)
    emit('admin_success', {'message': 'Шаблон тура обновлен!'})


@socketio.on('delete_tour_template')
@admin_required
def handle_delete_tour_template(payload, cleaned_data):
    template_id = cleaned_data.get('template_id')
    if ScheduledTour.query.filter_by(tour_template_id=template_id).first():
        return emit('admin_error', {'message': 'Нельзя удалить шаблон, используемый в расписании.'})
    template = TourTemplate.query.get(template_id)
    if template:
        db.session.delete(template);
        db.session.commit()
        mongo_db.tour_template_details.delete_one({'_id': template_id})
        emit('admin_success', {'message': 'Шаблон тура удален.'})
    else:
        emit('admin_error', {'message': 'Шаблон не найден.'})


@socketio.on('schedule_tour')
@admin_required
def handle_schedule_tour(payload, cleaned_data):
    template_id = cleaned_data.get('template_id')
    start_date_str = cleaned_data.get('start_date')
    price = float(cleaned_data.get('price'))
    max_seats = int(cleaned_data.get('max_seats'))

    try:
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if start_date_obj < date_type.today():
            return emit('admin_error', {'message': 'Нельзя ставить тур на прошедшую дату.'})
    except (ValueError, TypeError):
        return emit('admin_error', {'message': 'Некорректный формат даты.'})

    template_info = db.session.query(TourTemplate, Hotel).join(Hotel).filter(TourTemplate.id == template_id).first()
    if not template_info: return emit('admin_error', {'message': 'Шаблон тура не найден.'})

    tt, h = template_info

    end_date_obj = start_date_obj + timedelta(days=tt.duration_days)
    rooms_needed_by_tour = (max_seats + 1) // 2
    max_occupancy_in_period = get_hotel_occupancy_on_dates(h.id, start_date_obj, end_date_obj)
    available_rooms = h.total_rooms - max_occupancy_in_period
    if rooms_needed_by_tour > available_rooms:
        return emit('admin_error', {
            'message': f"В отеле доступно только {available_rooms} номеров, а тур требует {rooms_needed_by_tour}."})

    new_scheduled_tour = ScheduledTour(tour_template_id=template_id, start_date=start_date_str, price=price,
                                       max_seats=max_seats)
    db.session.add(new_scheduled_tour)
    db.session.commit()
    log_event('INFO', 'schedule_success', f"Тур '{tt.name}' добавлен в расписание на {start_date_str}.")
    emit('admin_success', {'message': 'Тур успешно добавлен в расписание!'})
    handle_get_tours_for_client({})


@socketio.on('delete_scheduled_tour')
@admin_required
def handle_delete_scheduled_tour(payload, cleaned_data):
    tour_id = cleaned_data.get('scheduled_tour_id')
    tour = ScheduledTour.query.get(tour_id)
    if tour:
        if Booking.query.filter_by(scheduled_tour_id=tour_id).first():
            return emit('admin_error', {'message': 'Нельзя удалить тур, на который есть брони. Сначала отмените их.'})
        db.session.delete(tour);
        db.session.commit()
        emit('admin_success', {'message': 'Тур удален из расписания.'})
        handle_get_tours_for_client({})
    else:
        emit('admin_error', {'message': 'Тур не найден.'})