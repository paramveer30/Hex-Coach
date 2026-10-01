"""API message shapes, and conversion between JSON and engine objects."""

from dataclasses import asdict
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

from hexcoach.engine import actions as act
from hexcoach.engine.geometry import NUM_EDGES, NUM_HEXES, NUM_VERTICES
from hexcoach.engine.rules import legal_actions, player_to_move, victory_points
from hexcoach.engine.state import GameState

Vertex = Annotated[int, Field(ge=0, lt=NUM_VERTICES)]
Edge = Annotated[int, Field(ge=0, lt=NUM_EDGES)]
Hex = Annotated[int, Field(ge=0, lt=NUM_HEXES)]
Resource = Annotated[int, Field(ge=0, le=4)]
Player = Annotated[int, Field(ge=0, le=2)]


class PlaceSetupSettlementIn(BaseModel):
    type: Literal["PlaceSetupSettlement"]
    vertex: Vertex


class PlaceSetupRoadIn(BaseModel):
    type: Literal["PlaceSetupRoad"]
    edge: Edge


class RollDiceIn(BaseModel):
    type: Literal["RollDice"]


class DiscardIn(BaseModel):
    type: Literal["Discard"]
    counts: Annotated[list[Annotated[int, Field(ge=0)]], Field(min_length=5, max_length=5)]


class MoveRobberIn(BaseModel):
    type: Literal["MoveRobber"]
    hex: Hex


class StealIn(BaseModel):
    type: Literal["Steal"]
    victim: Player


class BuildRoadIn(BaseModel):
    type: Literal["BuildRoad"]
    edge: Edge


class BuildSettlementIn(BaseModel):
    type: Literal["BuildSettlement"]
    vertex: Vertex


class BuildCityIn(BaseModel):
    type: Literal["BuildCity"]
    vertex: Vertex


class BankTradeIn(BaseModel):
    type: Literal["BankTrade"]
    give: Resource
    get: Resource


class EndTurnIn(BaseModel):
    type: Literal["EndTurn"]


# pydantic reads "type" first and validates the rest against the matching model
ActionIn = Annotated[
    PlaceSetupSettlementIn
    | PlaceSetupRoadIn
    | RollDiceIn
    | DiscardIn
    | MoveRobberIn
    | StealIn
    | BuildRoadIn
    | BuildSettlementIn
    | BuildCityIn
    | BankTradeIn
    | EndTurnIn,
    Field(discriminator="type"),
]
action_adapter: TypeAdapter[ActionIn] = TypeAdapter(ActionIn)

ENGINE_ACTIONS = {
    cls.__name__: cls
    for cls in (
        act.PlaceSetupSettlement,
        act.PlaceSetupRoad,
        act.RollDice,
        act.Discard,
        act.MoveRobber,
        act.Steal,
        act.BuildRoad,
        act.BuildSettlement,
        act.BuildCity,
        act.BankTrade,
        act.EndTurn,
    )
}


def to_engine_action(message: BaseModel) -> act.Action:
    fields = message.model_dump(exclude={"type"})
    if "counts" in fields:
        fields["counts"] = tuple(fields["counts"])
    return ENGINE_ACTIONS[message.type](**fields)


def action_to_json(action: act.Action) -> dict:
    fields = asdict(action)
    if "counts" in fields:
        fields["counts"] = list(fields["counts"])
    return {"type": type(action).__name__, **fields}


def state_to_json(state: GameState) -> dict:
    # camelCase to match frontend/lib/types.ts
    moves = legal_actions(state)
    return {
        "board": {
            "hexResource": list(state.board.hex_resource),
            "hexNumber": list(state.board.hex_number),
            "portType": list(state.board.port_type),
            "desertHex": state.board.desert_hex,
        },
        "robberHex": state.robber_hex,
        "vertexOwner": state.vertex_owner,
        "vertexLevel": state.vertex_level,
        "edgeOwner": state.edge_owner,
        "hands": state.hands,
        "bank": state.bank,
        "piecesLeft": [list(p) for p in state.pieces_left],
        "longestRoadHolder": state.longest_road_holder,
        "longestRoadLen": state.longest_road_len,
        "currentPlayer": state.current_player,
        "playerToMove": player_to_move(state),
        "phase": state.phase.name,
        "setupVertex": state.setup_vertex,
        "pendingDiscards": state.pending_discards,
        "turnNumber": state.turn_number,
        "lastRoll": state.last_roll,
        "winner": state.winner,
        "victoryPoints": [victory_points(state, p) for p in range(state.num_players)],
        "legal": {
            "road": sorted(
                a.edge for a in moves if isinstance(a, act.BuildRoad | act.PlaceSetupRoad)
            ),
            "settlement": sorted(
                a.vertex
                for a in moves
                if isinstance(a, act.BuildSettlement | act.PlaceSetupSettlement)
            ),
            "city": sorted(a.vertex for a in moves if isinstance(a, act.BuildCity)),
        },
    }
