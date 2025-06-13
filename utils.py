import re
from datetime import datetime, timedelta

from extensions import mongo_db, db
from models import TourTemplate, ScheduledTour, Booking


def log_event(level, event, message, **kwargs):
    if mongo_db is not None:
        log_entry = {'timestamp': datetime.utcnow(), 'level': level, 'event': event, 'message': message, **kwargs}
        mongo_db.logs.insert_one(log_entry)
    print(f"LOG [{level} - {event}]: {message}")


def is_valid_login(login):
    return re.match(r'^[a-zA-Z0-9_]{5,20}$', login)


def is_valid_password(password):
    if len(password) < 8:
        return False, "Пароль должен содержать не менее 8 символов."
    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву."
    if not re.search(r'[a-z]', password):
        return False, "Пароль должен содержать хотя бы одну строчную букву."
    if not re.search(r'[0-9]', password):
        return False, "Пароль должен содержать хотя бы одну цифру."
    return True, ""


def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email)


def is_valid_fullname(fullname):
    return re.match(r'^[а-яА-ЯёЁ\s-]{5,}$', fullname) and len(fullname.split()) >= 2


def is_valid_phone(phone):
    return re.match(r'^(\+7|8)\d{10}$', phone)


def is_valid_passport(passport):
    return re.match(r'^\d{4}\s\d{6}$', passport)


def get_hotel_occupancy_on_dates(hotel_id, check_start_date, check_end_date, exclude_booking_id=None):
    tour_templates_in_hotel_ids = [tt.id for tt in TourTemplate.query.filter_by(hotel_id=hotel_id).all()]
    if not tour_templates_in_hotel_ids: return 0

    scheduled_tours_in_hotel = ScheduledTour.query.filter(
        ScheduledTour.tour_template_id.in_(tour_templates_in_hotel_ids)).all()
    if not scheduled_tours_in_hotel: return 0

    relevant_bookings_query = Booking.query.filter(
        Booking.scheduled_tour_id.in_([st.id for st in scheduled_tours_in_hotel]),
        Booking.status != 'cancelled'
    )
    if exclude_booking_id:
        relevant_bookings_query = relevant_bookings_query.filter(Booking.id != exclude_booking_id)

    relevant_bookings = relevant_bookings_query.all()

    booking_tour_map = {}
    for st in scheduled_tours_in_hotel:
        template = TourTemplate.query.get(st.tour_template_id)
        if template:
            booking_tour_map[st.id] = {'start_date': st.start_date, 'duration': template.duration_days}

    occupancy_per_day = {}
    current_date_check = check_start_date
    while current_date_check < check_end_date:
        date_str = current_date_check.strftime('%Y-%m-%d')
        occupancy_per_day[date_str] = 0
        for booking in relevant_bookings:
            sch_tour_details = booking_tour_map.get(booking.scheduled_tour_id)
            if not sch_tour_details: continue

            b_start_date = datetime.strptime(sch_tour_details['start_date'], '%Y-%m-%d').date()
            b_end_date = b_start_date + timedelta(days=sch_tour_details['duration'])

            if b_start_date <= current_date_check < b_end_date:
                occupancy_per_day[date_str] += (booking.number_of_people + 1) // 2

        current_date_check += timedelta(days=1)

    return max(occupancy_per_day.values()) if occupancy_per_day else 0
