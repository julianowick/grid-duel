# Grid Duel v2

The game involves two characters moving around a board collecting items, engaging in duels, and trying to reach the opponent's base. Each character makes decisions to move or use items using a different algorithm.

## **How ​​does the game work?**

* Two players move alternately around a board.
* There are three types of items scattered around:
  * **Secret Chests**: These are magical items that provide extraordinary abilities of **invisibility**, **speed**, and **freezing** to the characters (value 'C').

  * **Buff/Debuff**: These are items that increase or decrease the player's strength (values ​​3, 2, 1, -1, -2, and -3).

  * **Walls:** Impassable positions on the map (value 'W'). * A player can win in three ways:

* By reaching the opponent's base.
* By winning a direct duel against the opponent.
* By accumulating more strength at the end of the time limit (or a draw if the strengths are equal).
* Duels occur when players meet on the board (they are in adjacent cells).
* In a duel, the character who has acquired more strength has a higher probability of winning, but **victory is not guaranteed**.

## Folders and Files

| File/Folder | Description |
|---|---|
| `game_engine.py` | Core game engine — board generation, turn processing, spell system (freeze/speed/invisibility), duel resolution, victory conditions, Tkinter-based rendering with sprite assets, and `pygame.mixer` audio playback for match music. |
| `playoffs.py` | Tournament bracket orchestrator — shuffles agents, runs best-of-3 matches with player-swapping for fairness, prints bracket progression, and determines the champion. |
| `agent_rand_defend.py` | Defensive agent — guards its own starting position, biases moves toward home, has a 30% chance of using spells. |
| `agent_rand_hunt.py` | Aggressive pursuit agent — chases the enemy's current position with doubled directional weight, has a 70% chance of activating spells. |
| `agent_rand_objective.py` | Goal-oriented agent — moves toward the assigned objective (enemy's base), has a 30% chance of using spells. |
| `agent_rand_spell.py` | Spell-seeking agent — overrides objective with the nearest chest, doubles directional bias toward it, uses spells only 1% of the time. |
| `audio/` | Audio assets — `main-theme.mp3` (background music, loops during a match) and `match-end.mp3` (end-of-match sound, loops on the end screen). Played via `pygame.mixer`. |
| `figures/` | 24 PNG sprite images for players (elf/wizard), items (buffs, debuffs), spells (freeze/speed/invisibility), board elements (wall, chest), UI icons, and end-screen art. |
| `.gitignore` | Git ignore rules — excludes listed files and folders from version control. |

## Developing New Agents

Each agent is a Python module that must implement a single top-level function:

```python
def get_move(board, objective, position, enemy_position, my_strength, enemy_strength, available_spells, memory):
```

### Arguments received from the game engine

| Argument | Type | Description |
|---|---|---|
| `board` | `tuple` of `tuple`s | 16×16 grid. `0` = empty cell, `'W'` = wall, `'C'` = spell chest, integers (`-3` to `3`) = buff/debuff items. |
| `objective` | `tuple` `(x, y)` | Coordinates of the enemy's base (the agent's goal to reach). Player 1 → `(15, 15)`, Player 2 → `(0, 0)`. |
| `position` | `tuple` `(x, y)` | The agent's current position on the board. |
| `enemy_position` | `tuple` `(x, y)` | The opponent's current position. Set to `(-1, -1)` when the opponent is invisible. |
| `my_strength` | `int` | The agent's accumulated strength (sum of collected buffs/debuffs). |
| `enemy_strength` | `int` | The opponent's accumulated strength. |
| `available_spells` | `tuple` of `str` | Spells the agent has collected and may activate. Possible values: `"freeze"`, `"speed"`, `"invisibility"`. |
| `memory` | `list` | Persists across turns — starts empty (`[]`). Use to store arbitrary data (e.g., initial position, path history). |

### Return value

Return one of the following:
- **Movement direction** — `"up"`, `"down"`, `"left"`, `"right"`, or `"stay"`. The engine validates the move and clamps coordinates to the board bounds; wall collisions are ignored (position stays unchanged).
- **Spell activation** — any string present in `available_spells` (e.g., `"freeze"`, `"speed"`, `"invisibility"`). The spell is consumed from `available_spells` and applied immediately for a duration of 5 turns.

### Registering an agent

Place the file in the project root (e.g., `my_agent.py`) and reference it by module name (without `.py` suffix) when running matches or playoffs.