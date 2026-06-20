import random
from game_engine import GameApp


def next_power_of_2(n):
    return 1 << (n - 1).bit_length() if n > 0 else 0


def run_round(rcompetitors, random_agents, trial, headless, third=False):
    round_of = len(rcompetitors)
    if round_of >= 16:
        print(f"+-------------- {'Round of ' + str(round_of):^18s} --------------+")
    elif round_of == 8:
        print(f"+-------------- {'Quarterfinals':^18s} --------------+")
    elif round_of == 4:
        print(f"+-------------- {'Semifinals':^18s} --------------+")
    elif round_of == 2 and third:
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
            # Swap players for balance
            if r % 2 == 0:
                app = GameApp(agent1, agent2, headless=headless)
            else:
                app = GameApp(agent2, agent1, headless=headless)
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
                    if not trial and agent1 in random_agents:
                        print(f">>> Match ended: Victory of {agent2}*")
                        next_round.append(agent2)
                    else:
                        print(f">>> Match ended: Victory of {agent1}")
                        next_round.append(agent1)
                else:
                    if not trial and agent2 in random_agents:
                        print(f">>> Match ended: Victory of {agent1}*")
                        next_round.append(agent1)
                    else:
                        print(f">>> Match ended: Victory of {agent2}")
                        next_round.append(agent2)

                break
    print("+", "-" * 48, "+", sep="")
    return next_round

# Random agents pool (used as filler when needed)
random_agents = [
    "agent_rand_defend",
    "agent_rand_objective",
    "agent_rand_hunt",
    "agent_rand_spell",
]

# Competition participants (students and custom agents only)
competitors = [
    # Students
    "agent_bfs",
    "agent_value_bfs",
    "adefend",
    "aobjective",
    #"ahunt",
    #"aspell",
    # "aadefend",
    # "aaobjective",
    # "aahunt",
    # "aaspell",
    # "a01",
    # "a02",
    # "a03",
    # "aa04",
    # "aa01",
    # "aa02",
    # "aa03",
    # "aa04",
]

# Flag to enable/disable random agents winning matches
trial = False

# Headless mode prompt
headless = input("Run headless? (y/n): ").strip().lower() == 'y'

# Pad to next power of 2 using random agents
filled_competitors = list(competitors)
target = next_power_of_2(len(filled_competitors))
while len(filled_competitors) < target:
    filled_competitors.append(random.choice(random_agents))

# Randomized competitors list
print("Shuffling agents...")
rcompetitors = list(filled_competitors)
random.shuffle(rcompetitors)
while True:
    for i in range(0, len(rcompetitors), 2):
        agent1, agent2 = rcompetitors[i], rcompetitors[i+1]
        if not trial and agent1 in random_agents and agent2 in random_agents:
            print("Shuffling agents...")
            random.shuffle(rcompetitors)
            break
    else:
        break

# List all players
print(f"+-------------- {'Players':^18s} --------------+")
for i, player in enumerate(rcompetitors):
    print(f"| {i:2d}. {player:<42s} |")
print("+", "-" * 48, "+", sep="")

# Run rounds dynamically until semifinals
while len(rcompetitors) > 4:
    rcompetitors = run_round(rcompetitors, random_agents, trial, headless)

if len(rcompetitors) == 2:
    # Only a final, no third-place match needed
    champion = run_round(rcompetitors, random_agents, trial, headless)
    second = [c for c in rcompetitors if c not in champion][0]
    print("Champion:", champion[0])
    print("2nd place:", second)
else:
    # Semifinals (4 competitors → 2 finalists)
    semifinalists = list(rcompetitors)
    finalists = run_round(semifinalists, random_agents, trial, headless)

    # Third place match (the 2 who lost in semifinals)
    third_place_result = run_round(
        [c for c in semifinalists if c not in finalists],
        random_agents, trial, headless, third=True
    )

    # Final
    champion = run_round(finalists, random_agents, trial, headless)
    finalists.remove(champion[0])
    print("Champion:", champion[0])
    print("2nd place:", finalists[0])
    print("3rd place:", third_place_result[0])

