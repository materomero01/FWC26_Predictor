import math
import pandas as pd
from collections import defaultdict

# =========================
# CONFIG
# =========================

BASE_ELO = 1500
HOME_ADVANTAGE = 50

START_DATE = "2014-01-01"

CURRENT_YEAR = 2026

# regresión anual hacia la media
REGRESSION_FACTOR = 0.93

# =========================
# WORLD CUP 2026 TEAMS
# =========================

WORLD_CUP_TEAMS = [

    "Argentina",
    "Australia",
    "Austria",
    "Belgium",
    "Bosnia and Herzegovina",
    "Brazil",
    "Canada",
    "Cape Verde",
    "Colombia",
    "Croatia",
    "Curaçao",
    "Czech Republic",
    "DR Congo",
    "Ecuador",
    "Egypt",
    "England",
    "France",
    "Germany",
    "Ghana",
    "Haiti",
    "Iran",
    "Iraq",
    "Ivory Coast",
    "Japan",
    "Jordan",
    "Mexico",
    "Morocco",
    "Netherlands",
    "New Zealand",
    "Norway",
    "Panama",
    "Paraguay",
    "Portugal",
    "Qatar",
    "Saudi Arabia",
    "Scotland",
    "Senegal",
    "South Africa",
    "South Korea",
    "Spain",
    "Sweden",
    "Switzerland",
    "Tunisia",
    "Turkey",
    "United States",
    "Uruguay",
    "Uzbekistan"
]

# =========================
# LOAD DATA
# =========================

df = pd.read_csv("data/results.csv")

df["date"] = pd.to_datetime(df["date"])

# eliminar partidos inválidos
df = df.dropna(subset=["home_score", "away_score"])

# usar fútbol moderno
df = df[df["date"] >= START_DATE]

# ordenar cronológicamente
df = df.sort_values("date").reset_index(drop=True)

# =========================
# ELO STORAGE
# =========================

ratings = defaultdict(lambda: BASE_ELO)

# =========================
# TOURNAMENT WEIGHTS
# =========================

def get_k_factor(tournament):

    tournament = str(tournament)

    # Mundial
    if "World Cup" in tournament and "qualification" not in tournament:
        return 80

    # Euro / Copa América
    elif "Euro" in tournament:
        return 50

    elif "Copa América" in tournament:
        return 50

    # Eliminatorias
    # CAMBIO: subido de 12 a 30 (más representativo de la importancia real)
    elif "qualification" in tournament:
        return 30

    # Nations League
    elif "Nations League" in tournament:
        return 20

    # CAMBIO: amistosos ya no ignorados, K bajo en vez de 0
    elif "Friendly" in tournament:
        return 6

    return 10

# =========================
# GOAL DIFFERENCE MULTIPLIER
# CAMBIO: agregado multiplicador logarítmico por diferencia de goles
# =========================

def get_margin_multiplier(goal_diff):

    if goal_diff == 0:
        return 1.0

    return math.log(abs(goal_diff) + 1) * 1.5

# =========================
# YEARLY REGRESSION
# =========================

last_year = None

# =========================
# MAIN LOOP
# =========================

for _, row in df.iterrows():

    current_year = row["date"].year

    # =========================
    # REGRESSION TO MEAN
    # =========================

    if last_year is not None and current_year != last_year:

        for team in ratings:

            ratings[team] = (
                BASE_ELO +
                (ratings[team] - BASE_ELO) * REGRESSION_FACTOR
            )

    last_year = current_year

    home = row["home_team"]
    away = row["away_team"]

    home_elo = ratings[home]
    away_elo = ratings[away]

    # =========================
    # HOME ADVANTAGE
    # =========================

    adjusted_home_elo = home_elo

    if not row["neutral"]:
        adjusted_home_elo += HOME_ADVANTAGE

    # =========================
    # SAFE ELO DIFF
    # =========================

    elo_diff = away_elo - adjusted_home_elo

    elo_diff = max(min(elo_diff, 400), -400)

    # =========================
    # EXPECTED SCORE
    # =========================

    expected_home = 1 / (
        1 + 10 ** (elo_diff / 400)
    )

    expected_away = 1 - expected_home

    # =========================
    # ACTUAL RESULT
    # =========================

    if row["home_score"] > row["away_score"]:

        actual_home = 1
        actual_away = 0

    elif row["home_score"] < row["away_score"]:

        actual_home = 0
        actual_away = 1

    else:

        actual_home = 0.5
        actual_away = 0.5

    # =========================
    # GOAL DIFFERENCE BONUS
    # CAMBIO: margin_multiplier ahora usa diferencia de goles real
    # =========================

    goal_diff = abs(
        row["home_score"] - row["away_score"]
    )

    margin_multiplier = get_margin_multiplier(goal_diff)

    # =========================
    # UPDATE VALUE
    # CAMBIO: eliminado el min(..., 40) que truncaba partidos de Mundial
    # =========================

    k = get_k_factor(row["tournament"])

    # CAMBIO: recency_multiplier eliminado (redundante con regresión anual)
    update = k * margin_multiplier

    # =========================
    # UPDATE ELO
    # =========================

    ratings[home] += update * (
        actual_home - expected_home
    )

    ratings[away] += update * (
        actual_away - expected_away
    )

# =========================
# ONLY WORLD CUP TEAMS
# =========================

world_cup_ratings = {
    team: rating
    for team, rating in ratings.items()
    if team in WORLD_CUP_TEAMS
}

# =========================
# FINAL RANKING
# =========================

top = sorted(
    world_cup_ratings.items(),
    key=lambda x: x[1],
    reverse=True
)

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print(f"\nPartidos usados: {len(df)}")

    print("\nTOP 48 ELO:\n")

    for i, (team, rating) in enumerate(top, start=1):

        print(
            f"{i:02d}. {team:<25} {rating:.2f}"
        )