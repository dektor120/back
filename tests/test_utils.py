import pytest
from utils import is_valid_login, is_valid_password, is_valid_email

@pytest.mark.parametrize("login, expected", [
    ("valid_login_123", True),
    ("short", False),
    ("invalid-char", False),
    ("a_very_long_login_name_that_is_not_valid", False),
    ("РусскийЛогин", False)
])
def test_is_valid_login(login, expected):
    assert is_valid_login(login) == expected

@pytest.mark.parametrize("password, expected", [
    ("123456", True),
    ("long_strong_password", True),
    ("12345", False),
    ("", False)
])
def test_is_valid_password(password, expected):
    assert is_valid_password(password) == expected

@pytest.mark.parametrize("email, expected", [
    ("test@example.com", True),
    ("test.test@example.co.uk", True),
    ("invalid-email", False),
    ("test@.com", False),
    ("test@domain.", False)
])
def test_is_valid_email(email, expected):
    assert is_valid_email(email) == expected