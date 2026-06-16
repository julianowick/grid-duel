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