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


def test_duplicate_signup_returns_400():
    activity = "Chess Club"
    test_email = "duplicate_test@example.com"

    # Cleanup if present
    resp = client.get("/activities")
    activities = resp.json()
    if test_email in activities[activity]["participants"]:
        client.delete(f"/activities/{activity}/participants?email={test_email}")

    # First signup should succeed
    resp = client.post(f"/activities/{activity}/signup?email={test_email}")
    assert resp.status_code == 200

    # Second signup should fail with 400
    resp = client.post(f"/activities/{activity}/signup?email={test_email}")
    assert resp.status_code == 400
    assert "already signed up" in resp.json().get("detail", "").lower()

    # Cleanup
    client.delete(f"/activities/{activity}/participants?email={test_email}")


def test_signup_full_activity_returns_400():
    activity = "Tennis Club"
    
    # Get current state
    resp = client.get("/activities")
    activities = resp.json()
    max_participants = activities[activity]["max_participants"]
    current_participants = activities[activity]["participants"].copy()
    
    # Fill activity to capacity
    test_emails = []
    for i in range(max_participants - len(current_participants)):
        test_email = f"capacity_test_{i}@example.com"
        test_emails.append(test_email)
        resp = client.post(f"/activities/{activity}/signup?email={test_email}")
        assert resp.status_code == 200
    
    # Verify activity is now full
    resp = client.get("/activities")
    activities = resp.json()
    assert len(activities[activity]["participants"]) == max_participants
    
    # Try to add one more - should fail
    overflow_email = "overflow_test@example.com"
    resp = client.post(f"/activities/{activity}/signup?email={overflow_email}")
    assert resp.status_code == 400
    assert "full" in resp.json().get("detail", "").lower()
    
    # Cleanup
    for email in test_emails:
        client.delete(f"/activities/{activity}/participants?email={email}")


