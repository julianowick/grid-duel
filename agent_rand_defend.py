import random

def get_move(board, objective, position, enemy_position, my_strength, enemy_strength, available_spells, memory):

    # Record its initial position in the memory
    if not memory:
        memory.append(position)

    # Check for collected spells
    if available_spells:
        # 30% chance of activating a spell
        if random.random() > 0.7:
            return random.choice(available_spells)

    # List of possible moves
    moves = ['stay']

    # Add prefered moves to defend its initial position
    x, y = position
    ox, oy = memory[0]
    if x > ox:
        moves.append('left') # move towards the objective
    elif x < ox:
        moves.append('right') # move towards the objective
    if y > oy:
        moves.append('up') # move towards the objective
    elif y < oy:
        moves.append('down') # move towards the objective
    
    # Add other possible moves to choose randomly
    if x < len(board) - 1:
        moves.append('right') # can move right
    if x > 0:
        moves.append('left') # can move left
    if y < len(board) - 1:
        moves.append('down') # can move down
    if y > 0:
        moves.append('up') # can move left
    
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

    # Choose random move from available moves
    move = random.choice(moves)
    #print('random player at ', x, y, 'moved', move)
    return move
