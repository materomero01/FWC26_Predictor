from poisson_model import predict_score

# =========================
# MATCH SIMULATION
# =========================

def simulate_match(team_a, team_b):

    goals_a, goals_b = predict_score(team_a, team_b)

    if goals_a > goals_b:
        return team_a, goals_a, goals_b

    elif goals_b > goals_a:
        return team_b, goals_a, goals_b

    else:
        return "Draw", goals_a, goals_b

# =========================
# MASS SIMULATION
# =========================

def simulate_many(team_a, team_b, n=10000):

    results = {
        team_a: 0,
        team_b: 0,
        "Draw": 0
    }

    total_goals_a = 0
    total_goals_b = 0

    for _ in range(n):

        winner, goals_a, goals_b = simulate_match(team_a, team_b)
        results[winner] += 1
        total_goals_a += goals_a
        total_goals_b += goals_b

    # =========================
    # PRINT RESULTS
    # =========================

    print(f"\nSIMULATION RESULTS ({n:,} partidos)\n")

    print(f"{team_a}: {(results[team_a]/n)*100:.2f}%")
    print(f"Draw:    {(results['Draw']/n)*100:.2f}%")
    print(f"{team_b}: {(results[team_b]/n)*100:.2f}%")

    print(f"\nPromedio de goles:")
    print(f"  {team_a}: {total_goals_a/n:.2f}")
    print(f"  {team_b}: {total_goals_b/n:.2f}")

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    simulate_many("Argentina", "France")
    simulate_many("Brazil", "Germany")
    simulate_many("Morocco", "England")