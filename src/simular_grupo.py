import random
from collections import defaultdict

from simple_predictor import predict_match

# =========================
# SCORE GENERATION
# =========================

def generate_score(result_type):

    # =========================
    # DRAWS
    # =========================

    if result_type == "Draw":

        possible_scores = [
            (0, 0),
            (1, 1),
            (2, 2)
        ]

        weights = [40, 45, 15]

        return random.choices(
            possible_scores,
            weights=weights
        )[0]

    # =========================
    # FAVORITE WINS
    # =========================

    possible_scores = [
        (1, 0),
        (2, 0),
        (2, 1),
        (3, 1),
        (3, 0)
    ]

    weights = [25, 25, 25, 15, 10]

    return random.choices(
        possible_scores,
        weights=weights
    )[0]

# =========================
# MATCH SIMULATION
# =========================

def simulate_match(team_a, team_b):

    prediction = predict_match(
        team_a,
        team_b
    )

    win_a = prediction["win_a"]
    draw_prob = prediction["draw"]

    r = random.random()

    # =========================
    # TEAM A WINS
    # =========================

    if r < win_a:

        home_goals, away_goals = generate_score(
            "Win"
        )

        return {
            "team_a": team_a,
            "team_b": team_b,
            "winner": team_a,
            "goals_a": home_goals,
            "goals_b": away_goals
        }

    # =========================
    # DRAW
    # =========================

    elif r < win_a + draw_prob:

        goals_a, goals_b = generate_score(
            "Draw"
        )

        return {
            "team_a": team_a,
            "team_b": team_b,
            "winner": "Draw",
            "goals_a": goals_a,
            "goals_b": goals_b
        }

    # =========================
    # TEAM B WINS
    # =========================

    else:

        away_goals, home_goals = generate_score(
            "Win"
        )

        return {
            "team_a": team_a,
            "team_b": team_b,
            "winner": team_b,
            "goals_a": home_goals,
            "goals_b": away_goals
        }

# =========================
# GROUP SIMULATION
# =========================

def simulate_group(teams):

    standings = defaultdict(lambda: {
        "pts": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0
    })

    matches = [

        (teams[0], teams[1]),
        (teams[0], teams[2]),
        (teams[0], teams[3]),

        (teams[1], teams[2]),
        (teams[1], teams[3]),

        (teams[2], teams[3]),
    ]

    print("\nMATCHES:\n")

    for team_a, team_b in matches:

        result = simulate_match(
            team_a,
            team_b
        )

        goals_a = result["goals_a"]
        goals_b = result["goals_b"]

        # =========================
        # UPDATE GOALS
        # =========================

        standings[team_a]["gf"] += goals_a
        standings[team_a]["ga"] += goals_b

        standings[team_b]["gf"] += goals_b
        standings[team_b]["ga"] += goals_a

        standings[team_a]["gd"] = (
            standings[team_a]["gf"] -
            standings[team_a]["ga"]
        )

        standings[team_b]["gd"] = (
            standings[team_b]["gf"] -
            standings[team_b]["ga"]
        )

        # =========================
        # RESULT
        # =========================

        if result["winner"] == team_a:

            standings[team_a]["pts"] += 3

        elif result["winner"] == team_b:

            standings[team_b]["pts"] += 3

        else:

            standings[team_a]["pts"] += 1
            standings[team_b]["pts"] += 1

        # =========================
        # PRINT MATCH
        # =========================

        print(
            f"{team_a} {goals_a} - {goals_b} {team_b}"
        )

    # =========================
    # FINAL TABLE
    # =========================

    table = sorted(

        standings.items(),

        key=lambda x: (
            x[1]["pts"],
            x[1]["gd"],
            x[1]["gf"]
        ),

        reverse=True
    )

    # =========================
    # PRINT TABLE
    # =========================

    print("\nFINAL TABLE:\n")

    for i, (team, stats) in enumerate(table, start=1):

        print(
            f"{i}. "
            f"{team:<15} "
            f"{stats['pts']} pts | "
            f"GD {stats['gd']:+} | "
            f"GF {stats['gf']}"
        )

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    group = [

        "Argentina",
        "Japan",
        "Canada",
        "Ghana"
    ]

    simulate_group(group)