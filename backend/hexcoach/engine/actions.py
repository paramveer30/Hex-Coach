"""Every move a player can make. Frozen so they can be dict keys in search."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlaceSetupSettlement:
    vertex: int


@dataclass(frozen=True, slots=True)
class PlaceSetupRoad:
    edge: int


@dataclass(frozen=True, slots=True)
class RollDice:
    pass


@dataclass(frozen=True, slots=True)
class Discard:
    counts: tuple[int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class MoveRobber:
    hex: int


@dataclass(frozen=True, slots=True)
class Steal:
    victim: int


@dataclass(frozen=True, slots=True)
class BuildRoad:
    edge: int


@dataclass(frozen=True, slots=True)
class BuildSettlement:
    vertex: int


@dataclass(frozen=True, slots=True)
class BuildCity:
    vertex: int


@dataclass(frozen=True, slots=True)
class BankTrade:
    give: int
    get: int


@dataclass(frozen=True, slots=True)
class EndTurn:
    pass


Action = (
    PlaceSetupSettlement
    | PlaceSetupRoad
    | RollDice
    | Discard
    | MoveRobber
    | Steal
    | BuildRoad
    | BuildSettlement
    | BuildCity
    | BankTrade
    | EndTurn
)
