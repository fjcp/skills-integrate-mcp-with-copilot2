import os
import tempfile
from src import storage


def setup_module(module):
    # Use a temporary DB path for tests
    storage.DB_PATH = os.path.join(tempfile.gettempdir(), 'test_activities.db')
    # Ensure clean DB
    try:
        os.remove(storage.DB_PATH)
    except Exception:
        pass
    storage.ensure_db()


def test_get_activities():
    acts = storage.get_activities()
    assert isinstance(acts, dict)
    assert 'Chess Club' in acts


def test_add_and_remove_participant():
    activity = 'Chess Club'
    email = 'testuser@example.com'
    # Ensure not present
    act = storage.get_activity(activity)
    if email in act.get('participants', []):
        storage.remove_participant(activity, email)

    # Add
    storage.add_participant(activity, email)
    act2 = storage.get_activity(activity)
    assert email in act2['participants']

    # Duplicate add should raise
    try:
        storage.add_participant(activity, email)
        assert False, 'Expected StorageError for duplicate signup'
    except storage.StorageError:
        pass

    # Remove
    storage.remove_participant(activity, email)
    act3 = storage.get_activity(activity)
    assert email not in act3['participants']
