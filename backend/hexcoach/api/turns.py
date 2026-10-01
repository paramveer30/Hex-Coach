"""Applying moves to a session and playing the bots' turns."""

from hexcoach.api.schemas import action_to_json
from hexcoach.api.sessions import Session
from hexcoach.engine.actions import Action, RollDice
from hexcoach.engine.rules import apply, is_terminal, player_to_move


def play_move(session: Session, action: Action) -> dict:
    seat = player_to_move(session.state)
    session.state = apply(session.state, action, session.rng)
    entry = {"player": seat, **action_to_json(action)}
    if isinstance(action, RollDice):
        entry["roll"] = session.state.last_roll
    session.log.append(entry)
    return entry


def bot_to_move(session: Session) -> bool:
    state = session.state
    return not is_terminal(state) and player_to_move(state) in session.bots


def bot_step(session: Session) -> dict:
    bot = session.bots[player_to_move(session.state)]
    return play_move(session, bot.choose(session.state, session.bot_rng))
