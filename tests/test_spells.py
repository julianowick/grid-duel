"""Tests for the teleport and invincibility spells (headless engine, stub agents)."""
import os
import random
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game_engine  # noqa: E402
from game_engine import GameApp  # noqa: E402


def _stub_agent(name, script):
    """Register module `name` whose get_move pops moves from `script` ('stay' when empty)."""
    calls = []

    def get_move(board, objective, position, enemy_position, my_strength,
                 enemy_strength, available_spells, memory):
        calls.append(position)
        return script.pop(0) if script else "stay"

    mod = types.ModuleType(name)
    mod.get_move = get_move
    sys.modules[name] = mod
    return calls


@pytest.fixture
def make_game(monkeypatch):
    # The constructor would run the whole match; drive play_turn() manually instead.
    monkeypatch.setattr(GameApp, "run", lambda self: None)

    def _make(script1=None, script2=None):
        calls1 = _stub_agent("stub_a", list(script1 or []))
        calls2 = _stub_agent("stub_b", list(script2 or []))
        game = GameApp("stub_a", "stub_b", headless=True)
        # Clear the board so only the spells under test matter.
        game.board = [[0] * game_engine.BOARD_SIZE for _ in range(game_engine.BOARD_SIZE)]
        game.items, game.spells = [], []
        return game, calls1, calls2

    return _make


def test_spell_types_and_chests(monkeypatch):
    monkeypatch.setattr(GameApp, "run", lambda self: None)
    _stub_agent("stub_a", [])
    _stub_agent("stub_b", [])
    random.seed(1)
    game = GameApp("stub_a", "stub_b", headless=True)
    assert "teleport" in game_engine.SPELL_TYPES and "invincibility" in game_engine.SPELL_TYPES
    assert sorted(s for _, _, s in game.spells) == sorted(game_engine.SPELL_TYPES)
    assert sum(row.count("C") for row in game.board) == len(game_engine.SPELL_TYPES)


def test_chest_is_single_use(make_game):
    game, _, _ = make_game(script1=["right"])
    game.board[1][0] = "C"
    game.items.append((1, 0, "chest"))
    game.spells.append((1, 0, "teleport"))
    game.play_turn()
    assert game.spells1 == ["teleport"]
    assert game.board[1][0] == 0 and (1, 0, "chest") not in game.items


def test_teleport_channel_then_home(make_game):
    game, calls1, _ = make_game(script1=["teleport"])
    game.pos1 = (5, 5)
    game.pos2 = (15, 15)
    game.spells1 = ["teleport"]
    game.play_turn()                      # cast round
    assert game.spells1 == [] and "teleport" in game.active_spells1
    assert game.pos1 == (5, 5)
    n = len(calls1)
    game.play_turn()                      # channel round 1
    assert len(calls1) == n and game.pos1 == (5, 5)
    game.play_turn()                      # channel round 2 -> lands home at round end
    assert len(calls1) == n               # get_move is never called while channeling
    assert game.pos1 == (0, 0)
    assert "teleport" not in game.active_spells1
    game.play_turn()                      # control returns to the agent
    assert len(calls1) == n + 1


def test_teleport_caster_vulnerable_during_channel(make_game):
    game, _, _ = make_game()
    game.pos1 = (5, 5)
    game.pos2 = (5, 6)                    # adjacent -> duel is checked at end of round
    game.active_spells1 = ["teleport"]
    game.spell_durations["teleport"] = 1  # this is the final channel round
    game.strength1, game.strength2 = 0, 10_000
    game.play_turn()
    # The duel is resolved before the teleport moves the caster home.
    assert game.game_over and game.end_reason == "duel"


def test_invincibility_wins_duels(make_game):
    for seed in range(20):
        random.seed(seed)
        game, _, _ = make_game(script1=["invincibility"])
        game.pos1, game.pos2 = (5, 5), (5, 6)
        game.spells1 = ["invincibility"]
        game.strength1, game.strength2 = -3, 3    # shielded player is the weaker one
        game.play_turn()                          # cast round counts as round 1
        assert game.game_over and game.end_winner == "Player 1"


def test_invincibility_lasts_exactly_five_rounds(make_game):
    game, _, _ = make_game(script1=["invincibility"])
    game.pos1, game.pos2 = (0, 0), (15, 15)
    game.spells1 = ["invincibility"]
    for rnd in range(1, 6):
        game.play_turn()
        if rnd < 5:
            assert "invincibility" in game.active_spells1, f"expired early after round {rnd}"
    assert "invincibility" not in game.active_spells1


def test_no_shield_uses_normal_duel(make_game, monkeypatch):
    game, _, _ = make_game()
    game.pos1, game.pos2 = (5, 5), (5, 6)
    monkeypatch.setattr(game, "resolve_duel", lambda a, b: "Player 2")
    game.play_turn()
    assert game.end_winner == "Player 2" and game.end_reason == "duel"
