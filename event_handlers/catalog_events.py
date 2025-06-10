from flask_socketio import emit
from extensions import db, socketio, mongo_db
from models import ScheduledTour, TourTemplate, Hotel, City, Country
from utils import log_event


@socketio.on('get_tours_for_client')
def handle_get_tours_for_client(data):
    """Отправляет клиенту список туров из расписания с учетом фильтров."""
    filters = data.get('filters', {}) if isinstance(data, dict) else {}
    log_event('INFO', 'get_tours_client', f"Запрос списка туров с фильтрами: {filters}")

    try:
        query = db.session.query(ScheduledTour, TourTemplate, Hotel, City, Country) \
            .join(TourTemplate, TourTemplate.id == ScheduledTour.tour_template_id) \
            .join(Hotel, Hotel.id == TourTemplate.hotel_id) \
            .join(City, City.id == Hotel.city_id) \
            .join(Country, Country.id == City.country_id)

        if filters.get('country_id'):
            query = query.filter(Country.id == int(filters['country_id']))
        if filters.get('city_id'):
            query = query.filter(City.id == int(filters['city_id']))
        if filters.get('start_date'):
            query = query.filter(ScheduledTour.start_date >= filters['start_date'])

        tours_in_schedule = query.order_by(ScheduledTour.start_date).all()
        tours_list = []
        for st, tt, h, ci, co in tours_in_schedule:
            tour_details = mongo_db.tour_template_details.find_one({'_id': tt.id})
            tours_list.append({
                'scheduled_tour_id': st.id,
                'name': tt.name,
                'country': co.name, 'city': ci.name, 'hotel_name': h.name, 'stars': h.stars,
                'start_date': st.start_date, 'duration_days': tt.duration_days,
                'price': st.price, 'max_seats': st.max_seats,
                'description': tour_details.get('itinerary', 'Описание отсутствует.') if tour_details else 'Описание отсутствует.',
                'photo_urls': tour_details.get('photo_urls', []) if tour_details else []
            })
        emit('client_tours_data', {'tours': tours_list})
    except Exception as e:
        log_event('ERROR', 'get_tours_client_fail', f"Ошибка при получении туров: {e}")


@socketio.on('get_filter_dictionaries')
def handle_get_filter_dictionaries(data):
    """Отправляет справочники стран и городов для фильтров на клиенте."""
    try:
        countries = Country.query.order_by(Country.name).all()
        cities = City.query.order_by(City.name).all()
        emit('filter_dictionaries_data', {
            'countries': [{'id': c.id, 'name': c.name} for c in countries],
            'cities': [{'id': c.id, 'name': c.name, 'country_id': c.country_id} for c in cities]
        })
    except Exception as e:
        log_event('ERROR', 'get_filter_dicts_fail', f"Ошибка при получении справочников: {e}")


@socketio.on('get_hotels')
def handle_get_hotels(data):
    """Отправляет полный список отелей и связанных справочников."""
    try:
        hotels = Hotel.query.order_by(Hotel.name).all()
        hotel_ids = [h.id for h in hotels]
        mongo_details = list(mongo_db.hotel_details.find({'_id': {'$in': hotel_ids}}))

        emit('hotels_data', {
            'hotels': [{'id': h.id, 'name': h.name, 'city_id': h.city_id, 'stars': h.stars, 'total_rooms': h.total_rooms} for h in hotels],
            'cities': [{'id': c.id, 'name': c.name, 'country_id': c.country_id} for c in City.query.all()],
            'countries': [{'id': c.id, 'name': c.name} for c in Country.query.all()],
            'mongo_details': mongo_details
        })
    except Exception as e:
        log_event('ERROR', 'get_hotels_fail', f"Ошибка при получении отелей: {e}")