"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Persistent storage for activities
from src import storage

# Initialize DB and seed from data/activities.json if needed
storage.ensure_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    """Return all activities from persistent storage."""
    return storage.get_activities()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity using storage layer."""
    act = storage.get_activity(activity_name)
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    try:
        storage.add_participant(activity_name, email)
    except storage.StorageError as e:
        msg = str(e)
        if "already" in msg.lower():
            raise HTTPException(status_code=400, detail="Student is already signed up")
        if "full" in msg.lower():
            raise HTTPException(status_code=400, detail="Activity is full")
        raise HTTPException(status_code=400, detail=msg)

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity using storage."""
    act = storage.get_activity(activity_name)
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check if user is signed up
    if email not in act.get('participants', []):
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    storage.remove_participant(activity_name, email)
    return {"message": f"Unregistered {email} from {activity_name}"}
