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
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        "Basketball Club": {
            "description": "Play competitive and recreational basketball",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"],
        },
        "Tennis Team": {
            "description": "Learn tennis skills and compete in matches",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["sarah@mergington.edu"],
        },
        "Art Club": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["grace@mergington.edu"],
        },
    }
    
    # Clear and restore
    activities.clear()
    activities.update(original_activities)
    yield
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_dict(self, client):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that activities list contains expected activity names"""
        response = client.get("/activities")
        data = response.json()
        assert "Basketball Club" in data
        assert "Tennis Team" in data
        assert "Art Club" in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "student@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(
            "/activities/Basketball Club/signup",
            params={"email": email}
        )
        
        response = client.get("/activities")
        activities_data = response.json()
        assert email in activities_data["Basketball Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test that signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email(self, client):
        """Test that signing up with duplicate email returns 400"""
        email = "james@mergington.edu"  # Already signed up for Basketball Club
        response = client.post(
            "/activities/Basketball Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Tennis Team/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball Club"]["participants"]
        assert email in data["Tennis Team"]["participants"]


class TestRootRedirect:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
