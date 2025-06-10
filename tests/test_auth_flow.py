from models import User


def test_registration_and_login_flow(client):
    client.emit('register', {
        'login': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })

    received = client.get_received()
    assert len(received) == 1
    assert received[0]['name'] == 'register_response'
    assert received[0]['args'][0]['success'] is True

    user = User.query.filter_by(login='testuser').first()
    assert user is not None
    assert user.email == 'test@example.com'

    client.emit('login', {
        'login': 'testuser',
        'password': 'password123'
    })

    received = client.get_received()
    assert len(received) == 1
    assert received[0]['name'] == 'login_response'
    login_data = received[0]['args'][0]
    assert login_data['success'] is True
    assert 'token' in login_data
    assert login_data['token'] is not None
