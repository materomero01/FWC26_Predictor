from collections import defaultdict

from simple_predictor import predict_match
from poisson_model import predict_score
from groups import *

# =========================
# MATCH SIMULATION
# =========================

def simulate_match(team_a, team_b):

    # score simulado con Poisson
    goals_a, goals_b = predict_score(team_a, team_b)

    if goals_a > goals_b:
        winner = team_a

    elif goals_b > goals_a:
        winner = team_b

    else:
        winner = "Draw"

    return {
        "team_a": team_a,
        "team_b": team_b,
        "winner": winner,
        "goals_a": goals_a,
        "goals_b": goals_b
    }

# =========================
# GROUP SIMULATION
# =========================

def simulate_group(teams, verbose=True):

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

    if verbose:
        print("\nMATCHES:\n")

    for team_a, team_b in matches:

        result = simulate_match(team_a, team_b)

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
        # POINTS
        # =========================

        if result["winner"] == team_a:
            standings[team_a]["pts"] += 3

        elif result["winner"] == team_b:
            standings[team_b]["pts"] += 3

        else:
            standings[team_a]["pts"] += 1
            standings[team_b]["pts"] += 1

        if verbose:
            print(f"{team_a} {goals_a} - {goals_b} {team_b}")

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

    if verbose:

        print("\nFINAL TABLE:\n")

        for i, (team, stats) in enumerate(table, start=1):
            print(
                f"{i}. "
                f"{team:<25} "
                f"{stats['pts']} pts | "
                f"GD {stats['gd']:+} | "
                f"GF {stats['gf']}"
            )

    # retorna lista de equipos ordenados y sus stats
    return [team for team, _ in table], {team: stats for team, stats in table}

# =========================
# MONTE CARLO GROUP
# =========================

def simulate_group_mc(teams, n=10000):

    # acumular posiciones: {equipo: [pos1, pos2, pos3, pos4]}
    position_counts = defaultdict(lambda: [0, 0, 0, 0])

    # acumular stats promedio
    stats_accum = defaultdict(lambda: {
        "pts": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0
    })

    for _ in range(n):

        table, stats = simulate_group(teams, verbose=False)

        for pos, team in enumerate(table):
            position_counts[team][pos] += 1
            stats_accum[team]["pts"] += stats[team]["pts"]
            stats_accum[team]["gf"] += stats[team]["gf"]
            stats_accum[team]["ga"] += stats[team]["ga"]
            stats_accum[team]["gd"] += stats[team]["gd"]

    # ordenar por probabilidad de quedar primero
    sorted_teams = sorted(
        teams,
        key=lambda t: position_counts[t][0],
        reverse=True
    )

    print(f"\n{'EQUIPO':<25} {'1ro':>6} {'2do':>6} {'3ro':>6} {'4to':>6} {'Clasif':>8} {'Pts avg':>8}")
    print("-" * 72)

    results = {}

    for team in sorted_teams:

        counts = position_counts[team]
        p1 = counts[0] / n * 100
        p2 = counts[1] / n * 100
        p3 = counts[2] / n * 100
        p4 = counts[3] / n * 100
        clasif = (counts[0] + counts[1]) / n * 100
        pts_avg = stats_accum[team]["pts"] / n

        print(
            f"{team:<25} "
            f"{p1:>5.1f}% {p2:>5.1f}% {p3:>5.1f}% {p4:>5.1f}% "
            f"{clasif:>7.1f}% {pts_avg:>7.2f}"
        )

        results[team] = {
            "p1": p1, "p2": p2, "p3": p3, "p4": p4,
            "clasif": clasif,
            "pts_avg": pts_avg,
            "gf_avg": stats_accum[team]["gf"] / n,
            "gd_avg": stats_accum[team]["gd"] / n,
        }

    return results

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    group = GROUP_J
    n=10000

    print(f"\nSimulando grupo ({n:,} iteraciones)...\n")

    simulate_group_mc(group, n)