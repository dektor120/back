from werkzeug.security import generate_password_hash
from extensions import db
from models import User, Country, City, Hotel, TourTemplate


def setup_database(app):
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(login='admin').first():
            hashed_password = generate_password_hash('admin', method='pbkdf2:sha256')
            admin_user = User(login='admin', email='admin@example.com', password_hash=hashed_password, role='admin')
            db.session.add(admin_user)
            print("Администратор 'admin' с паролем 'admin' создан.")

        if not Country.query.first():
            print("Наполнение справочников...")
            countries_map = {name: Country(name=name) for name in
                             ['Египет', 'Франция', 'Таиланд', 'Италия', 'Турция', 'Индонезия', 'Япония']}
            db.session.add_all(countries_map.values())
            db.session.commit()

            cities_data = [
                {'name': 'Хургада', 'country': 'Египет'}, {'name': 'Каир', 'country': 'Египет'},
                {'name': 'Париж', 'country': 'Франция'}, {'name': 'Пхукет', 'country': 'Таиланд'},
                {'name': 'Рим', 'country': 'Италия'}, {'name': 'Венеция', 'country': 'Италия'},
                {'name': 'Стамбул', 'country': 'Турция'}, {'name': 'Бали', 'country': 'Индонезия'},
                {'name': 'Токио', 'country': 'Япония'}, {'name': 'Киото', 'country': 'Япония'}
            ]
            cities_map = {c['name']: City(name=c['name'], country_id=countries_map[c['country']].id) for c in
                          cities_data}
            db.session.add_all(cities_map.values())
            db.session.commit()

            hotels_data = [
                {'id': 1, 'name': 'Sunrise Aqua Joy Resort', 'city_id': cities_map['Хургада'].id, 'stars': 4,
                 'total_rooms': 150},
                {'id': 2, 'name': 'Pyramids View Inn', 'city_id': cities_map['Каир'].id, 'stars': 3, 'total_rooms': 20},
                {'id': 3, 'name': 'Hotel du Louvre', 'city_id': cities_map['Париж'].id, 'stars': 5, 'total_rooms': 80},
                {'id': 4, 'name': 'Mom’art Hotel', 'city_id': cities_map['Париж'].id, 'stars': 4, 'total_rooms': 40},
                {'id': 5, 'name': 'The Kee Resort & Spa', 'city_id': cities_map['Пхукет'].id, 'stars': 4,
                 'total_rooms': 120},
                {'id': 6, 'name': 'SALA Phuket Mai Khao Beach Resort', 'city_id': cities_map['Пхукет'].id, 'stars': 5,
                 'total_rooms': 60},
                {'id': 7, 'name': 'Hotel Fori Imperiali Cavalieri', 'city_id': cities_map['Рим'].id, 'stars': 3,
                 'total_rooms': 50},
                {'id': 8, 'name': 'Anantara Uluwatu Bali Resort', 'city_id': cities_map['Бали'].id, 'stars': 5,
                 'total_rooms': 70},
                {'id': 9, 'name': 'CVK Park Bosphorus Hotel Istanbul', 'city_id': cities_map['Стамбул'].id, 'stars': 5,
                 'total_rooms': 200},
                {'id': 10, 'name': 'Shibuya Excel Hotel Tokyu', 'city_id': cities_map['Токио'].id, 'stars': 4,
                 'total_rooms': 150},
                {'id': 11, 'name': 'Hotel Canal Grande', 'city_id': cities_map['Венеция'].id, 'stars': 4,
                 'total_rooms': 40},
                {'id': 12, 'name': 'The Westin Excelsior, Rome', 'city_id': cities_map['Рим'].id, 'stars': 5,
                 'total_rooms': 100},
                {'id': 13, 'name': 'Tawaraya Ryokan', 'city_id': cities_map['Киото'].id, 'stars': 5, 'total_rooms': 18},
                {'id': 14, 'name': '9h nine hours Shinjuku-North', 'city_id': cities_map['Токио'].id, 'stars': 2,
                 'total_rooms': 200}
            ]
            for h_data in hotels_data:
                if not Hotel.query.get(h_data['id']): db.session.add(Hotel(**h_data))
            db.session.commit()

            templates_data = [
                {'id': 1, 'name': 'Солнечный Египет: все включено', 'hotel_id': 1, 'duration_days': 7},
                {'id': 2, 'name': 'Древний Каир и Пирамиды', 'hotel_id': 2, 'duration_days': 3},
                {'id': 3, 'name': 'Романтический уикенд в Париже', 'hotel_id': 3, 'duration_days': 3},
                {'id': 4, 'name': 'Пляжные приключения в Таиланде', 'hotel_id': 5, 'duration_days': 10},
                {'id': 5, 'name': 'Вечный город: Римские каникулы', 'hotel_id': 7, 'duration_days': 4},
                {'id': 6, 'name': 'Сердце двух континентов: Стамбул', 'hotel_id': 9, 'duration_days': 4},
                {'id': 7, 'name': 'Йога-ретрит на Бали', 'hotel_id': 8, 'duration_days': 14},
                {'id': 8, 'name': 'Неоновый Токио и гора Фудзи', 'hotel_id': 10, 'duration_days': 6},
                {'id': 9, 'name': 'Романтика венецианских каналов', 'hotel_id': 11, 'duration_days': 4},
                {'id': 10, 'name': 'Дух самураев: путешествие в Киото', 'hotel_id': 13, 'duration_days': 5}
            ]
            for tt_data in templates_data:
                if not TourTemplate.query.get(tt_data['id']): db.session.add(TourTemplate(**tt_data))
            db.session.commit()
            print("Справочники успешно наполнены.")

        db.session.commit()
