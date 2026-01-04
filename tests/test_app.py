from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_unregister_cycle():
    activity = "Chess Club"
    test_email = "pytest_user@example.com"

    # Ensure email is not present
    resp = client.get("/activities")
    assert resp.status_code == 200
    activities = resp.json()
    if test_email in activities[activity]["participants"]:
        # cleanup if leftover
        client.delete(f"/activities/{activity}/participants?email={test_email}")

    # Sign up
    resp = client.post(f"/activities/{activity}/signup?email={test_email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Verify it appears in GET
    resp = client.get("/activities")
    activities = resp.json()
    assert test_email in activities[activity]["participants"]

    # Unregister
    resp = client.delete(f"/activities/{activity}/participants?email={test_email}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Verify it's gone
    resp = client.get("/activities")
    activities = resp.json()
    assert test_email not in activities[activity]["participants"]


def test_unregister_nonexistent_returns_404():
    activity = "Programming Class"
    email = "no-such-user@example.com"

    # Ensure not present
    resp = client.get("/activities")
    activities = resp.json()
    assert email not in activities[activity]["participants"]

    # Attempt to delete
    resp = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp.status_code == 404
