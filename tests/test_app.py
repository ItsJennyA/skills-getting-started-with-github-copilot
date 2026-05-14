"""
FastAPI backend tests for Mergington High School Activities API

Uses the AAA (Arrange-Act-Assert) pattern for clear test structure.
Each test isolates activities data to prevent cross-test pollution.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import create_app


@pytest.fixture
def test_activities():
    """Fixture: Minimal test activities for isolated testing"""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 2,
            "participants": ["alice@test.edu", "bob@test.edu"]
        },
        "Coding Club": {
            "description": "Learn programming fundamentals",
            "schedule": "Tuesdays, 4:00 PM - 5:00 PM",
            "max_participants": 20,
            "participants": []
        }
    }


@pytest.fixture
def client(test_activities):
    """Fixture: Create test client with isolated test activities"""
    app = create_app(activities=test_activities)
    return TestClient(app)


class TestGetRoot:
    """Test suite for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """
        Arrange: GET request to /
        Act: Send request
        Assert: Verify redirect to /static/index.html
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_all_activities_returns_list(self, client):
        """
        Arrange: Two test activities in the database
        Act: GET /activities
        Assert: Returns all activities with correct structure
        """
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Coding Club" in data
        assert len(data) == 2

    def test_get_activities_includes_participants(self, client):
        """
        Arrange: Activity with existing participants
        Act: GET /activities
        Assert: Response includes participants list
        """
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert "participants" in chess_club
        assert chess_club["participants"] == ["alice@test.edu", "bob@test.edu"]

    def test_get_activities_includes_activity_details(self, client):
        """
        Arrange: Activities with various fields
        Act: GET /activities
        Assert: Response includes all required fields
        """
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert chess_club["description"]
        assert chess_club["schedule"]
        assert chess_club["max_participants"] == 2


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """
        Arrange: New participant email and empty activity
        Act: POST signup request
        Assert: Participant added and success message returned
        """
        # Arrange
        activity_name = "Coding Club"
        email = "charlie@test.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_existing_participant_fails(self, client):
        """
        Arrange: Participant already registered for activity
        Act: POST signup request with same email
        Assert: Returns 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "alice@test.edu"  # Already registered

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """
        Arrange: Activity name that doesn't exist
        Act: POST signup request for nonexistent activity
        Assert: Returns 404 error
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "david@test.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_updates_participant_list(self, client):
        """
        Arrange: Activity with initial participant count
        Act: POST signup request and then GET activities
        Assert: Participant list is updated
        """
        # Arrange
        activity_name = "Coding Club"
        email = "eve@test.edu"

        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200

        # Act - Fetch activities
        get_response = client.get("/activities")

        # Assert
        data = get_response.json()
        coding_club = data["Coding Club"]
        assert email in coding_club["participants"]
        assert len(coding_club["participants"]) == 1


class TestUnregisterFromActivity:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_success(self, client):
        """
        Arrange: Participant registered for activity
        Act: DELETE unregister request
        Assert: Participant removed and success message returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "alice@test.edu"  # Already registered

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """
        Arrange: Participant not registered for activity
        Act: DELETE unregister request for unregistered email
        Assert: Returns 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@test.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """
        Arrange: Activity name that doesn't exist
        Act: DELETE unregister request for nonexistent activity
        Assert: Returns 404 error
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "frank@test.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_updates_participant_list(self, client):
        """
        Arrange: Participant registered for activity
        Act: DELETE unregister request and then GET activities
        Assert: Participant list is updated
        """
        # Arrange
        activity_name = "Chess Club"
        email = "alice@test.edu"
        initial_participants = ["alice@test.edu", "bob@test.edu"]

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200

        # Act - Fetch activities
        get_response = client.get("/activities")

        # Assert
        data = get_response.json()
        chess_club = data["Chess Club"]
        assert email not in chess_club["participants"]
        assert "bob@test.edu" in chess_club["participants"]
        assert len(chess_club["participants"]) == 1


class TestActivityIsolation:
    """Test suite to verify test isolation (no cross-test pollution)"""

    def test_each_test_gets_fresh_activities(self, test_activities):
        """
        Arrange: Create two clients with test_activities fixture
        Act: Modify activities from first client
        Assert: Second client has fresh unmodified activities
        """
        # Arrange
        app1 = create_app(activities=test_activities)
        client1 = TestClient(app1)
        
        # Create a separate activities dict for second app
        fresh_activities = {
            "Chess Club": {
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 2,
                "participants": ["alice@test.edu", "bob@test.edu"]
            },
            "Coding Club": {
                "description": "Learn programming fundamentals",
                "schedule": "Tuesdays, 4:00 PM - 5:00 PM",
                "max_participants": 20,
                "participants": []
            }
        }
        app2 = create_app(activities=fresh_activities)
        client2 = TestClient(app2)

        # Act - Modify through client1
        client1.post(
            "/activities/Coding Club/signup",
            params={"email": "participant@test.edu"}
        )

        # Assert - client2 has fresh data
        response1 = client1.get("/activities")
        response2 = client2.get("/activities")

        data1 = response1.json()
        data2 = response2.json()

        assert len(data1["Coding Club"]["participants"]) == 1
        assert len(data2["Coding Club"]["participants"]) == 0
