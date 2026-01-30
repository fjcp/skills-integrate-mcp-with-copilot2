"""
Simple storage layer for activities and participants.
- Uses SQLite (data/activities.db) by default.
- Seeds initial data from data/activities.json if DB is missing.
- Provides helper functions for API use: get_activities, get_activity, add_participant, remove_participant.
"""
from pathlib import Path
import sqlite3
import json
from typing import Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "activities.db"
SEED_JSON = Path(__file__).parent.parent / "data" / "activities.json"

_schema = """
CREATE TABLE IF NOT EXISTS activities (
    name TEXT PRIMARY KEY,
    description TEXT,
    schedule TEXT,
    max_participants INTEGER
);

CREATE TABLE IF NOT EXISTS participants (
    activity_name TEXT,
    email TEXT,
    PRIMARY KEY (activity_name, email),
    FOREIGN KEY (activity_name) REFERENCES activities(name) ON DELETE CASCADE
);
"""


def _connect():
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _connect()
    cur = conn.cursor()
    cur.executescript(_schema)
    conn.commit()
    conn.close()


def _seed_from_json():
    if not SEED_JSON.exists():
        return
    with open(SEED_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    conn = _connect()
    cur = conn.cursor()
    for name, info in data.items():
        info = info.get('info', {})
        stats = info if isinstance(info, dict) else {}
        description = info.get('description', '') if isinstance(info, dict) else ''
        schedule = info.get('schedule', '') if isinstance(info, dict) else ''
        maxp = info.get('max_participants', None) or 9999
        try:
            cur.execute('INSERT OR IGNORE INTO activities (name, description, schedule, max_participants) VALUES (?,?,?,?)',
                        (name, description, schedule, int(maxp)))
        except Exception:
            continue
    conn.commit()
    conn.close()


def ensure_db():
    """Ensure DB initialized and seeded if empty."""
    _init_db()
    # If activities table empty, try seed
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as c FROM activities')
    count = cur.fetchone()['c']
    conn.close()
    if count == 0:
        _seed_from_json()


# API

def get_activities() -> Dict[str, Dict]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM activities')
    acts = {}
    for row in cur.fetchall():
        name = row['name']
        acts[name] = {
            'description': row['description'],
            'schedule': row['schedule'],
            'max_participants': row['max_participants'],
            'participants': []
        }
    if acts:
        cur.execute('SELECT activity_name, email FROM participants')
        for row in cur.fetchall():
            acts[row['activity_name']]['participants'].append(row['email'])
    conn.close()
    return acts


def get_activity(activity_name: str) -> Optional[Dict]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM activities WHERE name = ?', (activity_name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    act = {'description': row['description'], 'schedule': row['schedule'], 'max_participants': row['max_participants'], 'participants': []}
    cur.execute('SELECT email FROM participants WHERE activity_name = ?', (activity_name,))
    act['participants'] = [r['email'] for r in cur.fetchall()]
    conn.close()
    return act


class StorageError(Exception):
    pass


def add_participant(activity_name: str, email: str) -> None:
    conn = _connect()
    cur = conn.cursor()
    # Check activity exists
    cur.execute('SELECT max_participants FROM activities WHERE name = ?', (activity_name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise StorageError('Activity not found')
    maxp = row['max_participants']
    cur.execute('SELECT COUNT(*) as c FROM participants WHERE activity_name = ?', (activity_name,))
    c = cur.fetchone()['c']
    if c >= maxp:
        conn.close()
        raise StorageError('Activity full')
    try:
        cur.execute('INSERT INTO participants (activity_name, email) VALUES (?,?)', (activity_name, email))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise StorageError('Student already signed up')
    conn.close()


def remove_participant(activity_name: str, email: str) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('DELETE FROM participants WHERE activity_name = ? AND email = ?', (activity_name, email))
    conn.commit()
    conn.close()
