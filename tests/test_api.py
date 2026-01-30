from fastapi.testclient import TestClient
from src.app import app
from src import storage

client = TestClient(app)


def setup_module(module):
    # Ensure DB seeded
    storage.ensure_db()


def test_get_activities():
    r = client.get('/activities')
    assert r.status_code == 200
    data = r.json()
    assert 'Chess Club' in data


def test_signup_and_unregister():
    email = 'integration_test@example.com'
    activity = 'Chess Club'

    # Ensure not signed up
    client.delete(f'/activities/{activity}/unregister', params={'email': email})

    # Signup
    r1 = client.post(f'/activities/{activity}/signup', params={'email': email})
    assert r1.status_code == 200
    assert 'Signed up' in r1.json().get('message', '')

    # Duplicate signup -> 400
    r2 = client.post(f'/activities/{activity}/signup', params={'email': email})
    assert r2.status_code == 400

    # Unregister
    r3 = client.delete(f'/activities/{activity}/unregister', params={'email': email})
    assert r3.status_code == 200
    assert 'Unregistered' in r3.json().get('message', '')
