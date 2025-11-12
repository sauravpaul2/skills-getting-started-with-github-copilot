"""Test suite for the Mergington High School Activities API."""
import pytest
from fastapi import HTTPException


def test_get_activities(client):
    """Test GET /activities returns all activities."""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) > 0
    # Verify structure of an activity
    first_activity = list(activities.values())[0]
    assert "description" in first_activity
    assert "schedule" in first_activity
    assert "max_participants" in first_activity
    assert "participants" in first_activity
    assert isinstance(first_activity["participants"], list)


def test_signup_success(client, reset_activities):
    """Test successful signup for an activity."""
    email = "student@test.com"
    activity = "Chess Club"
    
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    assert activity in result["message"]


def test_signup_already_signed_up(client, reset_activities):
    """Test signup fails if student is already signed up."""
    email = "michael@mergington.edu"  # Already in Chess Club
    activity = "Chess Club"
    
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 400
    result = response.json()
    assert "already signed up" in result["detail"].lower()


def test_signup_activity_full(client, reset_activities):
    """Test signup fails if activity is at max capacity."""
    activity = "Tennis Club"
    
    # Get current participants
    response = client.get("/activities")
    current_count = len(response.json()[activity]["participants"])
    max_participants = response.json()[activity]["max_participants"]
    
    # Only test if activity is full
    if current_count >= max_participants:
        new_email = "new.student@test.com"
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": new_email}
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()


def test_signup_nonexistent_activity(client):
    """Test signup fails for nonexistent activity."""
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "student@test.com"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unregister_success(client, reset_activities):
    """Test successful unregister from an activity."""
    email = "michael@mergington.edu"  # Already in Chess Club
    activity = "Chess Club"
    
    response = client.post(
        f"/activities/{activity}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    
    # Verify participant was removed
    response = client.get("/activities")
    assert email not in response.json()[activity]["participants"]


def test_unregister_not_signed_up(client, reset_activities):
    """Test unregister fails if student is not signed up."""
    email = "not.signed.up@test.com"
    activity = "Chess Club"
    
    response = client.post(
        f"/activities/{activity}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"].lower()


def test_unregister_nonexistent_activity(client):
    """Test unregister fails for nonexistent activity."""
    response = client.post(
        "/activities/Nonexistent Activity/unregister",
        params={"email": "student@test.com"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_then_unregister_flow(client, reset_activities):
    """Test complete flow: signup then unregister."""
    email = "flow.test@test.com"
    activity = "Drama Club"
    
    # Signup
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify present
    response = client.get("/activities")
    assert email in response.json()[activity]["participants"]
    initial_count = len(response.json()[activity]["participants"])
    
    # Unregister
    response = client.post(
        f"/activities/{activity}/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify removed
    response = client.get("/activities")
    assert email not in response.json()[activity]["participants"]
    final_count = len(response.json()[activity]["participants"])
    assert final_count == initial_count - 1


def test_multiple_signups(client, reset_activities):
    """Test multiple different students can sign up for same activity."""
    activity = "Science Club"
    emails = ["student1@test.com", "student2@test.com", "student3@test.com"]
    
    for email in emails:
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify all are present
    response = client.get("/activities")
    participants = response.json()[activity]["participants"]
    for email in emails:
        assert email in participants


def test_availability_updates_after_signup(client, reset_activities):
    """Test that availability decreases after signup."""
    activity = "Basketball Team"
    email = "bball.student@test.com"
    
    # Get initial availability
    response = client.get("/activities")
    initial_max = response.json()[activity]["max_participants"]
    initial_count = len(response.json()[activity]["participants"])
    initial_available = initial_max - initial_count
    
    # Signup
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Check availability decreased
    response = client.get("/activities")
    new_count = len(response.json()[activity]["participants"])
    new_available = initial_max - new_count
    assert new_available == initial_available - 1
    assert new_count == initial_count + 1
