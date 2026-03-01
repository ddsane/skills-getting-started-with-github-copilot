"""
Tests for the Mergington High School Activities API.
Uses the AAA (Arrange-Act-Assert) pattern for clarity.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient instance for each test."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Reset activities to a known state before each test.
    Yields control to the test, then resets after.
    """
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy(),
        }
        for name, details in activities.items()
    }

    yield

    # Restore original state
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Arrange: No setup needed
        Act: GET /activities
        Assert: Returns 200 with all activities
        """
        response = client.get("/activities")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Arrange: No setup needed
        Act: GET /activities
        Assert: Each activity has required fields
        """
        response = client.get("/activities")
        data = response.json()

        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_shows_current_participants(self, client, reset_activities):
        """Arrange: No setup needed
        Act: GET /activities
        Assert: Participants list matches data
        """
        response = client.get("/activities")
        data = response.json()

        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client, reset_activities):
        """Arrange: No setup needed
        Act: GET /
        Assert: Redirect to /static/index.html (follow_redirects=False to see redirect)
        """
        response = client.get("/", follow_redirects=False)

        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client, reset_activities):
        """Arrange: New email not yet signed up
        Act: POST /activities/Chess Club/signup
        Assert: Returns 200 with success message and participant added
        """
        email = "newstudent@mergington.edu"

        response = client.post(
            f"/activities/Chess Club/signup?email={email}",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert email in activities["Chess Club"]["participants"]

    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """Arrange: Email already signed up for activity
        Act: POST /activities/Chess Club/signup with duplicate email
        Assert: Returns 400 with error detail
        """
        email = "michael@mergington.edu"  # Already in Chess Club

        response = client.post(
            f"/activities/Chess Club/signup?email={email}",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Arrange: Activity does not exist
        Act: POST /activities/Fake Activity/signup
        Assert: Returns 404 with error detail
        """
        response = client.post(
            "/activities/Fake%20Activity/signup?email=student@mergington.edu",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_adds_to_participants_list(self, client, reset_activities):
        """Arrange: Get initial participant count
        Act: POST signup for new student
        Assert: Participant count increases by 1
        """
        initial_count = len(activities["Tennis Club"]["participants"])
        new_email = "newtennis@mergington.edu"

        client.post(f"/activities/Tennis Club/signup?email={new_email}")

        assert len(activities["Tennis Club"]["participants"]) == initial_count + 1
        assert new_email in activities["Tennis Club"]["participants"]

    def test_signup_different_activity_same_email_succeeds(self, client, reset_activities):
        """Arrange: Email signed up for one activity
        Act: POST same email to different activity
        Assert: Succeeds (same email can signup for multiple activities)
        """
        email = "michael@mergington.edu"  # Already in Chess Club

        response = client.post(
            f"/activities/Basketball Team/signup?email={email}",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert email in activities["Basketball Team"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_successful(self, client, reset_activities):
        """Arrange: Email is signed up for activity
        Act: DELETE /activities/Chess Club/signup
        Assert: Returns 200 with success message and participant removed
        """
        email = "michael@mergington.edu"  # In Chess Club
        assert email in activities["Chess Club"]["participants"]

        response = client.delete(
            f"/activities/Chess Club/signup?email={email}",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_user_not_registered_returns_400(self, client, reset_activities):
        """Arrange: Email not signed up for activity
        Act: DELETE /activities/Chess Club/signup with non-registered email
        Assert: Returns 400 with error detail
        """
        email = "notstudent@mergington.edu"

        response = client.delete(
            f"/activities/Chess Club/signup?email={email}",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()

    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Arrange: Activity does not exist
        Act: DELETE /activities/Fake Activity/signup
        Assert: Returns 404 with error detail
        """
        response = client.delete(
            "/activities/Fake%20Activity/signup?email=student@mergington.edu",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_unregister_removes_from_participants_list(self, client, reset_activities):
        """Arrange: Get initial participant count
        Act: DELETE unregister student
        Assert: Participant count decreases by 1
        """
        email = "james@mergington.edu"  # In Tennis Club
        initial_count = len(activities["Tennis Club"]["participants"])
        assert email in activities["Tennis Club"]["participants"]

        client.delete(f"/activities/Tennis Club/signup?email={email}")

        assert len(activities["Tennis Club"]["participants"]) == initial_count - 1
        assert email not in activities["Tennis Club"]["participants"]

    def test_unregister_then_signup_again_succeeds(self, client, reset_activities):
        """Arrange: Email is registered
        Act: DELETE unregister, then POST signup again
        Assert: Both operations succeed
        """
        email = "michael@mergington.edu"

        # Unregister
        response1 = client.delete(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        assert email not in activities["Chess Club"]["participants"]

        # Sign up again
        response2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
