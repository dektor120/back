from datetime import datetime
from extensions import db




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(80), nullable=False, default='client')
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade="all, delete-orphan")


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(200), nullable=False)
    birth_date = db.Column(db.String(20), nullable=False)
    contact_phone_encrypted = db.Column(db.String(500), nullable=False)


class ContactRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    phone_encrypted = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)


class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)


class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    stars = db.Column(db.Integer, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)


class TourTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)


class ScheduledTour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tour_template_id = db.Column(db.Integer, db.ForeignKey('tour_template.id'), nullable=False)
    start_date = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    max_seats = db.Column(db.Integer, nullable=False)
    bookings = db.relationship('Booking', backref='scheduled_tour', cascade="all, delete-orphan")


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scheduled_tour_id = db.Column(db.Integer, db.ForeignKey('scheduled_tour.id'), nullable=False)
    number_of_people = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='pending_payment')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    travelers = db.relationship('BookingTraveler', backref='booking', cascade="all, delete-orphan")


class BookingTraveler(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    passport_data_encrypted = db.Column(db.String(500), nullable=False)
    phone_encrypted = db.Column(db.String(500))


class SavedTraveler(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    passport_data_encrypted = db.Column(db.String(500), nullable=False)
    phone_encrypted = db.Column(db.String(500))
