import json
import os
import random
from game_engine import GameApp

STATE_FILE = "playoffs_state.json"


def next_power_of_2(n):
    return 1 << (n - 1).bit_length() if n > 0 else 0


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


def _clear_match_state(state):
    state["match_agent1"] = None
    state["match_agent2"] = None
    state["match_balance"] = 0
    state["match_round"] = 1


def run_match(agent1, agent2, random_agents, trial, headless, state):
    """
    Run or resume a best-of-3 match between two agents.
    Reads/writes match progress in state so a crash mid-match only loses the
    current sub-round, not the whole match.
    Returns the winning agent module name (after trial overrides).
    """
    rounds = 3
    balance = int(state.get("match_balance", 0))
    r = int(state.get("match_round", 1))

    if r != 1 or balance != 0:
        print(f">>> Resuming match from round {r}, balance {balance}")

    while r <= rounds:
        print(f">>> Round {r} fight!")
        if r % 2 == 0:
            app = GameApp(agent1, agent2, headless=headless)
        else:
            app = GameApp(agent2, agent1, headless=headless)
        winner = app.get_winner()

        if winner is not None:
            print(f">>> And the winner is <{winner}>!")
            if winner == agent1:
                balance -= 1
            else:
                balance += 1
            r += 1

            state["match_balance"] = balance
            state["match_round"] = r
            save_state(state)
        else:
            print(">>> Round ended in a draw!")

        if abs(balance) > rounds - r:
            break

    # Determine match winner (original: balance < 0 → agent1, else → agent2)
    if balance < 0:
        result = agent1
    else:
        result = agent2

    # Trial / random-agent override
    if not trial and result in random_agents:
        result = agent1 if result == agent2 else agent2
        print(f">>> Match ended: Victory of {result}*")
    else:
        print(f">>> Match ended: Victory of {result}")

    return result


def run_round(rcompetitors, random_agents, trial, headless, state, third=False):
    """
    Process one round of the bracket tournament.
    Reads ongoing progress from state so the round can survive crashes.
    Returns the list of winners who advance to the next round.
    """
    round_of = len(rcompetitors)
    if round_of >= 16:
        header = f"Round of {round_of}"
    elif round_of == 8:
        header = "Quarterfinals"
    elif round_of == 4:
        header = "Semifinals"
    elif round_of == 2 and third:
        header = "Third place"
    else:
        header = "Final"

    print(f"+-------------- {header:^18s} --------------+")
    for i in range(0, len(rcompetitors), 2):
        a1, a2 = rcompetitors[i], rcompetitors[i + 1]
        print(f"| {a1:>20s} -vs- {a2:<20s} |")
    print("+", "-" * 48, "+", sep="")

    # Only prompt for fresh rounds (no partially-processed state)
    if state.get("pair_index", 0) == 0 and state.get("match_agent1") is None:
        input("Press <Enter> to start...")

    match_winners = list(state.get("match_winners", []))
    start_pair = int(state.get("pair_index", 0))

    # Resume an in-progress match if the engine crashed mid-match
    if state.get("match_agent1") is not None:
        ma1, ma2 = state["match_agent1"], state["match_agent2"]
        print(f"+-------------- Resuming Match! --------------+")
        print(f"| {ma1:>20s} -vs- {ma2:<20s} |")
        print("+", "-" * 48, "+", sep="")
        winner = run_match(ma1, ma2, random_agents, trial, headless, state)
        match_winners.append(winner)
        start_pair += 2
        _clear_match_state(state)
        state["pair_index"] = start_pair
        state["match_winners"] = match_winners
        save_state(state)

    # Process remaining matches
    match_counter = len(match_winners) + 1
    for i in range(start_pair, len(rcompetitors), 2):
        agent1, agent2 = rcompetitors[i], rcompetitors[i + 1]
        print(f"+-------------- Match #{match_counter:2d} started! --------------+")
        print(f"| {agent1:>20s} -vs- {agent2:<20s} |")
        print("+", "-" * 48, "+", sep="")

        # Snapshot state so we can resume here after a crash
        state["pair_index"] = i
        state["match_winners"] = match_winners
        state["match_agent1"] = agent1
        state["match_agent2"] = agent2
        state["match_balance"] = 0
        state["match_round"] = 1
        save_state(state)

        winner = run_match(agent1, agent2, random_agents, trial, headless, state)
        match_winners.append(winner)
        match_counter += 1

        state["pair_index"] = i + 2
        state["match_winners"] = match_winners
        _clear_match_state(state)
        save_state(state)

    print("+", "-" * 48, "+", sep="")
    return match_winners


# ============================================================
#  Main tournament flow
# ============================================================
def main():
    # --- Load or initialize state ---
    state = load_state()
    if state is not None:
        ans = input("Resume previous tournament? (y/n): ").strip().lower()
        if ans == "y":
            print("Resuming tournament from saved state...")
            if state.get("version") != 1:
                print("Warning: state file has unknown version. Starting fresh.")
                clear_state()
                state = None
        else:
            clear_state()
            state = None

    random_agents = [
        "agent_rand_defend",
        "agent_rand_objective",
        "agent_rand_hunt",
        "agent_rand_spell",
    ]

    if state is None:
        # --- Fresh tournament ---
        trial = False

        competitors = [
            "agent_bfs",
            "agent_value_bfs",
            "a01",
            "a02",
            "a03",
            "a04",
            "aa01",
            "aa02",
            "aa03",
            "aa04"
        ]

        headless = input("Run headless? (y/n): ").strip().lower() == "y"

        # Pad competitors to power of 2
        filled = list(competitors)
        target = next_power_of_2(len(filled))
        while len(filled) < target:
            filled.append(random.choice(random_agents))

        rcompetitors = list(filled)
        random.shuffle(rcompetitors)

        # Avoid random-vs-random first-round matchups
        while True:
            ok = True
            for i in range(0, len(rcompetitors), 2):
                a1, a2 = rcompetitors[i], rcompetitors[i + 1]
                if not trial and a1 in random_agents and a2 in random_agents:
                    ok = False
                    break
            if ok:
                break
            random.shuffle(rcompetitors)

        # Display players
        print(f"+-------------- {'Players':^18s} --------------+")
        for i, player in enumerate(rcompetitors):
            print(f"| {i:2d}. {player:<42s} |")
        print("+", "-" * 48, "+", sep="")

        state = {
            "version": 1,
            "random_agents": list(random_agents),
            "trial": trial,
            "headless": headless,
            "rcompetitors": rcompetitors,
            "phase": "shuffled",
            "pair_index": 0,
            "match_winners": [],
            "match_agent1": None,
            "match_agent2": None,
            "match_balance": 0,
            "match_round": 1,
            "semifinalists": None,
            "finalists": None,
            "third_place_result": None,
        }
        save_state(state)
    else:
        # --- Resuming ---
        random_agents = state.get("random_agents", random_agents)
        trial = state.get("trial", False)
        headless = state.get("headless", True)

    # --- Tournament phases ---
    rcomp = state["rcompetitors"]

    # Bracket rounds (while > 4 competitors)
    if state["phase"] in ("shuffled", "bracket_rounds"):
        state["phase"] = "bracket_rounds"
        while len(rcomp) > 4:
            next_round = run_round(rcomp, random_agents, trial, headless, state)
            rcomp = next_round
            state["rcompetitors"] = rcomp
            state["pair_index"] = 0
            state["match_winners"] = []
            _clear_match_state(state)
            save_state(state)

    # Transition out of bracket rounds
    if state["phase"] == "bracket_rounds":
        if len(rcomp) == 2:
            state["phase"] = "final"
        else:
            state["phase"] = "semifinal"
        save_state(state)

    # ----- 2 competitors: single final -----
    if len(rcomp) == 2:
        if state["phase"] == "final":
            champion = run_round(rcomp, random_agents, trial, headless, state)
            second = [c for c in rcomp if c not in champion][0]
            print("Champion:", champion[0])
            print("2nd place:", second)
            state["phase"] = "complete"
            save_state(state)
        clear_state()
        return

    # ----- 4 competitors: semifinals, third-place, final -----

    # Semifinals
    if state["phase"] == "semifinal":
        state["semifinalists"] = list(rcomp)
        finalists = run_round(rcomp, random_agents, trial, headless, state)
        state["finalists"] = finalists
        state["pair_index"] = 0
        state["match_winners"] = []
        _clear_match_state(state)
        state["phase"] = "third_place"
        save_state(state)
    else:
        finalists = state.get("finalists", [])

    # Third-place match
    if state["phase"] == "third_place":
        losers = [c for c in state["semifinalists"] if c not in finalists]
        state["third_place_contestants"] = losers
        if losers:
            third_result = run_round(
                losers, random_agents, trial, headless, state, third=True
            )
        else:
            print("Warning: could not determine third-place contestants!")
            third_result = []
        state["third_place_result"] = third_result
        state["pair_index"] = 0
        state["match_winners"] = []
        _clear_match_state(state)
        state["phase"] = "final"
        save_state(state)
    else:
        third_result = state.get("third_place_result", [])

    # Final
    if state["phase"] == "final":
        champion = run_round(finalists, random_agents, trial, headless, state)
        state["final_result"] = champion
        remaining = [c for c in finalists if c not in champion]
        print("Champion:", champion[0])
        print("2nd place:", remaining[0] if remaining else "?")
        print("3rd place:", third_result[0] if third_result else "?")
        state["phase"] = "complete"
        save_state(state)

    clear_state()


if __name__ == "__main__":
    main()
