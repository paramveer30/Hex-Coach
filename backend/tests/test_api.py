import pytest
from fastapi.testclient import TestClient

from hexcoach.api.main import HUMAN_SEAT, app, store
from hexcoach.engine import geometry as geo


@pytest.fixture
def client():
    store.sessions.clear()
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_geometry_matches_the_engine(client):
    data = client.get("/api/geometry").json()
    assert len(data["hexCenters"]) == 19
    assert len(data["vertexPositions"]) == 54
    assert len(data["edgeVertices"]) == 72
    assert data["hexVertices"][0] == list(geo.HEX_VERTICES[0])
    assert len(data["portEdges"]) == 9


def test_create_game(client):
    r = client.post("/api/games", json={})
    assert r.status_code == 201
    data = r.json()
    assert data["humanSeat"] == HUMAN_SEAT
    assert data["state"]["phase"] == "SETUP_SETTLEMENT"
    assert data["state"]["log"] == []
    assert len(data["legalActions"]) == 54


def test_same_seed_same_board(client):
    a = client.post("/api/games", json={"seed": 7}).json()
    b = client.post("/api/games", json={"seed": 7}).json()
    assert a["gameId"] != b["gameId"]
    assert a["state"]["board"] == b["state"]["board"]
    assert a["state"]["seed"] == 7


@pytest.mark.parametrize(
    "body", [{"difficulty": "hard"}, {"seed": -1}, {"seed": 2**31}, {"seed": "abc"}]
)
def test_bad_create_requests_are_rejected(client, body):
    assert client.post("/api/games", json=body).status_code == 422


def test_get_game_returns_the_created_game(client):
    created = client.post("/api/games", json={"seed": 3}).json()
    fetched = client.get(f"/api/games/{created['gameId']}").json()
    assert fetched == created


def test_unknown_game_is_404(client):
    r = client.get("/api/games/not-a-real-id")
    assert r.status_code == 404
    assert r.json()["detail"] == "Game not found or expired"


def test_cors_allows_only_the_frontend(client):
    ok = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:3000"
    other = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers
