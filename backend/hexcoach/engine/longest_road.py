"""Longest continuous road: a depth-first search over one player's roads."""

from hexcoach.engine.geometry import EDGE_VERTICES, NUM_EDGES, VERTEX_EDGES

EMPTY = -1


def longest_road_length(edge_owner: list[int], vertex_owner: list[int], player: int) -> int:
    used = [False] * NUM_EDGES
    best = 0

    def walk(v: int, length: int) -> None:
        nonlocal best
        best = max(best, length)
        for e in VERTEX_EDGES[v]:
            if edge_owner[e] != player or used[e]:
                continue
            a, b = EDGE_VERTICES[e]
            nxt = b if a == v else a
            used[e] = True
            # we can end a road at an opponent's building, but not pass through it
            if vertex_owner[nxt] in (EMPTY, player):
                walk(nxt, length + 1)
            else:
                best = max(best, length + 1)
            used[e] = False

    starts = {v for e in range(NUM_EDGES) if edge_owner[e] == player for v in EDGE_VERTICES[e]}
    for v in starts:
        walk(v, 0)
    return best
