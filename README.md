# Grid Duel ⚔️

A turn-based strategy game where two AI agents compete on a 16×16 board. Players collect buffs and debuffs, discover magical spells, and engage in duels while trying to reach the opponent's base to win.

## How It Works

- Two agents take turns moving around a procedurally generated board.
- The board contains three types of items:
  - **Secret Chests** (`C`) — grant spells: **invisibility**, **speed**, **freeze**, **teleport**, or **invincibility**.
  - **Buffs/Debuffs** (integers `-3` through `3`) — modify the player's strength.
  - **Walls** (`W`) — impassable obstacles.
- A player wins by:
  1. Reaching the opponent's base.
  2. Winning a direct duel (when players occupy adjacent cells).
  3. Having higher strength when the turn limit (120) is reached.
- In a duel, the player with greater strength has a higher probability of winning, but victory is **not guaranteed** — it's resolved by weighted random selection.

## Repository Structure

| Path | Description |
|---|---|
| `game_engine.py` | Core engine: board generation, turn processing, spell system, duel resolution, victory conditions, pygame rendering with sprite assets, and `pygame.mixer` audio. |
| `playoffs.py` | Tournament bracket orchestrator — shuffles agents, runs best-of-3 matches with player-swapping for fairness, prints bracket progression, and determines the champion. Progress is saved to `playoffs_state.json` so a tournament can be resumed. |
| `agents/` | Agent modules (loaded as `agents.<name>`). |
| `agents/agent_bfs.py` | BFS pathfinding agent — computes shortest path to objective and uses spells strategically at close range. |
| `agents/agent_value_bfs.py` | Value-weighted pathfinding agent — Dijkstra-style search favoring buffs/chests and avoiding debuffs, with weights scaled by distance to the objective. |
| `agents/agent_rand_defend.py` | Defensive agent — guards its start position, biases toward home, 30% spell usage. |
| `agents/agent_rand_hunt.py` | Aggressive pursuit agent — chases the enemy with double directional weight, 70% spell usage. |
| `agents/agent_rand_objective.py` | Goal-oriented agent — moves toward the enemy base, 30% spell usage. |
| `agents/agent_rand_spell.py` | Spell-seeking agent — overrides objective with the nearest chest, 1% spell usage. |
| `audio/` | Game audio assets (`lobby-theme.mp3`, `main-theme.mp3`, `match-end.mp3`). |
| `figures/` | 26 PNG sprite images for players, items, spells, board elements, UI, and end screen. |
| `fonts/` | MedievalSharp font used for in-game text. |
| `playoffs_state.json` | Auto-generated tournament save file (git-ignored). |
| `tests/` | Pytest suite for spell mechanics (`python -m pytest tests`). |
| `AGENTS.md` | Detailed guide for creating new agents (API reference, argument table, return values). |

## Requirements

- Python 3.8+
- `pygame` — install with `pip install pygame`
- Audio on Linux: the engine defaults `SDL_AUDIODRIVER` to `pipewire,pulseaudio,alsa`, because SDL's PulseAudio backend can deadlock on exit and freeze the app after a match. Set `SDL_AUDIODRIVER` yourself to override.

## Running a Match

```bash
python game_engine.py
```

By default the engine runs `agents.agent_value_bfs` vs `agents.agent_rand_defend`. To use custom agents, modify the `__main__` block at the bottom of `game_engine.py` or import `GameApp` from another script (agent modules are passed with the `agents.` prefix):

```python
from game_engine import GameApp

GameApp("agents.my_agent", "agents.agent_rand_objective")
```

### Headless mode (no GUI)

Useful for tournaments or automated testing:

```python
GameApp("agents.my_agent", "agents.agent_rand_objective", headless=True)
```

## Running a Tournament

Edit the `competitors` list in `playoffs.py` to include your agents (bare module names, e.g. `"my_agent"` — the `agents.` prefix is added automatically), then run:

```bash
python playoffs.py
```

The tournament runs best-of-3 matches, alternating player sides for fairness. If the competitor count isn't a power of 2, the bracket is padded with random agents. Progress is saved to `playoffs_state.json`; on the next launch you'll be asked whether to resume.

## Creating a New Agent

Each agent is a Python file in the `agents/` folder that implements a single function:

```python
def get_move(board, objective, position, enemy_position,
             my_strength, enemy_strength, available_spells, memory):
    # Your logic here
    return "up"  # or "down", "left", "right", "stay", or a spell name
```

**Arguments** (all received from the engine):

| Argument | Type | Description |
|---|---|---|
| `board` | `tuple` of `tuple`s | 16×16 grid. `0` = empty, `'W'` = wall, `'C'` = spell chest, ints = buffs/debuffs. |
| `objective` | `(x, y)` | Enemy base coordinates: Player 1 → `(15,15)`, Player 2 → `(0,0)`. |
| `position` | `(x, y)` | Your current position. |
| `enemy_position` | `(x, y)` | Opponent's position (`(-1, -1)` when invisible). |
| `my_strength` | `int` | Your accumulated strength. |
| `enemy_strength` | `int` | Opponent's accumulated strength. |
| `available_spells` | `tuple` of `str` | Spells you hold — `"freeze"`, `"speed"`, `"invisibility"`, `"teleport"`, `"invincibility"`. |
| `memory` | `list` | Persistent state across turns (starts empty). |

**Return value** — one of:
- **Direction**: `"up"`, `"down"`, `"left"`, `"right"`, or `"stay"`.
- **Spell**: any string present in `available_spells` (e.g., `"freeze"`). The spell is consumed and applied (5 turns, or a 2-round channel for `teleport`).

**Register your agent** by placing the `.py` file in the `agents/` folder and passing `agents.<name>` to `GameApp`, or adding `<name>` to the `competitors` list in `playoffs.py`.

> For a detailed walkthrough with examples, see [`AGENTS.md`](AGENTS.md).
