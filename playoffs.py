import tkinter as tk
import random
from game_engine import GameApp

def run_round(rcompetitors, third = False):
    # Round of
    round_of = len(rcompetitors)
    if round_of == 32:
        print(f"+-------------- {'Round of 32':^18s} --------------+")
    elif round_of == 16:
        print(f"+-------------- {'Round of 16':^18s} --------------+")
    elif round_of == 8:
        print(f"+-------------- {'Quarterfinals':^18s} --------------+")
    elif round_of == 4:
        print(f"+-------------- {'Semifinals':^18s} --------------+")
    elif round_of == 2 and third == True:
        print(f"+-------------- {'Third place':^18s} --------------+")
    else:
        print(f"+-------------- {'Final':^18s} --------------+")
    for i in range(0, len(rcompetitors), 2):
        agent1, agent2 = rcompetitors[i], rcompetitors[i+1]
        print(f"| {agent1:>20s} -vs- {agent2:<20s} |")
    print("+", "-" * 48, "+", sep="")

    input("Press <Enter> to start...")

    rounds = 3 # number of rounds per match
    match_conter = 0
    next_round = []
    for i in range(0, len(rcompetitors), 2):
        agent1, agent2 = rcompetitors[i], rcompetitors[i+1]
        match_conter += 1
        print(f"+-------------- Match #{match_conter:2d} started! --------------+")
        print(f"| {agent1:>20s} -vs- {agent2:<20s} |")
        print("+", "-" * 48, "+", sep="")
        balance = 0
        r = 1
        while r <= rounds:
            print(f">>> Round {r} fight!")
            root = tk.Tk()
            root.title("Grid Duel Game")
            # Swap players for balance
            if r % 2 == 0:
                app = GameApp(root, agent1, agent2)
            else:
                app = GameApp(root, agent2, agent1)
            root.mainloop()
            winner = app.get_winner()
            #winner = random.choice([agent1, agent2, None])
            if winner is not None:
                print(f">>> And the winner is <{winner}>!")
                if winner == agent1:
                    balance -= 1
                else:
                    balance += 1
                r += 1
            else:
                print(">>> Round ended in a draw!")

            # Balance is greater than rounds left
            if abs(balance) > rounds - r:
                if balance < 0:
                    if not trial and agent1.startswith("agent_rand"):
                        print(f">>> Match ended: Victory of {agent2}*")
                        next_round.append(agent2)
                    else:
                        print(f">>> Match ended: Victory of {agent1}")
                        next_round.append(agent1)
                else:
                    if not trial and agent2.startswith("agent_rand"):
                        print(f">>> Match ended: Victory of {agent1}*")
                        next_round.append(agent1)
                    else:
                        print(f">>> Match ended: Victory of {agent2}")
                        next_round.append(agent2)

                break
    print("+", "-" * 48, "+", sep="")
    return next_round

# Competition participants
competitors = [
    # Students
    #"", ##    STUDENT NAMES GO HERE
    # Default agents
    "agent_rand_defend",
    "agent_rand_objective",
    "agent_rand_hunt",
    "agent_rand_spell_seeker",
]
# Flag to enable/disable random agents wining matches
trial = True

# Randomized competitors list
print("Shuffling agents...")
rcompetitors = list(competitors)
random.shuffle(rcompetitors)
while True:
    for i in range(0, len(rcompetitors), 2):
        agent1, agent2 = rcompetitors[i], rcompetitors[i+1]
        # Avoid random agent matches (if trial is disabled)
        if not trial and agent1.startswith("agent_rand") and agent2.startswith("agent_rand"):
            print("Shuffling agents...")
            random.shuffle(rcompetitors)
            #print(rcompetitors)
            break
    else:
        break # No shuffle happened

# List all players
print(f"+-------------- {'Players':^18s} --------------+")
for i, player in enumerate(rcompetitors):
    print(f"| {i:2d}. {player:<42s} |")
print("+", "-" * 48, "+", sep="")

# Round of 16
if len(rcompetitors) == 16:
    rcompetitors = run_round(rcompetitors)

# Round of 8 (Quarterfinals)
if len(rcompetitors) == 8:
    rcompetitors = run_round(rcompetitors)

# Round of 4 (Semifinals)
if len(rcompetitors) == 4:
    finalist = run_round(rcompetitors)

# Round of 2 (Third place)
rcompetitors.remove(finalist[0])
rcompetitors.remove(finalist[1])
third = run_round(rcompetitors, third = True)

# Round of 2 (Final)
champion = run_round(finalist)
finalist.remove(champion[0])
print("Champion:", champion[0])
print("2nd place:", finalist[0])
print("3rd place:", third[0])

