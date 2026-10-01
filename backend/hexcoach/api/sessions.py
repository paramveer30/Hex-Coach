"""In-memory game sessions that expire after 2 hours without use."""

import asyncio
import random
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from hexcoach.bots.base import Bot
from hexcoach.engine.state import GameState

TTL_SECONDS = 2 * 60 * 60


@dataclass
class Session:
    id: str
    seed: int
    human_seat: int
    bots: dict[int, Bot]  # seat -> bot, for every seat except the human's
    state: GameState
    rng: random.Random
    last_used: float
    log: list[dict] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class SessionStore:
    def __init__(self, ttl: float = TTL_SECONDS, clock: Callable[[], float] = time.monotonic):
        self.ttl = ttl
        self.clock = clock
        self.sessions: dict[str, Session] = {}

    def create(self, seed: int, human_seat: int, bots: dict[int, Bot], state: GameState) -> Session:
        self.purge()
        session = Session(
            id=secrets.token_urlsafe(9),
            seed=seed,
            human_seat=human_seat,
            bots=bots,
            state=state,
            rng=random.Random(seed),
            last_used=self.clock(),
        )
        self.sessions[session.id] = session
        return session

    def get(self, game_id: str) -> Session | None:
        self.purge()
        session = self.sessions.get(game_id)
        if session is not None:
            session.last_used = self.clock()
        return session

    def purge(self) -> None:
        now = self.clock()
        expired = [gid for gid, s in self.sessions.items() if now - s.last_used > self.ttl]
        for gid in expired:
            del self.sessions[gid]
