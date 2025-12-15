"""
Tests for the Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        name: {**details, "participants": details["participants"].copy()}
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"].copy()


def test_root_redirect(client):
    """Test that root redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Soccer Team" in data
    assert "Basketball Team" in data
    assert "max_participants" in data["Soccer Team"]
    assert "participants" in data["Soccer Team"]


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Soccer%20Team/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@mergington.edu" in data["message"]
    assert "Soccer Team" in data["message"]
    
    # Verify participant was added
    assert "test@mergington.edu" in activities["Soccer Team"]["participants"]


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    response = client.post(
        "/activities/Invalid%20Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_already_registered(client):
    """Test signup when student is already registered"""
    email = "liam@mergington.edu"  # Already in Soccer Team
    response = client.post(
        f"/activities/Soccer%20Team/signup?email={email}"
    )
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"].lower()


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    email = "liam@mergington.edu"  # Already in Soccer Team
    
    # Verify participant exists before unregistering
    assert email in activities["Soccer Team"]["participants"]
    
    response = client.delete(
        f"/activities/Soccer%20Team/unregister?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert "Soccer Team" in data["message"]
    
    # Verify participant was removed
    assert email not in activities["Soccer Team"]["participants"]


def test_unregister_activity_not_found(client):
    """Test unregister from non-existent activity"""
    response = client.delete(
        "/activities/Invalid%20Activity/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_unregister_not_registered(client):
    """Test unregister when student is not registered"""
    email = "notregistered@mergington.edu"
    response = client.delete(
        f"/activities/Soccer%20Team/unregister?email={email}"
    )
    assert response.status_code == 400
    data = response.json()
    assert "not signed up" in data["detail"].lower()


def test_signup_and_unregister_workflow(client):
    """Test complete signup and unregister workflow"""
    email = "workflow@mergington.edu"
    activity = "Drama Club"
    
    # Initial state - not registered
    assert email not in activities[activity]["participants"]
    
    # Sign up
    response = client.post(
        f"/activities/{activity}/signup?email={email}"
    )
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    
    # Unregister
    response = client.delete(
        f"/activities/{activity}/unregister?email={email}"
    )
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]


def test_multiple_activities_signup(client):
    """Test signing up for multiple activities"""
    email = "multi@mergington.edu"
    
    # Sign up for Soccer Team
    response = client.post(
        f"/activities/Soccer%20Team/signup?email={email}"
    )
    assert response.status_code == 200
    assert email in activities["Soccer Team"]["participants"]
    
    # Sign up for Drama Club
    response = client.post(
        f"/activities/Drama%20Club/signup?email={email}"
    )
    assert response.status_code == 200
    assert email in activities["Drama Club"]["participants"]
    
    # Verify both registrations exist
    assert email in activities["Soccer Team"]["participants"]
    assert email in activities["Drama Club"]["participants"]
