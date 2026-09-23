"""GameState: everything about a game at one moment, as flat lists of ints."""

from dataclasses import dataclass
from enum import IntEnum

from hexcoach.engine.board import Board


class Phase(IntEnum):
    SETUP_SETTLEMENT = 0
    SETUP_ROAD = 1
    ROLL = 2
    DISCARD = 3
    MOVE_ROBBER = 4
    STEAL = 5
    MAIN = 6
    GAME_OVER = 7


@dataclass(slots=True)
class GameState:
    board: Board
    robber_hex: int
    vertex_owner: list[int]  # -1 empty, else player id
    vertex_level: list[int]  # 0 none, 1 settlement, 2 city
    edge_owner: list[int]  # -1 empty, else player id
    hands: list[list[int]]  # hands[player][resource]
    bank: list[int]
    pieces_left: list[tuple[int, int, int]]  # (roads, settlements, cities) per player
    longest_road_holder: int
    longest_road_len: list[int]
    current_player: int
    phase: Phase
    setup_step: int
    setup_vertex: int  # settlement just placed in setup, so the road can touch it
    pending_discards: list[int]
    turn_number: int
    last_roll: int | None
    winner: int | None

    @property
    def num_players(self) -> int:
        return len(self.hands)

    def clone(self) -> "GameState":
        # board and the tuples in pieces_left are immutable, so sharing them is safe
        return GameState(
            self.board,
            self.robber_hex,
            self.vertex_owner[:],
            self.vertex_level[:],
            self.edge_owner[:],
            [hand[:] for hand in self.hands],
            self.bank[:],
            self.pieces_left[:],
            self.longest_road_holder,
            self.longest_road_len[:],
            self.current_player,
            self.phase,
            self.setup_step,
            self.setup_vertex,
            self.pending_discards[:],
            self.turn_number,
            self.last_roll,
            self.winner,
        )
