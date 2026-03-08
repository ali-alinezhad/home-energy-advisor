import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_file = tmp_path / "test_home_energy.db"
    engine = create_engine(
        f"sqlite:///{database_file}", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def valid_home_payload():
    return {
        "size": 120,
        "year_built": 1985,
        "heating_type": "gas",
        "insulation_level": "medium",
    }


def create_home(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/homes", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_home(client: TestClient, valid_home_payload: dict):
    data = create_home(client, valid_home_payload)

    assert data["size"] == 120
    assert data["year_built"] == 1985
    assert data["heating_type"] == "gas"
    assert data["latest_advice"] is None
    assert data["advice_generated_at"] is None
    assert "id" in data


def test_get_home_returns_saved_profile(
    client: TestClient, valid_home_payload: dict
):
    created = create_home(client, valid_home_payload)

    response = client.get(f"/api/homes/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_create_home_rejects_invalid_payload(
    client: TestClient, valid_home_payload: dict
):
    invalid_payload = {**valid_home_payload, "year_built": 1700}

    response = client.post("/api/homes", json=invalid_payload)

    assert response.status_code == 422


def test_generate_advice_returns_fresh_structured_recommendations(
    client: TestClient, valid_home_payload: dict, monkeypatch
):
    created = create_home(client, valid_home_payload)
    llm_call_count = {"count": 0}
    expected_home_age = datetime.now().year - valid_home_payload["year_built"]

    def fake_generate_advice(prompt: str) -> str:
        llm_call_count["count"] += 1
        assert "Year built: 1985" in prompt
        assert f"Approximate home age: {expected_home_age} years" in prompt
        return json.dumps(
            {
                "recommendations": [
                    {
                        "title": f"Seal drafts {llm_call_count['count']}",
                        "description": (
                            "Seal windows and doors to reduce avoidable "
                            "heating losses quickly."
                        ),
                        "priority": "high",
                    },
                    {
                        "title": "Improve loft insulation",
                        "description": (
                            "Add insulation in the loft to reduce heat "
                            "escaping through the roof."
                        ),
                        "priority": "medium",
                    },
                    {
                        "title": "Install smart controls",
                        "description": (
                            "Use programmable heating controls to cut "
                            "runtime when rooms are empty."
                        ),
                        "priority": "low",
                    },
                ]
            }
        )

    monkeypatch.setattr(
        "app.services.advice.generate_advice", fake_generate_advice
    )

    first_response = client.post(f"/api/homes/{created['id']}/advice")
    second_response = client.post(f"/api/homes/{created['id']}/advice")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(first_response.json()["recommendations"]) == 3
    assert first_response.json() != second_response.json()
    assert llm_call_count["count"] == 2


def test_get_home_includes_latest_saved_advice(
    client: TestClient, valid_home_payload: dict, monkeypatch
):
    created = create_home(client, valid_home_payload)

    def fake_generate_advice(_: str) -> str:
        return json.dumps(
            {
                "recommendations": [
                    {
                        "title": "Fresh latest advice",
                        "description": (
                            "Show the most recently generated advice."
                        ),
                        "priority": "high",
                    },
                    {
                        "title": "Secondary improvement",
                        "description": "Improve insulation where practical.",
                        "priority": "medium",
                    },
                    {
                        "title": "Control schedules",
                        "description": "Cut unnecessary heating runtime.",
                        "priority": "low",
                    },
                ]
            }
        )

    monkeypatch.setattr(
        "app.services.advice.generate_advice", fake_generate_advice
    )

    advice_response = client.post(f"/api/homes/{created['id']}/advice")
    home_response = client.get(f"/api/homes/{created['id']}")

    assert advice_response.status_code == 200
    assert home_response.status_code == 200
    assert home_response.json()["latest_advice"] == advice_response.json()
    assert home_response.json()["advice_generated_at"] is not None
