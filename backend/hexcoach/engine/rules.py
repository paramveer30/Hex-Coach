"""The rules: legal moves, applying moves, and scoring."""

from hexcoach.engine.geometry import VERTEX_NEIGHBORS

EMPTY = -1


def settlement_spot_ok(vertex_owner: list[int], vertex: int) -> bool:
    if vertex_owner[vertex] != EMPTY:
        return False
    for neighbor in VERTEX_NEIGHBORS[vertex]:
        if vertex_owner[neighbor] != EMPTY:
            return False
    return True
