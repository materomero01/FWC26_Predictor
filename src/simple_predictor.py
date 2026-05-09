from elo import ratings

# =========================
# DRAW MODEL
# =========================

def draw_probability(elo_diff):

    diff = abs(elo_diff)

    # más parejos => más empate
    draw_prob = max(
        0.12,
        0.30 - (diff / 2000)
    )

    return draw_prob

# =========================
# MATCH PREDICTION
# =========================

def predict_match(team_a, team_b):

    elo_a = ratings[team_a]
    elo_b = ratings[team_b]

    # =========================
    # ELO SCALE
    # CAMBIO: corregido de 200 a 400 para ser consistente con elo.py
    # Con 200 se sobreestimaba la diferencia: 200 pts ELO daba 76% en vez de 64%
    # =========================

    SCALE = 400

    # =========================
    # WIN PROBABILITIES
    # =========================

    expected_a = 1 / (
        1 + 10 ** ((elo_b - elo_a) / SCALE)
    )

    expected_b = 1 - expected_a

    # =========================
    # DRAW PROBABILITY
    # =========================

    draw_prob = draw_probability(
        elo_a - elo_b
    )

    # =========================
    # REDISTRIBUTE
    # =========================

    win_a = expected_a * (
        1 - draw_prob
    )

    win_b = expected_b * (
        1 - draw_prob
    )

    # =========================
    # NORMALIZE
    # =========================

    total = win_a + draw_prob + win_b

    win_a /= total
    draw_prob /= total
    win_b /= total

    # =========================
    # RETURN
    # =========================

    return {
        "team_a": team_a,
        "team_b": team_b,
        "win_a": win_a,
        "draw": draw_prob,
        "win_b": win_b
    }

# =========================
# PRETTY PRINT
# =========================

def print_prediction(team_a, team_b):

    prediction = predict_match(
        team_a,
        team_b
    )

    print(f"\n{team_a} vs {team_b}\n")

    print(
        f"{team_a}: "
        f"{prediction['win_a']*100:.1f}%"
    )

    print(
        f"Empate: "
        f"{prediction['draw']*100:.1f}%"
    )

    print(
        f"{team_b}: "
        f"{prediction['win_b']*100:.1f}%"
    )

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print_prediction(
        "Argentina",
        "Japan"
    )

    print_prediction(
        "France",
        "Brazil"
    )

    print_prediction(
        "Spain",
        "Germany"
    )

    print_prediction(
        "Morocco",
        "England"
    )