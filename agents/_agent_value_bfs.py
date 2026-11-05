import heapq
import random
from math import inf

DIRECTIONS = [(-1, 0, 'left'), (1, 0, 'right'), (0, -1, 'up'), (0, 1, 'down')]

MIN_WEIGHT = 5
MAX_WEIGHT = 10
MAX_DIST = 30
CHEST_VALUE = 5


def cell_value(board, x, y):
    val = board[x][y]
    if isinstance(val, int):
        return val
    if val == 'C':
        return CHEST_VALUE
    return 0


def get_move(board, objective, position, enemy_position, my_strength, enemy_strength, available_spells, memory):
    x, y = position
    ox, oy = objective

    if available_spells:
        ex, ey = enemy_position
        dist_to_goal = abs(x - ox) + abs(y - oy)
        dist_to_enemy = abs(x - ex) + abs(y - ey) if ex != -1 else 99

        if "speed" in available_spells and dist_to_goal > 8:
            return "speed"
        if "invisibility" in available_spells and dist_to_enemy <= 3:
            return "invisibility"
        if "freeze" in available_spells and dist_to_enemy <= 2:
            return "freeze"
        if random.random() > 0.7:
            return random.choice(available_spells)

    board_size = len(board)

    dist_remaining = abs(x - ox) + abs(y - oy)
    weight = MAX_WEIGHT - (MAX_WEIGHT - MIN_WEIGHT) * dist_remaining / MAX_DIST
    weight = int(round(weight))
    weight = max(MIN_WEIGHT, min(MAX_WEIGHT, weight))

    start = (x, y)
    goal = (ox, oy)

    if start == goal:
        return 'stay'

    pq = [(0, x, y)]
    costs = {start: 0}
    parents = {}

    while pq:
        current_cost, cx, cy = heapq.heappop(pq)

        if (cx, cy) == goal:
            path = []
            cur = (cx, cy)
            while cur in parents:
                path.append(cur)
                cur = parents[cur]
            path.append(start)
            path.reverse()
            if len(path) > 1:
                nx, ny = path[1]
                dx, dy = nx - x, ny - y
                for ddx, ddy, direction in DIRECTIONS:
                    if ddx == dx and ddy == dy:
                        return direction
            return 'stay'

        if current_cost > costs.get((cx, cy), inf):
            continue

        for dx, dy, _ in DIRECTIONS:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < board_size and 0 <= ny < board_size):
                continue
            if board[nx][ny] == 'W':
                continue

            edge_cost = weight - cell_value(board, nx, ny)
            new_cost = current_cost + edge_cost

            if new_cost < costs.get((nx, ny), inf):
                costs[(nx, ny)] = new_cost
                parents[(nx, ny)] = (cx, cy)
                heapq.heappush(pq, (new_cost, nx, ny))

    return 'stay'
