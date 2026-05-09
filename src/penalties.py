import pandas as pd
from collections import defaultdict

# ==========================================
# penalties.py
# Análisis histórico de efectividad en Penales
# ==========================================

def load_penalty_stats(filepath="data/shootouts.csv"):
    df = pd.read_csv(filepath)
    
    shootouts_played = defaultdict(int)
    shootouts_won = defaultdict(int)
    
    # Procesar todo el historial
    for _, row in df.iterrows():
        home = row['home_team']
        away = row['away_team']
        winner = row['winner']
        
        shootouts_played[home] += 1
        shootouts_played[away] += 1
        shootouts_won[winner] += 1
        
    # Calcular el win rate (porcentaje de éxito)
    win_rates = {}
    for team, played in shootouts_played.items():
        # win_rate va de 0.0 a 1.0
        win_rates[team] = shootouts_won[team] / played
        
    return win_rates, shootouts_played

# Cargar las variables al importar el módulo
PENALTY_WIN_RATES, PENALTY_PLAYED = load_penalty_stats()

def get_penalty_winner(team_a, team_b, elo_a, elo_b):
    """
    Decide el ganador de una tanda de penales basándose en su efectividad histórica.
    Si un equipo no tiene historial, asume un 50% de efectividad (0.50).
    """
    rate_a = PENALTY_WIN_RATES.get(team_a, 0.50)
    rate_b = PENALTY_WIN_RATES.get(team_b, 0.50)
    
    if rate_a > rate_b:
        return team_a
    elif rate_b > rate_a:
        return team_b
    else:
        # Si tienen la misma efectividad exacta, desempatamos por su calidad actual (ELO)
        return team_a if elo_a > elo_b else team_b