from PIL import Image
import io
import numpy as np
import pytest

from HandwrittenDigitRecognizer import db
from HandwrittenDigitRecognizer.ai.routes import leaky_relu, predict_digit
from HandwrittenDigitRecognizer.app import create_app
from HandwrittenDigitRecognizer.config import TestingConfig


def test_leaky_relu_positive():
    x = np.array([1, 2, 3])
    result = leaky_relu(x)
    assert np.all(result == x)

def test_leaky_relu_negative():
    x = np.array([-1, -2, -3])
    result = leaky_relu(x)
    assert np.allclose(result, x * 0.01)

def test_leaky_relu_mixed():
    x = np.array([-1, 0, 1])
    result = leaky_relu(x)
    expected = np.array([-0.01, 0, 1])
    assert np.allclose(result, expected)

@pytest.fixture(autouse=True)
def mock_weights(monkeypatch):
    monkeypatch.setattr('HandwrittenDigitRecognizer.ai.routes.W1', np.ones((784, 10)))
    monkeypatch.setattr('HandwrittenDigitRecognizer.ai.routes.b1', np.zeros(10))
    monkeypatch.setattr('HandwrittenDigitRecognizer.ai.routes.W2', np.ones((10, 10)))
    monkeypatch.setattr('HandwrittenDigitRecognizer.ai.routes.b2', np.zeros(10))
    monkeypatch.setattr('HandwrittenDigitRecognizer.ai.routes.W3', np.ones((10, 10)))
    monkeypatch.setattr('HandwrittenDigitRecognizer.ai.routes.b3', np.zeros(10))

def test_predict_digit_output_shape():
    input_data = np.ones((1, 784))
    pred, conf = predict_digit(input_data)
    assert isinstance(pred, int)
    assert isinstance(conf, float)
    assert 0 <= pred < 10
    assert 0.0 <= conf <= 1.0


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        yield client

def test_upload_no_file(client):
    response = client.post('/upload', data={})
    assert response.status_code == 200
    assert b'<form method="POST" action="/upload"' in response.data


def test_upload_invalid_file(client):
    data = {
        'image': (io.BytesIO(b"notanimage"), 'test.txt')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert b'<form method="POST" action="/upload"' in response.data
    assert b'Confidence' not in response.data

def test_upload_valid_png(client, monkeypatch):
    img = Image.new('L', (28, 28), color=0)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    byte_arr.seek(0)

    class DummyUser:
        ID = 1

    monkeypatch.setattr('HandwrittenDigitRecognizer.ai.routes.current_user', DummyUser())
    monkeypatch.setattr('HandwrittenDigitRecognizer.ai.routes.predict_digit', lambda x: (7, 0.95))

    data = {
        'image': (byte_arr, 'digit.png')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert b'7' in response.data or b'Confidence' in response.data