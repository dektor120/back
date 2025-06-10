from flask_socketio import emit
from sqlalchemy import func
from datetime import datetime, timedelta

from extensions import db, socketio, cipher_suite
from models import ScheduledTour, TourTemplate, Hotel, Booking, BookingTraveler, User
from utils import log_event, get_hotel_occupancy_on_dates, is_valid_fullname, is_valid_passport, is_valid_phone
from auth import token_required


@socketio.on('check_availability')
@token_required
def handle_check_availability(payload, cleaned_data):
    """Проверяет доступность мест в туре и номеров в отеле."""
    scheduled_tour_id = cleaned_data.get('scheduled_tour_id')
    people_requested = int(cleaned_data.get('people', 1))

    tour_info = db.session.query(ScheduledTour, TourTemplate, Hotel) \
        .join(TourTemplate, TourTemplate.id == ScheduledTour.tour_template_id) \
        .join(Hotel, Hotel.id == TourTemplate.hotel_id) \
        .filter(ScheduledTour.id == scheduled_tour_id).first()

    if not tour_info:
        return emit('availability_response', {'success': False, 'message': 'Выбранный тур не найден.'})

    st, tt, h = tour_info

    booked_seats_tour = db.session.query(func.sum(Booking.number_of_people)).filter(
        Booking.scheduled_tour_id == scheduled_tour_id, Booking.status != 'cancelled'
    ).scalar() or 0
    available_seats_in_tour = st.max_seats - booked_seats_tour

    if people_requested > available_seats_in_tour:
        message = f"В этой группе осталось только {available_seats_in_tour} мест(а)."
        return emit('availability_response', {'success': False, 'message': message})

    rooms_requested = (people_requested + 1) // 2
    start_date = datetime.strptime(st.start_date, '%Y-%m-%d').date()
    end_date = start_date + timedelta(days=tt.duration_days)
    max_occupancy_in_period = get_hotel_occupancy_on_dates(h.id, start_date, end_date)
    available_rooms_in_hotel = h.total_rooms - max_occupancy_in_period

    if rooms_requested > available_rooms_in_hotel:
        msg = f"В отеле '{h.name}' на выбранные даты недостаточно свободных номеров. Доступно: {available_rooms_in_hotel}."
        return emit('availability_response', {'success': False, 'message': msg})

    emit('availability_response', {
        'success': True,
        'message': "Отлично! Места в туре и отеле доступны.",
        'params_for_booking': {'scheduled_tour_id': scheduled_tour_id, 'people': people_requested}
    })


@socketio.on('create_booking')
@token_required
def handle_create_booking(payload, cleaned_data):
    """Создает новую бронь."""
    user_id = payload['user_id']
    booking_details = cleaned_data.get('booking_details')
    travelers_data = cleaned_data.get('travelers')
    scheduled_tour_id = booking_details.get('scheduled_tour_id')

    for i, traveler in enumerate(travelers_data):
        if not (is_valid_fullname(traveler.get('fullName')) and is_valid_passport(traveler.get('passport')) \
                and (not traveler.get('phone') or is_valid_phone(traveler.get('phone')))):
            return emit('booking_response', {'success': False, 'message': f"Некорректные данные для туриста №{i + 1}."})

    new_booking = Booking(
        user_id=user_id, scheduled_tour_id=scheduled_tour_id, number_of_people=len(travelers_data)
    )
    db.session.add(new_booking)
    db.session.commit()

    for traveler in travelers_data:
        encrypted_passport = cipher_suite.encrypt(traveler.get('passport').encode()).decode('utf-8')
        phone_data = traveler.get('phone')
        encrypted_phone = cipher_suite.encrypt(phone_data.encode()).decode('utf-8') if phone_data else None
        new_traveler = BookingTraveler(
            booking_id=new_booking.id, full_name=traveler.get('fullName'),
            passport_data_encrypted=encrypted_passport,
            phone_encrypted=encrypted_phone
        )
        db.session.add(new_traveler)
    db.session.commit()

    log_event('INFO', 'booking_success', f"Пользователь {user_id} забронировал тур (бронь №{new_booking.id})")
    emit('booking_response', {'success': True, 'message': f'Бронь №{new_booking.id} успешно оформлена!'})


@socketio.on('get_my_bookings')
@token_required
def handle_get_my_bookings(payload, cleaned_data):
    """Отправляет пользователю список его бронирований."""
    bookings = Booking.query.filter_by(user_id=payload['user_id']).order_by(Booking.created_at.desc()).all()
    bookings_list = []
    for b in bookings:
        scheduled_tour = db.session.query(TourTemplate.name, ScheduledTour.start_date).join(ScheduledTour).filter(
            ScheduledTour.id == b.scheduled_tour_id).first()
        tour_name = scheduled_tour.name if scheduled_tour else 'Тур был удален'
        start_date = scheduled_tour.start_date if scheduled_tour else 'N/A'
        bookings_list.append({
            'id': b.id, 'tour_name': tour_name, 'start_date': start_date,
            'people': b.number_of_people, 'status': b.status
        })
    emit('my_bookings_data', {'bookings': bookings_list})


@socketio.on('update_booking_status')
@token_required
def handle_update_booking_status(payload, cleaned_data):
    """Позволяет пользователю изменить статус своей брони (оплатить или отменить)."""
    booking_id = cleaned_data.get('booking_id')
    new_status = cleaned_data.get('status')

    if new_status not in ['paid', 'cancelled']: return emit('error', {'message': 'Недопустимый статус.'})

    booking = Booking.query.filter_by(id=booking_id, user_id=payload['user_id']).first()
    if not booking: return emit('error', {'message': 'Бронирование не найдено.'})
    if booking.status != 'pending_payment': return emit('error', {'message': f'Нельзя изменить статус этой брони.'})

    booking.status = new_status
    db.session.commit()
    log_event('INFO', 'booking_status_update',
              f"Пользователь {payload['user_id']} изменил статус брони {booking_id} на {new_status}.")
    emit('booking_status_updated', {'message': 'Статус бронирования успешно изменен!'})
