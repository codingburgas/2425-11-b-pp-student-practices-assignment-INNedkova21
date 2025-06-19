import pytest

from HandwrittenDigitRecognizer import create_app, db
from HandwrittenDigitRecognizer.config import TestingConfig

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()


def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'Digit Recognizer' in response.data.decode('utf-8')


def test_home_route(client):
    response = client.get('/home')
    assert response.status_code == 200
    assert 'Начало' in response.data.decode('utf-8')