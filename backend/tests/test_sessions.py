from hexcoach.api.sessions import TTL_SECONDS, SessionStore
from hexcoach.bots.heuristic import HeuristicBot
from hexcoach.engine.rules import new_game


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make_store():
    clock = FakeClock()
    return SessionStore(clock=clock), clock


def add_game(store, seed=1):
    return store.create(seed, 0, {1: HeuristicBot(), 2: HeuristicBot()}, new_game(seed))


def test_created_game_can_be_found():
    store, _ = make_store()
    session = add_game(store)
    assert store.get(session.id) is session


def test_unknown_id_returns_none():
    store, _ = make_store()
    assert store.get("nope") is None


def test_ids_are_unique_and_not_guessable():
    store, _ = make_store()
    ids = {add_game(store).id for _ in range(100)}
    assert len(ids) == 100
    assert all(len(i) >= 12 for i in ids)


def test_game_expires_after_two_hours_unused():
    store, clock = make_store()
    session = add_game(store)
    clock.now = TTL_SECONDS + 1
    assert store.get(session.id) is None


def test_using_a_game_resets_its_timer():
    store, clock = make_store()
    session = add_game(store)
    clock.now = TTL_SECONDS - 60
    assert store.get(session.id) is session
    clock.now = 2 * TTL_SECONDS - 120
    assert store.get(session.id) is session


def test_purge_only_removes_expired_games():
    store, clock = make_store()
    old = add_game(store)
    clock.now = TTL_SECONDS - 10
    fresh = add_game(store)
    clock.now = TTL_SECONDS + 1
    store.purge()
    assert list(store.sessions) == [fresh.id]
    assert old.id not in store.sessions


def test_each_session_has_its_own_lock_and_seeded_rng():
    store, _ = make_store()
    a, b = add_game(store, seed=5), add_game(store, seed=5)
    assert a.lock is not b.lock
    assert a.rng is not b.rng
    assert a.rng.random() == b.rng.random()
