import random

from simple_predictor import predict_match

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
    win_b = prediction["win_b"]

    r = random.random()

    # =========================
    # RANDOM RESULT
    # =========================

    if r < win_a:

        return team_a

    elif r < win_a + draw_prob:

        return "Draw"

    else:

        return team_b

# =========================
# MASS SIMULATION
# =========================

def simulate_many(team_a, team_b, n=10000):

    results = {
        team_a: 0,
        team_b: 0,
        "Draw": 0
    }

    for _ in range(n):

        result = simulate_match(
            team_a,
            team_b
        )

        results[result] += 1

    # =========================
    # PRINT RESULTS
    # =========================

    print(
        f"\nSIMULATION RESULTS "
        f"({n:,} matches)\n"
    )

    print(
        f"{team_a}: "
        f"{(results[team_a]/n)*100:.2f}%"
    )

    print(
        f"Draw: "
        f"{(results['Draw']/n)*100:.2f}%"
    )

    print(
        f"{team_b}: "
        f"{(results[team_b]/n)*100:.2f}%"
    )

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    simulate_many(
        "Argentina",
        "Japan"
    )