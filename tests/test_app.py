import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


INITIAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities(monkeypatch):
    monkeypatch.setattr(app_module, "activities", copy.deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_root_redirects_to_frontend(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_available_activities(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.json()[expected_activity]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    # Arrange
    activity = "Art Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[activity]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email(client):
    # Arrange
    activity = "Art Club"

    # Act
    response = client.post(f"/activities/{activity}/signup")

    # Assert
    assert response.status_code == 422


def test_signup_supports_activity_names_with_spaces(client):
    # Arrange
    activity = "Programming Class"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in app_module.activities[activity]["participants"]


def test_unregister_removes_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in app_module.activities[activity]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    activity = "Art Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_requires_email(client):
    # Arrange
    activity = "Art Club"

    # Act
    response = client.delete(f"/activities/{activity}/signup")

    # Assert
    assert response.status_code == 422


def test_signup_is_visible_when_activities_are_fetched(client):
    # Arrange
    activity = "Art Club"
    email = "student@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert email in activities_response.json()[activity]["participants"]