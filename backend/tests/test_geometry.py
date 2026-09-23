from collections import Counter

from hexcoach.engine import geometry as g


def test_board_has_19_hexes_54_vertices_72_edges():
    assert g.NUM_HEXES == 19
    assert g.NUM_VERTICES == 54
    assert g.NUM_EDGES == 72


def test_rows_are_3_4_5_4_3():
    rows = Counter(r for _, r in g.HEX_COORDS)
    assert [rows[r] for r in range(-2, 3)] == [3, 4, 5, 4, 3]


def test_every_hex_has_6_distinct_vertices():
    for corners in g.HEX_VERTICES:
        assert len(set(corners)) == 6


def test_vertex_table_sizes():
    for v in range(g.NUM_VERTICES):
        assert 1 <= len(g.VERTEX_HEXES[v]) <= 3
        assert 2 <= len(g.VERTEX_NEIGHBORS[v]) <= 3
        assert len(g.VERTEX_EDGES[v]) == len(g.VERTEX_NEIGHBORS[v])


def test_every_edge_has_2_distinct_vertices():
    for a, b in g.EDGE_VERTICES:
        assert a < b


def test_vertex_adjacency_is_symmetric():
    for v, neighbors in enumerate(g.VERTEX_NEIGHBORS):
        for n in neighbors:
            assert v in g.VERTEX_NEIGHBORS[n]


def test_hex_adjacency_is_symmetric():
    for h, neighbors in enumerate(g.HEX_NEIGHBORS):
        assert h not in neighbors
        for n in neighbors:
            assert h in g.HEX_NEIGHBORS[n]


def test_hex_vertex_tables_agree():
    for h, corners in enumerate(g.HEX_VERTICES):
        for v in corners:
            assert h in g.VERTEX_HEXES[v]


def test_vertex_edge_tables_agree():
    for e, (a, b) in enumerate(g.EDGE_VERTICES):
        assert e in g.VERTEX_EDGES[a]
        assert e in g.VERTEX_EDGES[b]


def test_center_hex_touches_6_hexes_and_corner_hex_touches_3():
    center = g.HEX_COORDS.index((0, 0))
    top_left = g.HEX_COORDS.index((0, -2))
    assert len(g.HEX_NEIGHBORS[center]) == 6
    assert len(g.HEX_NEIGHBORS[top_left]) == 3


def test_coast_has_30_edges_and_30_vertices():
    coastal_edges = [e for e in range(g.NUM_EDGES) if len(g.EDGE_HEXES[e]) == 1]
    coastal_vertices = [v for v in range(g.NUM_VERTICES) if len(g.VERTEX_HEXES[v]) < 3]
    assert len(coastal_edges) == 30
    assert len(coastal_vertices) == 30


def test_adjacent_vertices_are_one_hex_side_apart():
    for a, b in g.EDGE_VERTICES:
        (x1, y1), (x2, y2) = g.VERTEX_POSITIONS[a], g.VERTEX_POSITIONS[b]
        side = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        assert abs(side - g.HEX_SIZE) < 0.01


def test_coastal_walk_is_a_connected_loop():
    edges = g.COASTAL_EDGES
    for i, e in enumerate(edges):
        nxt = edges[(i + 1) % len(edges)]
        assert set(g.EDGE_VERTICES[e]) & set(g.EDGE_VERTICES[nxt])


def test_9_ports_on_coastal_edges_with_no_shared_vertices():
    assert len(g.PORT_EDGES) == 9
    assert all(e in g.COASTAL_EDGES for e in g.PORT_EDGES)
    port_vertices = [v for pair in g.PORT_VERTICES for v in pair]
    assert len(set(port_vertices)) == 18


def test_geometry_tables_are_immutable_tuples():
    for table in (g.HEX_VERTICES, g.VERTEX_NEIGHBORS, g.EDGE_VERTICES, g.PORT_VERTICES):
        assert isinstance(table, tuple)
        assert all(isinstance(row, tuple) for row in table)
