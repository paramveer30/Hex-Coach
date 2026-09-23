"""Hex, vertex, edge, and port tables, built once from axial coordinates."""

import math

BOARD_RADIUS = 2

HEX_SIZE = 60.0

AXIAL_DIRECTIONS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))

# rounding lets the same corner computed from two hexes dedupe to one vertex
_ROUND_DECIMALS = 3

# spacing between ports along the 30 coastal edges (sums to 30)
PORT_GAPS = (3, 3, 4, 3, 3, 4, 3, 3, 4)


def _round_point(x: float, y: float) -> tuple[float, float]:
    # + 0.0 turns -0.0 into 0.0
    return round(x, _ROUND_DECIMALS) + 0.0, round(y, _ROUND_DECIMALS) + 0.0


def _axial_to_pixel(q: int, r: int) -> tuple[float, float]:
    x = HEX_SIZE * math.sqrt(3) * (q + r / 2)
    y = HEX_SIZE * 1.5 * r
    return x, y


def _corner(cx: float, cy: float, i: int) -> tuple[float, float]:
    angle = math.radians(60 * i - 30)
    return _round_point(cx + HEX_SIZE * math.cos(angle), cy + HEX_SIZE * math.sin(angle))


def _build():
    coords = [
        (q, r)
        for r in range(-BOARD_RADIUS, BOARD_RADIUS + 1)
        for q in range(-BOARD_RADIUS, BOARD_RADIUS + 1)
        if max(abs(q), abs(r), abs(-q - r)) <= BOARD_RADIUS
    ]
    coord_to_hex = {c: h for h, c in enumerate(coords)}
    centers = [_axial_to_pixel(q, r) for q, r in coords]

    hex_neighbors = []
    for q, r in coords:
        neighbors = [coord_to_hex.get((q + dq, r + dr)) for dq, dr in AXIAL_DIRECTIONS]
        hex_neighbors.append(tuple(sorted(n for n in neighbors if n is not None)))

    hex_corner_points = [[_corner(cx, cy, i) for i in range(6)] for cx, cy in centers]
    unique_points = sorted(
        {p for corners in hex_corner_points for p in corners}, key=lambda p: (p[1], p[0])
    )
    point_to_vertex = {p: v for v, p in enumerate(unique_points)}
    hex_vertices = [tuple(point_to_vertex[p] for p in corners) for corners in hex_corner_points]

    edge_pairs = set()
    for corners in hex_vertices:
        for i in range(6):
            a, b = corners[i], corners[(i + 1) % 6]
            edge_pairs.add((min(a, b), max(a, b)))

    def midpoint(pair):
        (x1, y1), (x2, y2) = unique_points[pair[0]], unique_points[pair[1]]
        return _round_point((x1 + x2) / 2, (y1 + y2) / 2)

    edge_vertices = sorted(edge_pairs, key=lambda pair: midpoint(pair)[::-1])
    edge_midpoints = [midpoint(pair) for pair in edge_vertices]

    n_vertices = len(unique_points)
    vertex_hexes = [[] for _ in range(n_vertices)]
    for h, corners in enumerate(hex_vertices):
        for v in corners:
            vertex_hexes[v].append(h)

    vertex_edges = [[] for _ in range(n_vertices)]
    vertex_neighbors = [[] for _ in range(n_vertices)]
    for e, (a, b) in enumerate(edge_vertices):
        vertex_edges[a].append(e)
        vertex_edges[b].append(e)
        vertex_neighbors[a].append(b)
        vertex_neighbors[b].append(a)

    edge_hexes = [[] for _ in edge_vertices]
    edge_index = {pair: e for e, pair in enumerate(edge_vertices)}
    for h, corners in enumerate(hex_vertices):
        for i in range(6):
            a, b = corners[i], corners[(i + 1) % 6]
            edge_hexes[edge_index[(min(a, b), max(a, b))]].append(h)

    # sorted by angle around the center = clockwise, since screen y points down
    coastal = [e for e in range(len(edge_vertices)) if len(edge_hexes[e]) == 1]
    coastal.sort(key=lambda e: math.atan2(edge_midpoints[e][1], edge_midpoints[e][0]))

    port_edges = []
    i = 0
    for gap in PORT_GAPS:
        port_edges.append(coastal[i])
        i += gap

    def freeze(rows):
        return tuple(tuple(sorted(row)) for row in rows)

    return {
        "HEX_COORDS": tuple(coords),
        "HEX_NEIGHBORS": tuple(hex_neighbors),
        "HEX_VERTICES": tuple(hex_vertices),
        "VERTEX_HEXES": freeze(vertex_hexes),
        "VERTEX_NEIGHBORS": freeze(vertex_neighbors),
        "VERTEX_EDGES": freeze(vertex_edges),
        "EDGE_VERTICES": tuple(edge_vertices),
        "EDGE_HEXES": freeze(edge_hexes),
        "COASTAL_EDGES": tuple(coastal),
        "PORT_EDGES": tuple(port_edges),
        "HEX_CENTERS": tuple(_round_point(x, y) for x, y in centers),
        "VERTEX_POSITIONS": tuple(unique_points),
        "EDGE_MIDPOINTS": tuple(edge_midpoints),
    }


_tables = _build()

HEX_COORDS: tuple[tuple[int, int], ...] = _tables["HEX_COORDS"]
HEX_NEIGHBORS: tuple[tuple[int, ...], ...] = _tables["HEX_NEIGHBORS"]
HEX_VERTICES: tuple[tuple[int, ...], ...] = _tables["HEX_VERTICES"]
VERTEX_HEXES: tuple[tuple[int, ...], ...] = _tables["VERTEX_HEXES"]
VERTEX_NEIGHBORS: tuple[tuple[int, ...], ...] = _tables["VERTEX_NEIGHBORS"]
VERTEX_EDGES: tuple[tuple[int, ...], ...] = _tables["VERTEX_EDGES"]
EDGE_VERTICES: tuple[tuple[int, int], ...] = _tables["EDGE_VERTICES"]
EDGE_HEXES: tuple[tuple[int, ...], ...] = _tables["EDGE_HEXES"]
COASTAL_EDGES: tuple[int, ...] = _tables["COASTAL_EDGES"]
PORT_EDGES: tuple[int, ...] = _tables["PORT_EDGES"]
PORT_VERTICES: tuple[tuple[int, int], ...] = tuple(EDGE_VERTICES[e] for e in PORT_EDGES)

HEX_CENTERS: tuple[tuple[float, float], ...] = _tables["HEX_CENTERS"]
VERTEX_POSITIONS: tuple[tuple[float, float], ...] = _tables["VERTEX_POSITIONS"]
EDGE_MIDPOINTS: tuple[tuple[float, float], ...] = _tables["EDGE_MIDPOINTS"]

NUM_HEXES = len(HEX_COORDS)
NUM_VERTICES = len(VERTEX_POSITIONS)
NUM_EDGES = len(EDGE_VERTICES)
