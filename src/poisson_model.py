import numpy as np
import pandas as pd
from collections import defaultdict

# =========================
# CONFIG
# =========================

LAST_N_MATCHES = 20

# promedio histórico de goles por equipo por partido en mundiales
BASE_GOALS = 1.35

# =========================
# LOAD DATA
# =========================

print("[poisson] Cargando datos...")

df_results = pd.read_csv("data/results.csv")
df_scorers = pd.read_csv("data/goalscorers.csv")

df_results["date"] = pd.to_datetime(df_results["date"])
df_scorers["date"] = pd.to_datetime(df_scorers["date"])

# eliminar partidos inválidos
df_results = df_results.dropna(subset=["home_score", "away_score"])

# ordenar cronológicamente
df_results = df_results.sort_values("date").reset_index(drop=True)

print(f"[poisson] {len(df_results):,} partidos | {len(df_scorers):,} goles cargados")

# para el historial de ataque/defensa solo usamos fútbol moderno
df_results = df_results[df_results["date"] >= "2010-01-01"].reset_index(drop=True)
df_scorers = df_scorers[df_scorers["date"] >= "2010-01-01"].reset_index(drop=True)

print(f"[poisson] Filtrado desde 2010: {len(df_results):,} partidos")

# importar lista de equipos del mundial
from elo import WORLD_CUP_TEAMS

# solo partidos donde al menos un equipo es del mundial
df_results = df_results[
    df_results["home_team"].isin(WORLD_CUP_TEAMS) |
    df_results["away_team"].isin(WORLD_CUP_TEAMS)
].reset_index(drop=True)

df_scorers = df_scorers[
    df_scorers["home_team"].isin(WORLD_CUP_TEAMS) |
    df_scorers["away_team"].isin(WORLD_CUP_TEAMS)
].reset_index(drop=True)

print(f"[poisson] Filtrado a equipos del mundial: {len(df_results):,} partidos")

# =========================
# GOLES REALES POR PARTIDO
# (excluyendo own goals del equipo que los anotó)
# =========================

print("[poisson] Procesando goles válidos...")

# goles válidos: solo los que NO son own goal
df_valid_goals = df_scorers[df_scorers["own_goal"] == False].copy()

# contar goles por partido y equipo
goals_per_match = (
    df_valid_goals
    .groupby(["date", "home_team", "away_team", "team"])
    .size()
    .reset_index(name="goals_scored")
)

# =========================
# ÍNDICE para lookup O(1)
# key: (date, home_team, away_team, team) -> goals_scored
# =========================

goals_index = {}

for _, row in goals_per_match.iterrows():
    key = (row["date"], row["home_team"], row["away_team"], row["team"])
    goals_index[key] = row["goals_scored"]

# =========================
# CONSTRUIR HISTORIAL POR EQUIPO
# Para cada equipo: lista de (goles_anotados, goles_recibidos) por partido
# ordenada cronológicamente
# =========================

print("[poisson] Construyendo historial por equipo...")

# estructura: {equipo: [(goles_a_favor, goles_en_contra), ...]}
match_history = defaultdict(list)

for _, row in df_results.iterrows():

    home = row["home_team"]
    away = row["away_team"]
    home_score = int(row["home_score"])
    away_score = int(row["away_score"])
    date = row["date"]

    # lookup O(1) en vez de filter O(n)
    home_valid = goals_index.get((date, home, away, home), None)
    away_valid = goals_index.get((date, home, away, away), None)

    # fallback al score del resultado si no hay datos en scorers
    if home_valid is None:
        home_valid = home_score
    if away_valid is None:
        away_valid = away_score

    match_history[home].append((home_valid, away_valid))
    match_history[away].append((away_valid, home_valid))

print(f"[poisson] Historial construido para {len(match_history):,} equipos")

# =========================
# CALCULAR ATAQUE Y DEFENSA
# usando los últimos N partidos
# =========================

def get_team_stats(team, n=LAST_N_MATCHES):

    history = match_history[team]

    # tomar los últimos N partidos
    recent = history[-n:] if len(history) >= n else history

    if not recent:
        return BASE_GOALS, BASE_GOALS

    goals_scored = [g[0] for g in recent]
    goals_conceded = [g[1] for g in recent]

    attack = sum(goals_scored) / len(goals_scored)
    defense = sum(goals_conceded) / len(goals_conceded)

    # evitar lambdas de 0 (equipos muy defensivos)
    attack = max(attack, 0.3)
    defense = max(defense, 0.3)

    return attack, defense

# =========================
# LAMBDA DE GOLES ESPERADOS
# Dixon-Coles + ajuste por ELO:
# lambda_a = base * (attack_a / base) * (defense_b / base) * elo_factor
# El ELO factor amplifica/reduce los lambdas según diferencia de rating
# =========================

def get_lambdas(team_a, team_b):

    from elo import ratings

    attack_a, defense_a = get_team_stats(team_a)
    attack_b, defense_b = get_team_stats(team_b)

    elo_a = ratings[team_a]
    elo_b = ratings[team_b]

    # factor ELO: >1 si team_a es mejor, <1 si es peor
    # divisor 800 equilibra impacto ELO con variabilidad del Poisson
    elo_factor_a = 10 ** ((elo_a - elo_b) / 800)
    elo_factor_b = 10 ** ((elo_b - elo_a) / 800)

    lambda_a = BASE_GOALS * (attack_a / BASE_GOALS) * (defense_b / BASE_GOALS) * elo_factor_a
    lambda_b = BASE_GOALS * (attack_b / BASE_GOALS) * (defense_a / BASE_GOALS) * elo_factor_b

    # clamping razonable
    lambda_a = max(min(lambda_a, 5.0), 0.2)
    lambda_b = max(min(lambda_b, 5.0), 0.2)

    return lambda_a, lambda_b

# =========================
# SCORE PREDICTION
# retorna (goles_a, goles_b) sampleados con Poisson
# =========================

def predict_score(team_a, team_b):

    lambda_a, lambda_b = get_lambdas(team_a, team_b)

    goals_a = np.random.poisson(lambda_a)
    goals_b = np.random.poisson(lambda_b)

    return goals_a, goals_b


# =========================
# SCORE PREDICTION (DETERMINISTA PARA PRODE)
# Retorna el resultado matemático más probable (sin azar)
# =========================
def predict_score_prode(team_a, team_b):
    lambda_a, lambda_b = get_lambdas(team_a, team_b)

    # Redondeamos la expectativa matemática al gol entero más cercano.
    # Esto elimina las sorpresas y te da el resultado "estadísticamente más seguro".
    goals_a = int(round(lambda_a))
    goals_b = int(round(lambda_b))

    return goals_a, goals_b

# =========================
# MAIN — debug
# =========================

if __name__ == "__main__":

    teams = [
        ("Argentina", "France"),
        ("Brazil", "Germany"),
        ("Morocco", "England"),
        ("Japan", "Spain"),
    ]

    print(f"\nEstadísticas (últimos {LAST_N_MATCHES} partidos):\n")

    for team_a, team_b in teams:

        atk_a, def_a = get_team_stats(team_a)
        atk_b, def_b = get_team_stats(team_b)
        l_a, l_b = get_lambdas(team_a, team_b)

        print(f"{team_a} vs {team_b}")
        print(f"  {team_a}: ataque={atk_a:.2f}, defensa={def_a:.2f} → λ={l_a:.2f}")
        print(f"  {team_b}: ataque={atk_b:.2f}, defensa={def_b:.2f} → λ={l_b:.2f}")

        # muestra 5 scores simulados
        scores = [predict_score(team_a, team_b) for _ in range(5)]
        print(f"  Scores simulados: {scores}\n")


