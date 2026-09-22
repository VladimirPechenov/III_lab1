"""Конечный автомат стражника: Patrol → Alert → Chase → Attack → Return."""

from enum import Enum, auto


class State(Enum):
    PATROL = auto()
    ALERT = auto()
    CHASE = auto()
    ATTACK = auto()
    RETURN = auto()


TRANSITIONS: dict[tuple[State, str], State] = {
    (State.PATROL, "see_player"): State.ALERT,
    (State.PATROL, "hear_noise"): State.ALERT,
    (State.ALERT, "confirm"): State.CHASE,
    (State.ALERT, "timeout"): State.PATROL,
    (State.CHASE, "in_range"): State.ATTACK,
    (State.CHASE, "lost"): State.RETURN,
    (State.ATTACK, "out_of_range"): State.CHASE,
    (State.RETURN, "arrived"): State.PATROL,
}


class GuardFSM:
    def __init__(self) -> None:
        self.state = State.PATROL
        self.history: list[tuple[State, str, State]] = []

    def fire(self, trigger: str) -> bool:
        nxt = TRANSITIONS.get((self.state, trigger))
        if nxt is None:
            return False
        self.history.append((self.state, trigger, nxt))
        self.state = nxt
        return True
