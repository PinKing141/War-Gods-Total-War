"""Phase 7 turn-simulation tests."""

from warfare_simulation.orchestration import GameState


def test_game_state_advances_across_year_boundary():
    """The global clock should roll month 12 into year +1."""
    state = GameState(current_turn=12, current_month=12, current_year=1)

    state.advance_turn()

    assert state.current_turn == 13
    assert state.current_month == 1
    assert state.current_year == 2


def test_game_state_checkpoint_round_trip(tmp_path):
    """GameState checkpoints should save and restore the campaign clock."""
    checkpoint = tmp_path / "checkpoint.json"
    state = GameState(current_turn=4, current_month=4, current_year=1)

    saved_path = state.save_checkpoint(checkpoint)
    restored = GameState.load_checkpoint(saved_path)

    assert restored == state
