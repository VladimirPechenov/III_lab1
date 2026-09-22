from guard.bt import Status, build_guard_tree
from guard.fsm import GuardFSM, State


def test_full_cycle():
    g = GuardFSM()
    for t in ["see_player", "confirm", "in_range", "out_of_range", "lost", "arrived"]:
        assert g.fire(t)
    assert g.state == State.PATROL


def test_bt_priority():
    bb = {"see_player": True, "hear_noise": True}
    assert build_guard_tree().tick(bb) == Status.RUNNING
    assert bb["action"] == "chase"
