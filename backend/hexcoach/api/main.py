"""The web server: REST endpoints for board geometry and games."""

import secrets
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from hexcoach.api.schemas import action_to_json, state_to_json
from hexcoach.api.sessions import Session, SessionStore
from hexcoach.bots.heuristic import HeuristicBot
from hexcoach.engine import geometry as geo
from hexcoach.engine.rules import legal_actions, new_game, player_to_move

HUMAN_SEAT = 0
ALLOWED_ORIGINS = ["http://localhost:3000"]

app = FastAPI(title="Hexcoach")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
store = SessionStore()

GEOMETRY = {
    "hexSize": geo.HEX_SIZE,
    "hexCoords": geo.HEX_COORDS,
    "hexCenters": geo.HEX_CENTERS,
    "hexVertices": geo.HEX_VERTICES,
    "vertexPositions": geo.VERTEX_POSITIONS,
    "edgeVertices": geo.EDGE_VERTICES,
    "edgeMidpoints": geo.EDGE_MIDPOINTS,
    "portEdges": geo.PORT_EDGES,
    "portVertices": geo.PORT_VERTICES,
}


class CreateGameIn(BaseModel):
    # only the heuristic bot exists until the search bot in Phase 4
    difficulty: Literal["easy"] = "easy"
    seed: int | None = Field(default=None, ge=0, lt=2**31)


def game_json(session: Session) -> dict:
    state = session.state
    mine = player_to_move(state) == session.human_seat
    return {
        "gameId": session.id,
        "humanSeat": session.human_seat,
        "state": {**state_to_json(state), "seed": session.seed, "log": session.log},
        "legalActions": [action_to_json(a) for a in legal_actions(state)] if mine else [],
    }


def find_session(game_id: str) -> Session:
    session = store.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found or expired")
    return session


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/geometry")
async def geometry() -> dict:
    return GEOMETRY


@app.post("/api/games", status_code=201)
async def create_game(body: CreateGameIn) -> dict:
    seed = body.seed if body.seed is not None else secrets.randbelow(2**31)
    state = new_game(seed)
    bots = {seat: HeuristicBot() for seat in range(state.num_players) if seat != HUMAN_SEAT}
    return game_json(store.create(seed, HUMAN_SEAT, bots, state))


@app.get("/api/games/{game_id}")
async def get_game(game_id: str) -> dict:
    return game_json(find_session(game_id))
