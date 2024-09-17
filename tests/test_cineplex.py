import pytest
from cineplex.cineplex import Cineplex
import os
from dotenv import load_dotenv
import datetime

# Get secrets
load_dotenv()
username = os.environ["CINEPLEX_USERNAME"]
password = os.environ["CINEPLEX_PASSWORD"]
totp_secret = os.environ["CINEPLEX_TOTP_SECRET"]

# Avoid session has expired error when ran too often
# TODO: This is bad practice
good_cineplex = Cineplex()

# test valid login
def test_valid_login():
    good_cineplex.login(username, password, totp_secret)

# test login with wrong username & password
def test_invalid_login():
    cineplex = Cineplex()
    with pytest.raises(RuntimeError) as excinfo:
        cineplex.login("wrong", "wrong", "wrong")
    assert "InvalidCredentialsException" in str(excinfo)

# test login with empty username, password, and totp_secret
def test_empty_login():
    cineplex = Cineplex()
    with pytest.raises(RuntimeError) as excinfo:
        cineplex.login("", "", "")
    assert "IllegalArgumentException" in str(excinfo)

# test login with wrong username
def test_wrong_username():
    cineplex = Cineplex()
    with pytest.raises(RuntimeError) as excinfo:
        cineplex.login("wrong", password, totp_secret)
    assert "InvalidCredentialsException" in str(excinfo)

def test_empty_username():
    cineplex = Cineplex()
    with pytest.raises(RuntimeError) as excinfo:
        cineplex.login("", password, totp_secret)
    assert "IllegalArgumentException" in str(excinfo)

# test login with wrong password
def test_wrong_password():
    cineplex = Cineplex()
    with pytest.raises(RuntimeError) as excinfo:
        cineplex.login(username, "wrong", totp_secret)
    assert "InvalidCredentialsException" in str(excinfo)

# test login with empty password
def test_empty_password():
    cineplex = Cineplex()
    with pytest.raises(RuntimeError) as excinfo:
        cineplex.login(username, "", totp_secret)
    assert "IllegalArgumentException" in str(excinfo)

# test login with wrong totp secret
def test_wrong_totp_secret():
    cineplex = Cineplex()
    with pytest.raises(RuntimeError) as excinfo:
        cineplex.login(username, password, "wrong")
    assert "incorrect code" in str(excinfo.value)

def test_empty_totp_secret():
    cineplex = Cineplex()
    with pytest.raises(RuntimeError) as excinfo:
        cineplex.login(username, password, "")
    assert "incorrect code" in str(excinfo.value)

# get existing shift
def test_existant_shift():
    date = datetime.date(2024, 9, 15)
    (start_time, end_time) = good_cineplex.get_shift(date)
    assert start_time == datetime.time(17) # 5pm
    assert end_time == datetime.time(23) # 11pm

# get non-existant shift
def test_non_existant_shift():
    date = datetime.date(2024, 9, 16)
    result = good_cineplex.get_shift(date)
    assert result == None