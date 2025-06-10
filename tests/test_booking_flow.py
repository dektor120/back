from models import Booking, User


def test_full_booking_flow(client):
    client.emit('login', {'login': 'admin', 'password': 'admin'})
    received = client.get_received()
    token = received[0]['args'][0]['token']
    user = User.query.filter_by(login='admin').first()

    tour_id_to_book = 1
    client.emit('check_availability', {
        'token': token,
        'scheduled_tour_id': tour_id_to_book,
        'people': 2
    })
    received = client.get_received()
    assert received[0]['name'] == 'availability_response'
    assert received[0]['args'][0]['success'] is True

    booking_details = {'scheduled_tour_id': tour_id_to_book}
    travelers_data = [
        {'fullName': 'Иван Иванов', 'passport': '1234 567890'},
        {'fullName': 'Мария Иванова', 'passport': '4321 098765'}
    ]
    client.emit('create_booking', {
        'token': token,
        'booking_details': booking_details,
        'travelers': travelers_data
    })

    received = client.get_received()
    assert received[0]['name'] == 'booking_response'
    assert received[0]['args'][0]['success'] is True

    booking = Booking.query.filter_by(user_id=user.id).first()
    assert booking is not None
    assert booking.scheduled_tour_id == tour_id_to_book
    assert booking.number_of_people == len(travelers_data)
    assert len(booking.travelers) == len(travelers_data)