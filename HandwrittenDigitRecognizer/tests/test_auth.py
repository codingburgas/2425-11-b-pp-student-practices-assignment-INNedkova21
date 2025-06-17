import pytest
from flask import url_for
from HandwrittenDigitRecognizer.app import create_app, db
from HandwrittenDigitRecognizer.config import TestingConfig
from HandwrittenDigitRecognizer.models.user import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client


def test_register_success(client):
    response = client.post('/register', data={
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'User'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Провери имейла си за потвърждение' in response.data.decode('utf-8')


def test_register_password_mismatch(client):
    response = client.post('/register', data={
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'mismatch@example.com',
        'password': 'pass1',
        'confirm_password': 'pass2',
    })
    assert 'Паролите не съвпадат' in response.data.decode('utf-8')


def test_login_unconfirmed_email(client, app):
    with app.app_context():
        user = User(
            FirstName='Ana',
            LastName='Ivanova',
            Email='ana@example.com',
            Password=generate_password_hash('testpass'),
            Confirmed=False
        )
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', data={
        'email': 'ana@example.com',
        'password': 'testpass'
    }, follow_redirects=True)

    assert 'потвърдете своя имейл адрес' in response.data.decode('utf-8')


def test_login_success(client, app):
    with app.app_context():
        user = User(
            FirstName='Confirmed',
            LastName='User',
            Email='confirm@example.com',
            Password=generate_password_hash('testpass'),
            Confirmed=True
        )
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', data={
        'email': 'confirm@example.com',
        'password': 'testpass'
    }, follow_redirects=True)

    assert 'Успешно' in response.data or b'home' in response.data.decode('utf-8')

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()