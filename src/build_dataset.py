import pandas as pd
from collections import defaultdict

# =========================
# CONFIGURACIÓN ELO BASE
# =========================
BASE_ELO = 1500
HOME_ADVANTAGE = 50
START_DATE = "2010-01-01" # Entrenamos al modelo con fútbol moderno (desde 2010)
REGRESSION_FACTOR = 0.96

def get_k_factor(tournament):
    tournament = str(tournament)
    if "World Cup" in tournament and "qualification" not in tournament:
        return 80
    elif "Euro" in tournament or "Copa América" in tournament:
        return 50
    elif "qualification" in tournament:
        return 30
    elif "Nations League" in tournament:
        return 20
    return 10

def get_recency_multiplier(match_year, current_year):
    years_old = current_year - match_year
    if years_old <= 2: return 1.0
    elif years_old <= 3: return 0.8
    elif years_old <= 4: return 0.6
    return 0.4

def build_xgboost_dataset():
    print("🛠️ Construyendo Matriz de Características para XGBoost...")
    
    df = pd.read_csv("data/results.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["home_score", "away_score"])
    
    # Filtramos desde 2010 para que no aprenda de cómo se jugaba en 1980
    df = df[df["date"] >= START_DATE].sort_values("date").reset_index(drop=True)

    ratings = defaultdict(lambda: BASE_ELO)
    dataset_rows = []

    last_year = None

    for _, row in df.iterrows():
        current_year = row["date"].year

        # 1. Regresión anual a la media
        if last_year is not None and current_year != last_year:
            for team in ratings:
                ratings[team] = (BASE_ELO + (ratings[team] - BASE_ELO) * REGRESSION_FACTOR)
        
        last_year = current_year

        home, away = row["home_team"], row["away_team"]
        home_elo, away_elo = ratings[home], ratings[away]
        
        home_score = int(row["home_score"])
        away_score = int(row["away_score"])
        neutral = 1 if row["neutral"] else 0
        
        # ====================================================================
        # FASE DE EXTRACCIÓN (FEATURES ANTES DEL PARTIDO)
        # ====================================================================
        is_worldcup = 1 if row["tournament"] == "FIFA World Cup" else 0
        
        # Calculamos la diferencia real de nivel (sumando ventaja local)
        adj_home_elo = home_elo + (0 if neutral else HOME_ADVANTAGE)
        elo_diff = adj_home_elo - away_elo

        # Guardamos la "foto" exacta de cómo llegaban los equipos a ese partido
        dataset_rows.append({
            "date": row["date"],
            "home_team": home,
            "away_team": away,
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_diff": elo_diff,
            "is_neutral": neutral,
            "is_worldcup": is_worldcup,
            "home_score": home_score,  # TARGET 1 (Lo que el modelo debe aprender a predecir)
            "away_score": away_score   # TARGET 2 (Lo que el modelo debe aprender a predecir)
        })

        # ====================================================================
        # FASE DE ACTUALIZACIÓN (CÁLCULO ELO POST-PARTIDO)
        # ====================================================================
        expected_home = 1 / (1 + 10 ** ((away_elo - adj_home_elo) / 400))
        expected_away = 1 - expected_home

        goal_diff = abs(home_score - away_score)
        if home_score > away_score:
            actual_home, actual_away = 1, 0
        elif home_score < away_score:
            actual_home, actual_away = 0, 1
        else:
            actual_home, actual_away = 0.5, 0.5

        if goal_diff <= 1: margin_mult = 1.0
        elif goal_diff == 2: margin_mult = 1.5
        else: margin_mult = (11 + goal_diff) / 8

        k = get_k_factor(row["tournament"])
        recency = get_recency_multiplier(current_year, current_year)
        update_base = k * margin_mult * recency

        ratings[home] += update_base * (actual_home - expected_home)
        ratings[away] += update_base * (actual_away - expected_away)

    # 3. Exportar a CSV
    df_dataset = pd.DataFrame(dataset_rows)
    output_path = "data/xgboost_dataset.csv"
    df_dataset.to_csv(output_path, index=False)
    
    print(f"✅ Matriz generada exitosamente. Partidos procesados: {len(df_dataset):,}")
    print(f"📁 Guardado en: {output_path}")

if __name__ == "__main__":
    build_xgboost_dataset()