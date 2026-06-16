import tkinter as tk
from PIL import Image, ImageTk
import importlib
import random
import logging

# Game configuration
BOARD_SIZE = 16
CELL_SIZE = 32
NUM_ITEMS = 20
ITEM_VALUES = [-3, -2, -1, 1, 2, 3]
NUM_WALLS = 15
SPELL_TYPES = ["freeze", "speed", "invisibility"]
SPELL_DURATION = 5
MAX_TURNS = 120
DELAY_MS = 500  # Time between turns
INFO_PANEL_WIDTH = CELL_SIZE * 8  # Width of side lanes
FONT_LARGE = CELL_SIZE // 2
FONT_MEDIUM = int(FONT_LARGE * 0.875)
FONT_SMALL = int(FONT_MEDIUM * 0.875)
FONT_TINY = FONT_SMALL // 2

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("grid_duel")

class GameApp:
    def __init__(self, root, agent1_module, agent2_module):
        # Configure main window
        self.root = root
        total_width = BOARD_SIZE * CELL_SIZE + 2 * INFO_PANEL_WIDTH
        self.canvas = tk.Canvas(root, width=total_width, height=BOARD_SIZE * CELL_SIZE)
        self.canvas.pack()
        # Try to load agents from modules
        try:
            self.agent1 = importlib.import_module(agent1_module).get_move
            self.agent2 = importlib.import_module(agent2_module).get_move
        except Exception as e:
            logger.exception(f"Error importing agent: {e}")
            exit()
        # Load images
        image_size = (int(CELL_SIZE*0.95), int(CELL_SIZE*0.95)) # Images take 90% of cell size
        wall_size = (CELL_SIZE, CELL_SIZE) # Wall icon takes full cell size
        badge_size = (CELL_SIZE*3, CELL_SIZE*3) # Player icon size at the side panels top position
        player_size = (CELL_SIZE*6, CELL_SIZE*6) # Player icon size at end screen
        reason_size = (CELL_SIZE*2, CELL_SIZE*2) # Reason icon size at end screen
        self.images = {
            "Player 1": ImageTk.PhotoImage(Image.open("figures/elf.png").resize(image_size)),
            "Player 1 badge": ImageTk.PhotoImage(Image.open("figures/elf.png").resize(badge_size)),
            "Player 1 win": ImageTk.PhotoImage(Image.open("figures/elf_full.png").resize(player_size)),
            "Player 1 lose": ImageTk.PhotoImage(Image.open("figures/elf_full_lose.png").resize(player_size)),
            "Player 1 base": ImageTk.PhotoImage(Image.open("figures/elf_base.png").resize(image_size)),
            "Player 2": ImageTk.PhotoImage(Image.open("figures/wizard.png").resize(image_size)),
            "Player 2 badge": ImageTk.PhotoImage(Image.open("figures/wizard.png").resize(badge_size)),
            "Player 2 win": ImageTk.PhotoImage(Image.open("figures/wizard_full.png").resize(player_size)),
            "Player 2 lose": ImageTk.PhotoImage(Image.open("figures/wizard_full_lose.png").resize(player_size)),
            "Player 2 base": ImageTk.PhotoImage(Image.open("figures/wizard_base.png").resize(image_size)),
            -3: ImageTk.PhotoImage(Image.open("figures/rex.png").resize(image_size)),
            -2: ImageTk.PhotoImage(Image.open("figures/snake.png").resize(image_size)),
            -1: ImageTk.PhotoImage(Image.open("figures/spider.png").resize(image_size)),
            1: ImageTk.PhotoImage(Image.open("figures/rune.png").resize(image_size)),
            2: ImageTk.PhotoImage(Image.open("figures/sigil.png").resize(image_size)),
            3: ImageTk.PhotoImage(Image.open("figures/mark.png").resize(image_size)),
            "wall": ImageTk.PhotoImage(Image.open("figures/wall.png").resize(wall_size)),
            "chest": ImageTk.PhotoImage(Image.open("figures/chest.png").resize(image_size)),
            "freeze": ImageTk.PhotoImage(Image.open("figures/freeze.png").resize(image_size)),
            "speed": ImageTk.PhotoImage(Image.open("figures/speed.png").resize(image_size)),
            "invisibility": ImageTk.PhotoImage(Image.open("figures/invisibility.png").resize(image_size)),
            "duel": ImageTk.PhotoImage(Image.open("figures/duel.png").resize(reason_size)),
            "base": ImageTk.PhotoImage(Image.open("figures/trophy.png").resize(reason_size)),
            "timeout": ImageTk.PhotoImage(Image.open("figures/clock.png").resize(reason_size)),
        }

        # Game setup
        self.turn = 0
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.items = []
        self.spells = []
        # Set spells duration in a dictionary
        self.spell_durations = {}
        for spell in SPELL_TYPES:
            self.spell_durations[spell] = SPELL_DURATION
        self.place_walls()
        self.place_items()
        self.place_spells()
        # Show board contents
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                logger.debug("board[%d][%d] = %s", x, y, self.board[x][y])
            logger.debug("-" * 50)
        self.pos1 = (0, 0)
        self.obj1 = (BOARD_SIZE - 1, BOARD_SIZE - 1)
        self.name1 = agent1_module
        self.pos2 = (BOARD_SIZE - 1, BOARD_SIZE - 1)
        self.obj2 = (0, 0)
        self.name2 = agent2_module
        self.strength1 = 0
        self.strength2 = 0
        self.spells1 = []
        self.spells2 = []
        self.active_spells1 = []
        self.active_spells2 = []
        self.player1_memory = []
        self.player2_memory = []
        self.winner = None
        # Draws main board with items and players
        self.draw_board()
        # Start game loop after delay
        self.root.after(DELAY_MS, self.play_turn)

    def place_walls(self):
        count = 0
        # place 1 third of walls randomly
        while count < NUM_WALLS // 3:
            x, y = random.randint(3, BOARD_SIZE-3), random.randint(3, BOARD_SIZE-3)
            if (x, y) not in [(0, 0), (BOARD_SIZE-1, BOARD_SIZE-1)] and self.board[x][y] == 0:
                self.board[x][y] = "W"
                self.items.append((x, y, "wall"))
                count += 1
        # place remainig walls next to existing walls
        while count < NUM_WALLS:
            wall_positions = [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE) if self.board[x][y] == "W"]
            if not wall_positions:
                break
            wx, wy = random.choice(wall_positions)
            directions = [(0,1), (1,0), (0,-1), (-1,0)]
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = wx + dx, wy + dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if (nx, ny) not in [(0, 0), (BOARD_SIZE-1, BOARD_SIZE-1)] and self.board[nx][ny] == 0:
                        self.board[nx][ny] = "W"
                        self.items.append((nx, ny, "wall"))
                        count += 1
                        break

    def place_items(self):
        # Place a number of items with random positions and values
        count = 0
        while count < NUM_ITEMS:
            x, y = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
            if (x, y) not in [(0, 0), (BOARD_SIZE-1, BOARD_SIZE-1)] and self.board[x][y] == 0:
                val = random.choice(ITEM_VALUES)
                self.board[x][y] = val
                self.items.append((x, y, val))
                count += 1

    def place_spells(self):
        # Place exactly one spell of each type
        for spell in SPELL_TYPES:
            while True:
                x, y = random.randint(3, BOARD_SIZE-3), random.randint(3, BOARD_SIZE-3)
                if self.board[x][y] == 0:
                    val = spell
                    self.board[x][y] = "C"
                    self.items.append((x, y, "chest"))
                    self.spells.append((x, y, val))
                    break

    def draw_board(self):
        self.canvas.delete("all")

        # Draw main board
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                self.canvas.create_rectangle(
                    INFO_PANEL_WIDTH + x * CELL_SIZE, y * CELL_SIZE,
                    INFO_PANEL_WIDTH + (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                    fill="#dcbc8d", outline='#956841'
                )
        
        # Draw small x, y label inside grid cells
        if logger.level == logging.DEBUG:
            for x in range(BOARD_SIZE):
                for y in range(BOARD_SIZE):
                    self.canvas.create_text(
                        INFO_PANEL_WIDTH + x * CELL_SIZE + 8,
                        y * CELL_SIZE + 8,
                        text=f"({x},{y})",
                        anchor="nw",
                        fill="gray",
                        font=('Arial', FONT_TINY)
                    )

        # Draw items
        for x, y, val in self.items:
            img = self.images[val]
            self.canvas.create_image(INFO_PANEL_WIDTH + x * CELL_SIZE + CELL_SIZE // 2,
                                     y * CELL_SIZE + CELL_SIZE // 2,
                                     image=img)

        # Draw players considering active spells
        i, s, f = False, False, False # Player 1
        if "invisibility" in self.active_spells1:
            i = True
        elif "speed" in self.active_spells1:
            s = True
        elif "freeze" in self.active_spells2:
            f = True    
        self.draw_player(self.pos1, "Player 1", invisible=i, speed=s, freeze=f)
        
        i, s, f = False, False, False # Player 2
        if "invisibility" in self.active_spells2:
            i = True
        elif "speed" in self.active_spells2:
            s = True
        elif "freeze" in self.active_spells1:
            f = True
        self.draw_player(self.pos2, "Player 2", invisible=i, speed=s, freeze=f)
        
        # Draw objectives
        img = self.images["Player 1 base"]
        self.canvas.create_image(INFO_PANEL_WIDTH + self.obj2[0] * CELL_SIZE + CELL_SIZE // 2,
                                 self.obj2[1] * CELL_SIZE + CELL_SIZE // 2,
                                 image=img)
        #self.draw_objective(self.obj1, "orange")
        img = self.images["Player 2 base"]
        self.canvas.create_image(INFO_PANEL_WIDTH + self.obj1[0] * CELL_SIZE + CELL_SIZE // 2,
                                 self.obj1[1] * CELL_SIZE + CELL_SIZE // 2,
                                 image=img)
        #self.draw_objective(self.obj2, "blue")

        # Draw info panels
        self.draw_player_info()

    def draw_player_info(self):
        # Player 1 panel (left)
        x_center = INFO_PANEL_WIDTH//2
        self.canvas.create_rectangle(0, 0, INFO_PANEL_WIDTH, BOARD_SIZE * CELL_SIZE, fill="#d4d4d4")

        # Player badge at the top of the info panel
        img = self.images["Player 1 badge"]
        self.canvas.create_image(x_center, CELL_SIZE * 2, image=img)

        self.canvas.create_text(x_center, CELL_SIZE * 4, text="Player 1", fill="#2f5b40", font=('Arial', FONT_MEDIUM, 'bold'))
        self.canvas.create_text(x_center, CELL_SIZE * 6, text="("+self.name1+")", fill="#2f5b40", font=('Arial', FONT_MEDIUM, 'bold'))
        self.canvas.create_text(x_center, CELL_SIZE * 8, text=f"Strength: {self.strength1}", font=('Arial', FONT_SMALL))
        if self.turn % 2 == 0:
            self.canvas.create_text(INFO_PANEL_WIDTH//2, CELL_SIZE * 9, text="➤ Your Turn", fill="black", font=('Arial', FONT_SMALL, 'italic'))

        # Collected spells information
        self.canvas.create_text(x_center, CELL_SIZE * 11, text="Collected Spells:", font=('Arial', FONT_SMALL, 'underline'))
        for i, spell in enumerate(self.spells1):
            self.canvas.create_text(x_center, CELL_SIZE * 12 + i * CELL_SIZE, text=f"- {spell}", font=('Arial', FONT_SMALL))

            # Draw the spell image next to each spell
            img = self.images[spell]
            self.canvas.create_image(x_center - CELL_SIZE * 2, CELL_SIZE * 12 + i * CELL_SIZE, image=img)

        # Player 2 panel (right)
        x0 = INFO_PANEL_WIDTH + BOARD_SIZE * CELL_SIZE
        x_center = x0 + INFO_PANEL_WIDTH//2
        self.canvas.create_rectangle(x0, 0, x0 + INFO_PANEL_WIDTH, BOARD_SIZE * CELL_SIZE, fill='#d4d4d4')
        
        # Player badge at the top of the info panel
        img = self.images["Player 2 badge"]
        self.canvas.create_image(x_center, CELL_SIZE * 2, image=img)

        self.canvas.create_text(x_center, CELL_SIZE * 4, text="Player 2", fill="#343c7d", font=('Arial', FONT_MEDIUM, 'bold'))
        self.canvas.create_text(x_center, CELL_SIZE * 6, text="("+self.name2+")", fill="#343c7d", font=('Arial', FONT_MEDIUM, 'bold'))
        self.canvas.create_text(x_center, CELL_SIZE * 8, text=f"Strength: {self.strength2}", font=('Arial', FONT_SMALL))
        if self.turn % 2 == 1:
            self.canvas.create_text(x_center, CELL_SIZE * 9, text="➤ Your Turn", fill="black", font=('Arial', FONT_SMALL, 'italic'))
        
        # Collected spells information
        self.canvas.create_text(x_center, CELL_SIZE * 11, text="Collected Spells:", font=('Arial', FONT_SMALL, 'underline'))
        for i, spell in enumerate(self.spells2):
            # Draw spell name aligned to the left
            self.canvas.create_text(x_center, CELL_SIZE * 12 + i * CELL_SIZE, text=f"- {spell}", font=('Arial', FONT_SMALL))

            # Draw the spell image next to each spell
            img = self.images[spell]
            self.canvas.create_image(x_center - CELL_SIZE * 2, CELL_SIZE * 12 + i * CELL_SIZE, image=img)

    def draw_objective(self, pos, color):
        x, y = pos
        self.canvas.create_oval(
            (x*CELL_SIZE + 10)+INFO_PANEL_WIDTH, y*CELL_SIZE + 10,
            ((x+1)*CELL_SIZE - 10)+INFO_PANEL_WIDTH, (y+1)*CELL_SIZE - 10,
            outline=color
        )

    def draw_player(self, pos, image, invisible=False, speed=False, freeze=False):
        x, y = pos

        # Draw light red background if speed active
        if speed:
            self.canvas.create_rectangle(
                INFO_PANEL_WIDTH + x * CELL_SIZE, y * CELL_SIZE,
                INFO_PANEL_WIDTH + (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill="#ff7c7c"
            )

        # Draw player image
        img = self.images[image]
        self.canvas.create_image(INFO_PANEL_WIDTH + x * CELL_SIZE + CELL_SIZE // 2,
                                y * CELL_SIZE + CELL_SIZE // 2,
                                image=img)

        # Draw light blue background if frozen
        if freeze:
            self.canvas.create_rectangle(
                INFO_PANEL_WIDTH + x * CELL_SIZE, y * CELL_SIZE,
                INFO_PANEL_WIDTH + (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill="#74f8ff", stipple='gray50'
            )

        # Overlay a white transparency to indicate invisibility
        if invisible:
            self.canvas.create_rectangle(
                INFO_PANEL_WIDTH + x * CELL_SIZE, y * CELL_SIZE,
                INFO_PANEL_WIDTH + (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill='white', stipple='gray50'
            )

    def get_safe_move(self, agent_func, state):
        board = state["board"]
        objective = state["objective"]
        position = state["position"]
        enemy_position = state["enemy_position"]
        my_strength = state["my_strength"]
        enemy_strength = state["enemy_strength"]
        available_spells = state["available_spells"]
        memory = state["memory"]
        try:
            return agent_func(board, objective, position, enemy_position, my_strength, enemy_strength, available_spells, memory)
        except Exception as e:
            # Show summarized information about the exception in the log
            logger.warning(f"Agent raised an exception during get_move: {e}")
            return "stay"

    def apply_move(self, pos, move, available_spells, active_spells):
        x, y = pos

        # Check if player is activating a spell
        if move in SPELL_TYPES:
            # Check if player actually has the spell they are activating
            if move not in available_spells:
                logger.warning(f"Invalid spell activation attempt: {move}")
                return pos
            # Take activated spell out of the available spells list and add to active spells
            available_spells.remove(move)
            active_spells.append(move)
            logger.info(f"Spells active now: {active_spells}")
            return pos
        # Check if player is moving to valid direction
        elif move in ["up", "down", "left", "right", "stay"]:
            if move == "up": y -= 1
            elif move == "down": y += 1
            elif move == "left": x -= 1
            elif move == "right": x += 1
            # Make sure players never leave the board
            x = max(0, min(BOARD_SIZE-1, x))
            y = max(0, min(BOARD_SIZE-1, y))
            if self.board[x][y] == "W":  # Wall collision
                logger.warning("Player hit a wall!")
                return pos  # Stay in place if hitting a wall
            return (x, y)
        else:
            # Invalid move
            logger.warning(f"Invalid move: {move}")
            return pos

    def resolve_duel(self, strength1, strength2):
        # Adjust weights in case of negative of zero strength
        if strength1 < 1 or strength2 < 1:
            min_strength = min(strength1, strength2)
            strength1 = strength1 - min_strength + 1
            strength2 = strength2 - min_strength + 1
        winner = random.choices(
            population=["Player 1", "Player 2"],
            weights=[strength1, strength2],
            k=1
        )[0] # Returns a list with k (1) random player considering weights
        return winner

    def show_end_screen(self, reason, winner=None):
        # Icons
        reason_icon = self.images[reason]
        if winner == "Player 1":
            player1_icon = self.images["Player 1 win"]
            player2_icon = self.images["Player 2 lose"]
        elif winner == "Player 2":
            player1_icon = self.images["Player 1 lose"]
            player2_icon = self.images["Player 2 win"]
        else:
            player1_icon = self.images["Player 1 lose"]
            player2_icon = self.images["Player 2 lose"]
        # Canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Background
        self.canvas.create_rectangle(INFO_PANEL_WIDTH, 0, width-INFO_PANEL_WIDTH,
                                     height, fill='#dcbc8d')

        # Draw icons
        y_offset = CELL_SIZE * 5
        spacing = CELL_SIZE * 5

        # Draw reason icon at top center
        self.canvas.create_image(width//2, y_offset, image=reason_icon)

        # Player icons
        self.canvas.create_image(width//2 - spacing, y_offset, image=player1_icon)
        self.canvas.create_image(width//2 + spacing, y_offset, image=player2_icon)
        
        # Title message
        if reason == "base":
            message = f"{winner} reached the enemy base!"
        elif reason == "duel":
            message = f"{winner} won the final duel!"
        elif reason == "timeout":
            if winner:
                message = f"Time's up! {winner} wins by points!"
            else:
                message = "Time's up! It's a draw!"
        else:
            message = "Game Over"

        self.canvas.create_text(
            width // 2,
            y_offset + CELL_SIZE * 5,
            text=message,
            fill="black",
            font=("Helvetica", FONT_LARGE, "bold")
        )

        # Exit Button
        self.canvas.create_text(
            width // 2,
            y_offset + CELL_SIZE * 7,
            text="Press any key to exit...",
            fill="gray",
            font=("Helvetica", FONT_MEDIUM, "italic")
        )

        # Bind key press to exit or restart
        self.root.bind("<Key>", lambda event: self.root.destroy())


    def play_turn(self):
        logger.debug(f"Turn: {self.turn}")
        # Check for end of game by reaching turns limit
        if self.turn >= MAX_TURNS:
            logger.info("Game over. Max turns reached.")
            if self.strength1 > self.strength2:
                logger.info("Player 1 wins with higher strength!")
                self.winner = self.name1
                self.root.after(DELAY_MS*2, lambda: self.show_end_screen(reason="timeout", winner="Player 1"))
                return
            elif self.strength1 < self.strength2:
                logger.info("Player 2 wins with higher strength!")
                self.root.after(DELAY_MS*2, lambda: self.show_end_screen(reason="timeout", winner="Player 2"))
                self.winner = self.name2
                return
            else:
                logger.info("It's a draw!")
                self.root.after(DELAY_MS*2, lambda: self.show_end_screen(reason="timeout"))
            return None

        # Process both players moves
        for i, (agent, pos, opp_pos, str_self, str_opp, memory, obj, available_spells, active_spells) in enumerate([
            (self.agent1, self.pos1, self.pos2, self.strength1, self.strength2, self.player1_memory, self.obj1, self.spells1, self.active_spells1),
            (self.agent2, self.pos2, self.pos1, self.strength2, self.strength1, self.player2_memory, self.obj2, self.spells2, self.active_spells2),
        ]):
            # Process freeze spell effect
            if i == 0 and "freeze" in self.active_spells2:
                logger.info("Player 1 is frozen this turn!")
                logger.debug(f"Freeze turns left: {self.spell_durations['freeze']}")
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
            
            # Process speed spell effect (allows player to move twice)
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
            
            # Process invisibility spell effect
            if i == 0 and "invisibility" in self.active_spells2:
                self.spell_durations["invisibility"] -= 1
                # Invalidate enemy position while invisible
                opp_pos = (-1, -1)
                if self.spell_durations["invisibility"] == 0:
                    self.active_spells2.remove("invisibility")
            elif i == 1 and "invisibility" in self.active_spells1:
                self.spell_durations["invisibility"] -= 1
                # Invalidate enemy position while invisible
                opp_pos = (-1, -1)
                if self.spell_durations["invisibility"] == 0:
                    self.active_spells1.remove("invisibility")

            # Creates a copy of the board to pass it into the player's function
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
            x, y = new_pos
            val = self.board[x][y]
            # Check if player collects item or spell
            if val != 0:
                # Check for integer items (positive or negative)
                if type(val) == int:
                    logger.info(f"Player {i+1} collects item ({val}) at {new_pos}")
                    str_self += val
                else:
                    # Player collected spell
                    for sx, sy, spell in self.spells:
                        if (sx, sy) == new_pos:
                            logger.info(f"Player {i+1} collects spell ({spell}) at {new_pos}")
                            available_spells.append(spell)
                # Reset board position (remove item or spell)
                self.board[x][y] = 0
                self.items = [(ix, iy, v) for (ix, iy, v) in self.items if (ix, iy) != (x, y)]
            
            # Update current players position and strength
            if i == 0:
                self.pos1 = new_pos
                self.strength1 = str_self
                self.spells1 = available_spells
            else:
                self.pos2 = new_pos
                self.strength2 = str_self
                self.spells2 = available_spells

            logger.debug(f"Player {i+1} at {new_pos}!")
            if new_pos == obj:
                self.draw_board() # Draw board one last time to place players at final position
                logger.info(f"Player {i+1} reached opponent base and wins!")
                self.root.after(DELAY_MS*2, lambda: self.show_end_screen(reason="base", winner=f"Player {i+1}"))
                self.winner = self.name1 if i == 0 else self.name2
                return

        # Verify duel
        if not ("invisibility" in self.active_spells1 or "invisibility" in self.active_spells2):
            x1, y1 = self.pos1
            x2, y2 = self.pos2
            dx, dy = abs(x1 - x2), abs(y1 - y2)
            if (dx, dy) in ((0, 0), (0, 1), (1, 0), (1, 1)): # absolute distance at most 1 cell
                logger.info(f"Duel at {self.pos1} (Player 1) - {self.pos2} (Player 2)!")
                self.draw_board() # Draw board one last time to place players at duel position
                if self.resolve_duel(self.strength1, self.strength2) == "Player 1":
                    logger.info("Player 1 wins the duel!")
                    self.winner = self.name1
                    self.root.after(DELAY_MS*2, lambda: self.show_end_screen(reason="duel", winner="Player 1"))
                else:
                    logger.info("Player 2 wins the duel!")
                    self.winner = self.name2
                    self.root.after(DELAY_MS*2, lambda: self.show_end_screen(reason="duel", winner="Player 2"))
                return

        self.turn += 1
        self.draw_board()
        self.root.after(DELAY_MS, self.play_turn)

    def get_winner(self):
        return self.winner
    
if __name__ == "__main__":
    # Example usage
    root = tk.Tk()
    root.title("Grid Duel Game")
    app = GameApp(root, "agent_rand_spell", "agent_rand_spell")
    root.mainloop()
