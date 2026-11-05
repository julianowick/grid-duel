import random
from collections import deque

DIRECTIONS = [(-1, 0, 'left'), (1, 0, 'right'), (0, -1, 'up'), (0, 1, 'down')]

def get_move(board, objective, position, enemy_position, my_strength, enemy_strength, available_spells, memory):
    x, y = position
    ox, oy = objective

    # Minimal spell usage
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

    def bfs(start, goal):
        if start == goal:
            return [start]

        queue = deque([start])
        visited = {start: None}

        while queue:
            cx, cy = queue.popleft()

            for dx, dy, _ in DIRECTIONS:
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < board_size and 0 <= ny < board_size):
                    continue
                if board[nx][ny] == 'W' or (nx, ny) in visited:
                    continue
                visited[(nx, ny)] = (cx, cy)
                if (nx, ny) == goal:
                    path = []
                    cur = (nx, ny)
                    while cur is not None:
                        path.append(cur)
                        cur = visited[cur]
                    path.reverse()
                    return path
                queue.append((nx, ny))

        return None

    # Check cached path
    if memory:
        cached = memory[0]
        if 'path' in cached:
            path = cached['path']
            if path and path[0] == position:
                if len(path) > 1:
                    next_pos = path[1]
                    memory[0] = {'path': path[1:]}
                    dx = next_pos[0] - x
                    dy = next_pos[1] - y
                    for ddx, ddy, direction in DIRECTIONS:
                        if ddx == dx and ddy == dy:
                            return direction
                return 'stay'

    # Compute new path
    path = bfs(position, objective)
    if path and len(path) > 1:
        memory.clear()
        memory.append({'path': path})
        next_pos = path[1]
        dx = next_pos[0] - x
        dy = next_pos[1] - y
        for ddx, ddy, direction in DIRECTIONS:
            if ddx == dx and ddy == dy:
                return direction

    return 'stay'
