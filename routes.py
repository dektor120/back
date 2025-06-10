from flask import Blueprint, render_template


pages = Blueprint('pages', __name__)


@pages.route('/')
def index():
    return render_template('index.html')


@pages.route('/tours')
def tours_page():
    return render_template('tours.html')


@pages.route('/hotels')
def hotels_page():
    return render_template('hotels.html')


@pages.route('/auth')
def auth_page():
    return render_template('auth.html')


@pages.route('/profile')
def profile_page():
    return render_template('profile.html')


@pages.route('/admin_dashboard')
def admin_dashboard_page():
    return render_template('admin_dashboard.html')


@pages.route('/services')
def services_page():
    return render_template('services.html')


@pages.route('/about')
def about_page():
    return render_template('about.html')