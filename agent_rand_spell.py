import random

def get_move(board, objective, position, enemy_position, my_strength, enemy_strength, available_spells, memory):

    # Check for collected spells
    if available_spells:
        # 30% chance of activating a spell
        if random.random() > 0.99:
            return random.choice(available_spells)
    
    # By default set objective to current objective
    ox, oy = objective
    x, y = position

    # Set objective to nearest chest on the board (if any)
    chests = []
    for i, row in enumerate(board):
        for j, cell in enumerate(row):
            if cell == 'C':
                chests.append((i, j))
    #print(" ====== New round ====== ")
    #print("Current position:", position)
    #print("Chests found at:", chests)
    if chests:
        distances = [abs(x - i) + abs(y - j) for (i, j) in chests]
        nearest_chest = chests[distances.index(min(distances))]
        #print("Distances to chests:", distances)
        ox, oy = nearest_chest
        #print("New objective set to nearest chest at:", nearest_chest)
    
    moves = ['stay']
    if x > ox:
        moves += ['left', 'left'] # move towards the objective
    elif x < ox:
        moves += ['right', 'right'] # move towards the objective
    if y > oy:
        moves += ['up', 'up'] # move towards the objective
    elif y < oy:
        moves += ['down', 'down'] # move towards the objective
    
    if x < len(board) - 1:
        moves.append('right') # can move right
    if x > 0:
        moves.append('left') # can move left
    if y < len(board) - 1:
        moves.append('down') # can move down
    if y > 0:
        moves.append('up') # can move up
    
    # Remove invalid moves (walls)
    valid_moves = []
    for move in moves:
        new_x, new_y = x, y
        if move == 'left':
            new_x -= 1
        elif move == 'right':
            new_x += 1
        elif move == 'up':
            new_y -= 1
        elif move == 'down':
            new_y += 1
        if board[new_x][new_y] != 'W':
            valid_moves.append(move)
    moves = valid_moves
    if len(moves) > 1:
        moves.remove('stay') # prefer moving over staying if possible

    #print("Possible moves:", moves)
    move = random.choice(moves)
    #print('Chose to move', move)
    return move
