import faulthandler
import importlib
import random
import logging
import sys

import pygame

BOARD_SIZE = 16
CELL_SIZE = 32
NUM_ITEMS = 20
ITEM_VALUES = [-3, -2, -1, 1, 2, 3]
NUM_WALLS = 20
SPELL_TYPES = ["freeze", "speed", "invisibility"]
SPELL_DURATION = 5
MAX_TURNS = 120
DELAY_MS = 50
INFO_PANEL_WIDTH = CELL_SIZE * 8
FONT_LARGE = CELL_SIZE
FONT_MEDIUM = int(FONT_LARGE * 0.875)
FONT_SMALL = int(FONT_MEDIUM * 0.60)
FONT_TINY = FONT_SMALL // 2
FONT_TITLE = int(FONT_LARGE * 1.75)

BOARD_BG = (220, 188, 141)
BOARD_OUTLINE = (149, 104, 65)
PANEL_BG = (212, 212, 212)
PLAYER1_COLOR = (47, 91, 64)
PLAYER2_COLOR = (52, 60, 125)
SPEED_COLOR = (255, 124, 124)
FREEZE_COLOR = (116, 248, 255)
INVISIBLE_ALPHA = 128
FREEZE_ALPHA = 128
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GOLD = (212, 175, 55)
DARK_BG = (25, 25, 40)

faulthandler.enable()
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("grid_duel")


class GameApp:
    def __init__(self, agent1_module, agent2_module, headless=False):
        self.headless = headless

        if not self.headless:
            pygame.init()
            total_width = BOARD_SIZE * CELL_SIZE + 2 * INFO_PANEL_WIDTH
            self.screen = pygame.display.set_mode((total_width, BOARD_SIZE * CELL_SIZE))
            pygame.display.set_caption("Grid Duel Game")
            self.clock = pygame.time.Clock()
            self._init_audio()

        try:
            self.agent1 = importlib.import_module(agent1_module).get_move
            self.agent2 = importlib.import_module(agent2_module).get_move
        except Exception as e:
            logger.exception(f"Error importing agent: {e}")
            sys.exit(1)

        self.name1 = agent1_module
        self.name2 = agent2_module

        self.images = {}
        if not self.headless:
            self._load_images()

        self.fonts = {}
        if not self.headless:
            self._init_fonts()

        self._init_game_state()

        self.run()

    def _init_audio(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            pygame.mixer.stop()
            self.lobby_theme = pygame.mixer.Sound("audio/lobby-theme.mp3")
            self.main_theme = pygame.mixer.Sound("audio/main-theme.mp3")
            self.match_end = pygame.mixer.Sound("audio/match-end.mp3")
            self.lobby_theme.play(loops=-1)
            self.audio_enabled = True
        except Exception as e:
            logger.warning(f"Audio initialization failed: {e}")
            self.audio_enabled = False

    def _load_images(self):
        def load(path, size):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)

        isz = (int(CELL_SIZE * 0.95), int(CELL_SIZE * 0.95))
        wsz = (CELL_SIZE, CELL_SIZE)
        bsz = (CELL_SIZE * 3, CELL_SIZE * 3)
        psz = (CELL_SIZE * 6, CELL_SIZE * 6)
        rsz = (CELL_SIZE * 4, CELL_SIZE * 4)

        self.images = {
            "Player 1": load("figures/elf.png", isz),
            "Player 1 badge": load("figures/elf.png", bsz),
            "Player 1 win": load("figures/elf_full.png", psz),
            "Player 1 lose": load("figures/elf_full_lose.png", psz),
            "Player 1 base": load("figures/elf_base.png", isz),
            "Player 2": load("figures/wizard.png", isz),
            "Player 2 badge": load("figures/wizard.png", bsz),
            "Player 2 win": load("figures/wizard_full.png", psz),
            "Player 2 lose": load("figures/wizard_full_lose.png", psz),
            "Player 2 base": load("figures/wizard_base.png", isz),
            -3: load("figures/rex.png", isz),
            -2: load("figures/snake.png", isz),
            -1: load("figures/spider.png", isz),
            1: load("figures/rune.png", isz),
            2: load("figures/sigil.png", isz),
            3: load("figures/mark.png", isz),
            "wall": load("figures/wall.png", wsz),
            "chest": load("figures/chest.png", isz),
            "freeze": load("figures/freeze.png", isz),
            "speed": load("figures/speed.png", isz),
            "invisibility": load("figures/invisibility.png", isz),
            "duel": load("figures/duel.png", rsz),
            "base": load("figures/trophy.png", rsz),
            "timeout": load("figures/clock.png", rsz),
        }

    def _init_fonts(self):
        font_path = "fonts/MedievalSharp-Regular.ttf"
        self.fonts = {
            'title': pygame.font.Font(font_path, FONT_TITLE),
            'large': pygame.font.Font(font_path, FONT_LARGE),
            'medium': pygame.font.Font(font_path, FONT_MEDIUM),
            'small': pygame.font.Font(font_path, FONT_SMALL),
            'tiny': pygame.font.Font(font_path, FONT_TINY),
        }

    def _init_game_state(self):
        self.turn = 0
        self.game_over = False
        self.start_screen_showing = not self.headless
        self.end_screen_showing = False
        self.end_screen_time = 0
        self.end_reason = None
        self.end_winner = None
        self.winner = None

        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.items = []
        self.spells = []
        self.spell_durations = {}
        for spell in SPELL_TYPES:
            self.spell_durations[spell] = SPELL_DURATION
        self.place_walls()
        self.place_items()
        self.place_spells()

        self.pos1 = (0, 0)
        self.obj1 = (BOARD_SIZE - 1, BOARD_SIZE - 1)
        self.pos2 = (BOARD_SIZE - 1, BOARD_SIZE - 1)
        self.obj2 = (0, 0)
        self.strength1 = 0
        self.strength2 = 0
        self.spells1 = []
        self.spells2 = []
        self.active_spells1 = []
        self.active_spells2 = []
        self.player1_memory = []
        self.player2_memory = []

    def _is_connected(self):
        from collections import deque
        visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        q = deque([(0, 0)])
        visited[0][0] = True
        while q:
            x, y = q.popleft()
            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if not visited[nx][ny] and self.board[nx][ny] != "W":
                        visited[nx][ny] = True
                        q.append((nx, ny))
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if self.board[x][y] != "W" and not visited[x][y]:
                    return False
        return True

    def place_walls(self):
        max_attempts = NUM_WALLS * 20
        attempts = 0

        # First two walls are guaranteed to be at the left and right edges to prevent hardcoded routes
        a = random.randint(1, BOARD_SIZE - 2)
        b = random.randint(1, BOARD_SIZE - 2)
        self.board[0][a] = "W"
        self.items.append((0, a, "wall"))
        self.board[BOARD_SIZE - 1][b] = "W"
        self.items.append((BOARD_SIZE - 1, b, "wall"))
        # Third and fourth walls are placed randomly at the center zone of the board to add early complexity
        random_coordinates = random.sample(range(BOARD_SIZE // 4, BOARD_SIZE * 3 // 4), 4)
        x1, y1 = random_coordinates[2], random_coordinates[3]
        x2, y2 = random_coordinates[0], random_coordinates[1]
        self.board[x1][y1] = "W"
        self.board[x2][y2] = "W"
        logger.debug(f"Placed initial walls at: (0, {a}) and ({BOARD_SIZE - 1}, {b}) and ({x1}, {y1}) and ({x2}, {y2})")
        
        # Initially placed wall count
        count = 4
        
        # Place remaining walls with a bias towards clustering but ensuring connectivity
        while count < NUM_WALLS and attempts < max_attempts:
            attempts += 1
            if count > 0 and random.random() < 0.7: # 70% chance to place wall adjacent to existing one for more natural layout
                wall_positions = [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE) if self.board[x][y] == "W"]
                random.shuffle(wall_positions)
                placed = False
                for wx, wy in wall_positions:
                    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                    random.shuffle(directions)
                    for dx, dy in directions:
                        nx, ny = wx + dx, wy + dy
                        # Avoid placing wall outside the board or on starting/ending positions
                        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                            # Avoid placing wall on starting/ending positions
                            if (nx, ny) not in [(0, 0), (BOARD_SIZE - 1, BOARD_SIZE - 1)] and self.board[nx][ny] == 0:
                                # Avoid creating blocks of walls by checking adjacent cells
                                count_adj = 0
                                for ddx, ddy in directions:
                                    adj_x, adj_y = nx + ddx, ny + ddy
                                    if 0 <= adj_x < BOARD_SIZE and 0 <= adj_y < BOARD_SIZE:
                                        if self.board[adj_x][adj_y] == "W":
                                            count_adj += 1
                                if count_adj > 1:
                                    logger.debug(f"Skipping wall at ({nx}, {ny}) due to adjacent walls ({count_adj})")
                                    continue  # Skip if more than one adjacent wall to avoid blocks
                                self.board[nx][ny] = "W"
                                if self._is_connected():
                                    self.items.append((nx, ny, "wall"))
                                    count += 1
                                    placed = True
                                    break
                                else:
                                    self.board[nx][ny] = 0
                    if placed:
                        break
                if placed:
                    continue

            # Fallback to random placement if adjacent placement fails or by chance
            x = random.randint(0, BOARD_SIZE - 1)
            y = random.randint(0, BOARD_SIZE - 1)
            if (x, y) not in [(0, 0), (BOARD_SIZE - 1, BOARD_SIZE - 1)] and self.board[x][y] == 0:
                self.board[x][y] = "W"
                if self._is_connected():
                    self.items.append((x, y, "wall"))
                    count += 1
                else:
                    self.board[x][y] = 0
        
    def place_items(self):
        count = 0
        while count < NUM_ITEMS:
            x, y = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
            if (x, y) not in [(0, 0), (BOARD_SIZE - 1, BOARD_SIZE - 1)] and self.board[x][y] == 0:
                val = random.choice(ITEM_VALUES)
                self.board[x][y] = val
                self.items.append((x, y, val))
                count += 1

    def place_spells(self):
        for spell in SPELL_TYPES:
            while True:
                x, y = random.randint(3, BOARD_SIZE - 3), random.randint(3, BOARD_SIZE - 3)
                if self.board[x][y] == 0:
                    val = spell
                    self.board[x][y] = "C"
                    self.items.append((x, y, "chest"))
                    self.spells.append((x, y, val))
                    break

    def _blit_centered(self, image, cx, cy):
        rect = image.get_rect(center=(cx, cy))
        self.screen.blit(image, rect)

    def _draw_text(self, text, font_key, color, cx, cy):
        font = self.fonts[font_key]
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(cx, cy))
        self.screen.blit(surf, rect)

    def draw_board(self):
        if self.headless:
            return
        self.screen.fill(BOARD_BG)

        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                rect = (INFO_PANEL_WIDTH + x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, BOARD_BG, rect)
                pygame.draw.rect(self.screen, BOARD_OUTLINE, rect, 1)

        if logger.level == logging.DEBUG:
            font = self.fonts['tiny']
            for x in range(BOARD_SIZE):
                for y in range(BOARD_SIZE):
                    surf = font.render(f"({x},{y})", True, GRAY)
                    self.screen.blit(surf, (INFO_PANEL_WIDTH + x * CELL_SIZE + 8, y * CELL_SIZE + 8))

        for gx, gy, val in self.items:
            img = self.images[val]
            cx = INFO_PANEL_WIDTH + gx * CELL_SIZE + CELL_SIZE // 2
            cy = gy * CELL_SIZE + CELL_SIZE // 2
            self._blit_centered(img, cx, cy)

        i, s, f = False, False, False
        if "invisibility" in self.active_spells1:
            i = True
        elif "speed" in self.active_spells1:
            s = True
        elif "freeze" in self.active_spells2:
            f = True
        self.draw_player(self.pos1, "Player 1", invisible=i, speed=s, freeze=f)

        i, s, f = False, False, False
        if "invisibility" in self.active_spells2:
            i = True
        elif "speed" in self.active_spells2:
            s = True
        elif "freeze" in self.active_spells1:
            f = True
        self.draw_player(self.pos2, "Player 2", invisible=i, speed=s, freeze=f)

        img = self.images["Player 1 base"]
        cx = INFO_PANEL_WIDTH + self.obj2[0] * CELL_SIZE + CELL_SIZE // 2
        cy = self.obj2[1] * CELL_SIZE + CELL_SIZE // 2
        self._blit_centered(img, cx, cy)

        img = self.images["Player 2 base"]
        cx = INFO_PANEL_WIDTH + self.obj1[0] * CELL_SIZE + CELL_SIZE // 2
        cy = self.obj1[1] * CELL_SIZE + CELL_SIZE // 2
        self._blit_centered(img, cx, cy)

        self.draw_player_info()
        pygame.display.flip()

    def draw_end_screen(self):
        if self.headless:
            return
        width = BOARD_SIZE * CELL_SIZE + 2 * INFO_PANEL_WIDTH
        height = BOARD_SIZE * CELL_SIZE

        reason_icon = self.images[self.end_reason]
        if self.end_winner == "Player 1":
            p1_icon = self.images["Player 1 win"]
            p2_icon = self.images["Player 2 lose"]
        elif self.end_winner == "Player 2":
            p1_icon = self.images["Player 1 lose"]
            p2_icon = self.images["Player 2 win"]
        else:
            p1_icon = self.images["Player 1 lose"]
            p2_icon = self.images["Player 2 lose"]

        self.screen.fill(PANEL_BG)
        pygame.draw.rect(self.screen, BOARD_BG, (INFO_PANEL_WIDTH, 0, width - 2 * INFO_PANEL_WIDTH, height))

        self.draw_player_info()

        y_offset = CELL_SIZE * 5
        spacing = CELL_SIZE * 5

        self._blit_centered(reason_icon, width // 2, y_offset)
        self._blit_centered(p1_icon, width // 2 - spacing, y_offset)
        self._blit_centered(p2_icon, width // 2 + spacing, y_offset)

        if self.end_reason == "base":
            message = f"{self.end_winner} reached the enemy base!"
        elif self.end_reason == "duel":
            message = f"{self.end_winner} won the final duel!"
        elif self.end_reason == "timeout":
            if self.end_winner:
                message = f"Time's up! {self.end_winner} wins by points!"
            else:
                message = "Time's up! It's a draw!"
        else:
            message = "Game Over"

        self._draw_text(message, 'large', BLACK, width // 2, y_offset + CELL_SIZE * 5)
        self._draw_text("Press any key to exit...", 'small', GRAY, width // 2, y_offset + CELL_SIZE * 7)

        pygame.display.flip()

    def draw_start_screen(self):
        if self.headless:
            return
        width = BOARD_SIZE * CELL_SIZE + 2 * INFO_PANEL_WIDTH
        height = BOARD_SIZE * CELL_SIZE

        self.screen.fill(DARK_BG)

        self._draw_text("GRID DUEL", 'title', GOLD, width // 2, int(height * 0.12))
        self._draw_text("Two players enter, one leaves.", 'medium', GRAY, width // 2, int(height * 0.22))

        elf_img = self.images["Player 1 win"]
        wizard_img = self.images["Player 2 win"]
        elf_center_x = width // 4
        wizard_center_x = width * 3 // 4
        char_y = int(height * 0.55)
        self._blit_centered(elf_img, elf_center_x, char_y)
        self._blit_centered(wizard_img, wizard_center_x, char_y)

        self._draw_text(f"Player 1 ({self.name1})", 'small', WHITE, elf_center_x, int(height * 0.78))
        self._draw_text(f"Player 2 ({self.name2})", 'small', WHITE, wizard_center_x, int(height * 0.78))

        now = pygame.time.get_ticks()
        if (now // 500) % 2 == 0:
            self._draw_text("Press any key to start...", 'small', GRAY, width // 2, int(height * 0.92))

        pygame.display.flip()

    def draw_player(self, pos, image_key, invisible=False, speed=False, freeze=False):
        gx, gy = pos
        cell_x = INFO_PANEL_WIDTH + gx * CELL_SIZE
        cell_y = gy * CELL_SIZE

        if speed:
            pygame.draw.rect(self.screen, SPEED_COLOR, (cell_x, cell_y, CELL_SIZE, CELL_SIZE))

        img = self.images[image_key]
        cx = cell_x + CELL_SIZE // 2
        cy = cell_y + CELL_SIZE // 2
        self._blit_centered(img, cx, cy)

        if freeze:
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill((*FREEZE_COLOR, FREEZE_ALPHA))
            self.screen.blit(s, (cell_x, cell_y))

        if invisible:
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill((*WHITE, INVISIBLE_ALPHA))
            self.screen.blit(s, (cell_x, cell_y))

    def draw_player_info(self):
        w = INFO_PANEL_WIDTH

        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, w, BOARD_SIZE * CELL_SIZE))

        cx = w // 2
        self._blit_centered(self.images["Player 1 badge"], cx, CELL_SIZE * 2)
        self._draw_text("Player 1", 'medium', PLAYER1_COLOR, cx, CELL_SIZE * 4)
        self._draw_text(f"({self.name1})", 'small', PLAYER1_COLOR, cx, CELL_SIZE * 6)
        self._draw_text(f"Strength: {self.strength1}", 'small', BLACK, cx, CELL_SIZE * 8)
        if self.turn % 2 == 0:
            self._draw_text("> Your Turn", 'small', BLACK, cx, CELL_SIZE * 9)
        self._draw_text("Collected Spells:", 'small', BLACK, cx, CELL_SIZE * 11)
        for i, spell in enumerate(self.spells1):
            self._draw_text(f"- {spell}", 'small', BLACK, cx, CELL_SIZE * 12 + i * CELL_SIZE)
            spell_img = self.images[spell]
            self._blit_centered(spell_img, cx - CELL_SIZE * 2, CELL_SIZE * 12 + i * CELL_SIZE)

        x0 = w + BOARD_SIZE * CELL_SIZE
        pygame.draw.rect(self.screen, PANEL_BG, (x0, 0, w, BOARD_SIZE * CELL_SIZE))

        cx = x0 + w // 2
        self._blit_centered(self.images["Player 2 badge"], cx, CELL_SIZE * 2)
        self._draw_text("Player 2", 'medium', PLAYER2_COLOR, cx, CELL_SIZE * 4)
        self._draw_text(f"({self.name2})", 'small', PLAYER2_COLOR, cx, CELL_SIZE * 6)
        self._draw_text(f"Strength: {self.strength2}", 'small', BLACK, cx, CELL_SIZE * 8)
        if self.turn % 2 == 1:
            self._draw_text("> Your Turn", 'small', BLACK, cx, CELL_SIZE * 9)
        self._draw_text("Collected Spells:", 'small', BLACK, cx, CELL_SIZE * 11)
        for i, spell in enumerate(self.spells2):
            self._draw_text(f"- {spell}", 'small', BLACK, cx, CELL_SIZE * 12 + i * CELL_SIZE)
            spell_img = self.images[spell]
            self._blit_centered(spell_img, cx - CELL_SIZE * 2, CELL_SIZE * 12 + i * CELL_SIZE)

    def get_safe_move(self, agent_func, state):
        try:
            return agent_func(
                state["board"], state["objective"], state["position"],
                state["enemy_position"], state["my_strength"],
                state["enemy_strength"], state["available_spells"], state["memory"]
            )
        except Exception as e:
            logger.warning(f"Agent raised an exception during get_move: {e}")
            return "stay"

    def apply_move(self, pos, move, available_spells, active_spells):
        x, y = pos

        if move in SPELL_TYPES:
            if move not in available_spells:
                logger.warning(f"Invalid spell activation attempt: {move}")
                return pos
            available_spells.remove(move)
            active_spells.append(move)
            logger.info(f"Spells active now: {active_spells}")
            return pos
        elif move in ["up", "down", "left", "right", "stay"]:
            if move == "up":
                y -= 1
            elif move == "down":
                y += 1
            elif move == "left":
                x -= 1
            elif move == "right":
                x += 1
            x = max(0, min(BOARD_SIZE - 1, x))
            y = max(0, min(BOARD_SIZE - 1, y))
            if self.board[x][y] == "W":
                logger.warning("Player hit a wall!")
                return pos
            return (x, y)
        else:
            logger.warning(f"Invalid move: {move}")
            return pos

    def resolve_duel(self, strength1, strength2):
        if strength1 < 1 or strength2 < 1:
            min_strength = min(strength1, strength2)
            strength1 = strength1 - min_strength + 1
            strength2 = strength2 - min_strength + 1
        winner = random.choices(
            population=["Player 1", "Player 2"],
            weights=[strength1, strength2],
            k=1
        )[0]
        return winner

    def play_turn(self):
        if self.turn >= MAX_TURNS:
            logger.info("Game over. Max turns reached.")
            if self.strength1 > self.strength2:
                logger.info("Player 1 wins with higher strength!")
                self.winner = self.name1
                self.end_winner = "Player 1"
            elif self.strength1 < self.strength2:
                logger.info("Player 2 wins with higher strength!")
                self.winner = self.name2
                self.end_winner = "Player 2"
            else:
                logger.info("It's a draw!")
                self.winner = None
                self.end_winner = None
            self.end_reason = "timeout"
            self.game_over = True
            if not self.headless:
                self.end_screen_time = pygame.time.get_ticks() + DELAY_MS * 2
            return

        for i, (agent, pos, opp_pos, str_self, str_opp, memory, obj, available_spells, active_spells) in enumerate([
            (self.agent1, self.pos1, self.pos2, self.strength1, self.strength2, self.player1_memory, self.obj1, self.spells1, self.active_spells1),
            (self.agent2, self.pos2, self.pos1, self.strength2, self.strength1, self.player2_memory, self.obj2, self.spells2, self.active_spells2),
        ]):
            if i == 0 and "freeze" in self.active_spells2:
                logger.info("Player 1 is frozen this turn!")
                self.spell_durations["freeze"] -= 1
                if self.spell_durations["freeze"] == 0:
                    self.active_spells2.remove("freeze")
                continue
            elif i == 1 and "freeze" in self.active_spells1:
                logger.info("Player 2 is frozen this turn!")
                self.spell_durations["freeze"] -= 1
                if self.spell_durations["freeze"] == 0:
                    self.active_spells1.remove("freeze")
                continue

            if i == 0 and "speed" in self.active_spells2:
                if self.turn % 2 == 1:
                    logger.info("Player 2 has speed spell active and moves twice!")
                    self.spell_durations["speed"] -= 1
                    if self.spell_durations["speed"] == 0:
                        self.active_spells2.remove("speed")
                    continue
            elif i == 1 and "speed" in self.active_spells1:
                if self.turn % 2 == 1:
                    logger.info("Player 1 has speed spell active and moves twice!")
                    self.spell_durations["speed"] -= 1
                    if self.spell_durations["speed"] == 0:
                        self.active_spells1.remove("speed")
                    continue

            if i == 0 and "invisibility" in self.active_spells2:
                self.spell_durations["invisibility"] -= 1
                opp_pos = (-1, -1)
                if self.spell_durations["invisibility"] == 0:
                    self.active_spells2.remove("invisibility")
            elif i == 1 and "invisibility" in self.active_spells1:
                self.spell_durations["invisibility"] -= 1
                opp_pos = (-1, -1)
                if self.spell_durations["invisibility"] == 0:
                    self.active_spells1.remove("invisibility")

            state = {
                "position": pos,
                "enemy_position": opp_pos,
                "board": tuple(tuple(row) for row in self.board),
                "my_strength": str_self,
                "enemy_strength": str_opp,
                "memory": memory,
                "objective": obj,
                "available_spells": tuple(available_spells),
            }
            move = self.get_safe_move(agent, state)
            new_pos = self.apply_move(pos, move, available_spells, active_spells)
            gx, gy = new_pos
            val = self.board[gx][gy]
            if val != 0:
                if isinstance(val, int):
                    logger.info(f"Player {i+1} collects item ({val}) at {new_pos}")
                    str_self += val
                else:
                    for sx, sy, spell in self.spells:
                        if (sx, sy) == new_pos:
                            logger.info(f"Player {i+1} collects spell ({spell}) at {new_pos}")
                            available_spells.append(spell)
                self.board[gx][gy] = 0
                self.items = [(ix, iy, v) for (ix, iy, v) in self.items if (ix, iy) != (gx, gy)]

            if i == 0:
                self.pos1 = new_pos
                self.strength1 = str_self
                self.spells1 = available_spells
            else:
                self.pos2 = new_pos
                self.strength2 = str_self
                self.spells2 = available_spells

            if new_pos == obj:
                self.draw_board()
                logger.info(f"Player {i+1} reached opponent base and wins!")
                self.winner = self.name1 if i == 0 else self.name2
                self.end_winner = f"Player {i+1}"
                self.end_reason = "base"
                self.game_over = True
                if not self.headless:
                    self.end_screen_time = pygame.time.get_ticks() + DELAY_MS * 2
                return

        if not ("invisibility" in self.active_spells1 or "invisibility" in self.active_spells2):
            x1, y1 = self.pos1
            x2, y2 = self.pos2
            dx, dy = abs(x1 - x2), abs(y1 - y2)
            if (dx, dy) in ((0, 0), (0, 1), (1, 0), (1, 1)):
                logger.info(f"Duel at {self.pos1} (Player 1) - {self.pos2} (Player 2)!")
                self.draw_board()
                duel_winner = self.resolve_duel(self.strength1, self.strength2)
                if duel_winner == "Player 1":
                    logger.info("Player 1 wins the duel!")
                    self.winner = self.name1
                else:
                    logger.info("Player 2 wins the duel!")
                    self.winner = self.name2
                self.end_winner = duel_winner
                self.end_reason = "duel"
                self.game_over = True
                if not self.headless:
                    self.end_screen_time = pygame.time.get_ticks() + DELAY_MS * 2
                return

        self.turn += 1
        self.draw_board()

    def _run_headless(self):
        while not self.game_over:
            self.play_turn()

    def _run_gui(self):
        while self.start_screen_showing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()
                    return
                if event.type == pygame.KEYDOWN:
                    if self.audio_enabled:
                        self.lobby_theme.stop()
                        self.main_theme.play(loops=-1)
                    self.start_screen_showing = False
            self.draw_start_screen()
            self.clock.tick(30)

        self.draw_board()
        next_turn_time = pygame.time.get_ticks() + DELAY_MS
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.debug("DIAG: QUIT event received, scheduling faulthandler dump")
                    sys.stdout.flush()
                    faulthandler.dump_traceback_later(3, repeat=False)
                    self.cleanup()
                    return
                if self.game_over and event.type == pygame.KEYDOWN:
                    logger.debug("DIAG: KEYDOWN event received (game_over), scheduling faulthandler dump")
                    sys.stdout.flush()
                    faulthandler.dump_traceback_later(3, repeat=False)
                    self.cleanup()
                    return

            now = pygame.time.get_ticks()
            if not self.game_over:
                if now >= next_turn_time:
                    self.play_turn()
                    next_turn_time = now + DELAY_MS
            else:
                if self.end_screen_showing:
                    self.draw_end_screen()
                elif now >= self.end_screen_time:
                    if self.audio_enabled:
                        logger.debug("DIAG: stopping main_theme...")
                        sys.stdout.flush()
                        self.main_theme.stop()
                        logger.debug("DIAG: main_theme stopped, playing match_end (loops=-1)...")
                        sys.stdout.flush()
                        self.match_end.play(loops=-1)
                        logger.debug("DIAG: match_end play returned")
                        sys.stdout.flush()
                    self.end_screen_showing = True
                else:
                    self.draw_board()

            self.clock.tick(30)

    def run(self):
        if self.headless:
            self._run_headless()
        else:
            self._run_gui()

    def cleanup(self):
        logger.debug("CLEANUP: starting cleanup()")
        sys.stdout.flush()
        if self.audio_enabled:
            logger.debug("CLEANUP: calling pygame.mixer.stop()...")
            sys.stdout.flush()
            pygame.mixer.stop()
            logger.debug("CLEANUP: pygame.mixer.stop() returned")
            sys.stdout.flush()
        logger.debug("CLEANUP: calling pygame.quit()...")
        sys.stdout.flush()
        pygame.quit()
        logger.debug("CLEANUP: pygame.quit() returned")
        sys.stdout.flush()

    def get_winner(self):
        return self.winner


if __name__ == "__main__":
    GameApp("agent_value_bfs", "agent_value_bfs")
