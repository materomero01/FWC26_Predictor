import pandas as pd
import numpy as np
import xgboost as xgb
from collections import Counter, defaultdict

from groups import (
    GROUP_A, GROUP_B, GROUP_C, GROUP_D, GROUP_E, GROUP_F,
    GROUP_G, GROUP_H, GROUP_I, GROUP_J, GROUP_K, GROUP_L
)
from elo import ratings
from modifiers import MARKET_VALUE_M, HOST_ADVANTAGE, PEDIGREE_BONUS, INJURY_PENALTY
from penalties import get_penalty_winner, PENALTY_WIN_RATES, PENALTY_PLAYED

# =========================
# CONFIGURACIÓN
# =========================
N_SIMULACIONES = 100000

GROUPS = {
    "A": GROUP_A, "B": GROUP_B, "C": GROUP_C, "D": GROUP_D,
    "E": GROUP_E, "F": GROUP_F, "G": GROUP_G, "H": GROUP_H,
    "I": GROUP_I, "J": GROUP_J, "K": GROUP_K, "L": GROUP_L,
}

# =========================
# CARGAR MODELOS XGBOOST
# =========================
print("🧠 Cargando modelos de Inteligencia Artificial (XGBoost)...")
model_home = xgb.XGBRegressor()
model_home.load_model("models/xgb_home.json")

model_away = xgb.XGBRegressor()
model_away.load_model("models/xgb_away.json")

# =========================
# INFERENCIA: XGBOOST + MODIFICADORES
# =========================
def get_xgb_lambdas(team_a, team_b, is_knockout=False):
    # 1. ELO Base Histórico
    elo_a = ratings[team_a]
    elo_b = ratings[team_b]

    # 2. Modificadores de Localía e Hinchada
    elo_a += HOST_ADVANTAGE.get(team_a, 0)
    elo_b += HOST_ADVANTAGE.get(team_b, 0)

    # 3. Modificadores por Lesiones (Manual)
    elo_a += INJURY_PENALTY.get(team_a, 0)
    elo_b += INJURY_PENALTY.get(team_b, 0)

    # 4. Ajuste por Valor de Mercado
    val_a = MARKET_VALUE_M.get(team_a, 10)
    val_b = MARKET_VALUE_M.get(team_b, 10)
    
    diff_mercado = val_a - val_b
    bono_mercado_a = (diff_mercado / 100) * 5 if diff_mercado > 0 else 0
    bono_mercado_b = (-diff_mercado / 100) * 5 if diff_mercado < 0 else 0
    
    elo_a += bono_mercado_a
    elo_b += bono_mercado_b

    # 5. Bono de Pedigrí (SOLO en fase eliminatoria)
    if is_knockout:
        elo_a *= PEDIGREE_BONUS.get(team_a, 1.0)
        elo_b *= PEDIGREE_BONUS.get(team_b, 1.0)

    # Diferencia final calculada
    elo_diff = elo_a - elo_b

    # 6. Preparar los datos para el formato exacto que espera XGBoost
    # Asumimos neutral=1 porque el mundial es terreno neutral (la ventaja ya se sumó arriba)
    input_data = pd.DataFrame([{
        "home_elo": elo_a,
        "away_elo": elo_b,
        "elo_diff": elo_diff,
        "is_neutral": 1,
        "is_worldcup": 1
    }])

  # 7. Predicción (Lambdas)
    lambda_a = float(model_home.predict(input_data)[0])
    lambda_b = float(model_away.predict(input_data)[0])

    # Aplicamos un techo (cap) lógico para evitar resultados absurdos (como el 12.27)
    # y un piso para que siempre haya una chance mínima de gol.
    lambda_a = max(min(lambda_a, 5.0), 0.1)
    lambda_b = max(min(lambda_b, 5.0), 0.1)

    return lambda_a, lambda_b

# =========================
# MOTOR MONTE CARLO
# =========================
def obtener_consenso(team_a, team_b, n=N_SIMULACIONES, is_knockout=False):
    lambda_a, lambda_b = get_xgb_lambdas(team_a, team_b, is_knockout)
    
    sims_a = np.random.poisson(lambda_a, n)
    sims_b = np.random.poisson(lambda_b, n)
    
    resultados = zip(sims_a, sims_b)
    conteo = Counter(resultados)
    mas_comun, frecuencia = conteo.most_common(1)[0]
    
    probabilidad = (frecuencia / n) * 100
    return mas_comun[0], mas_comun[1], probabilidad

# =========================
# LÓGICA DE TORNEO
# =========================
def resolver_grupos_prode():
    winners, runners, thirds_dict = {}, {}, {}
    print("\n" + "="*65)
    print(f"🏆 FASE DE GRUPOS (XGBOOST V2 + {N_SIMULACIONES:,} SIMS) 🏆")
    print("="*65)

    for group_name, teams in GROUPS.items():
        print(f"\n--- GRUPO {group_name} ---")
        standings = defaultdict(lambda: {"pts": 0, "gf": 0, "ga": 0, "gd": 0})
        matches = [
            (teams[0], teams[1]), (teams[0], teams[2]), (teams[0], teams[3]),
            (teams[1], teams[2]), (teams[1], teams[3]), (teams[2], teams[3])
        ]
        
        for a, b in matches:
            goals_a, goals_b, prob = obtener_consenso(a, b)
            print(f"  {a:>20} {goals_a} - {goals_b} {b:<20} [Prob: {prob:.1f}%]")
            
            standings[a]["gf"] += goals_a
            standings[a]["ga"] += goals_b
            standings[b]["gf"] += goals_b
            standings[b]["ga"] += goals_a
            standings[a]["gd"] = standings[a]["gf"] - standings[a]["ga"]
            standings[b]["gd"] = standings[b]["gf"] - standings[b]["ga"]
            
            if goals_a > goals_b: standings[a]["pts"] += 3
            elif goals_b > goals_a: standings[b]["pts"] += 3
            else:
                standings[a]["pts"] += 1
                standings[b]["pts"] += 1

        tabla = sorted(standings.items(), key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]), reverse=True)
        print(f"  -> Pasan: 1° {tabla[0][0]} | 2° {tabla[1][0]} | 3° {tabla[2][0]}")
        
        winners[group_name], runners[group_name] = tabla[0][0], tabla[1][0]
        thirds_dict[group_name] = (tabla[2][0], tabla[2][1])
        
    return winners, runners, thirds_dict

def obtener_mejores_terceros_prode(thirds_dict):
    sorted_thirds = sorted(thirds_dict.items(), key=lambda x: (x[1][1]["pts"], x[1][1]["gd"], x[1][1]["gf"]), reverse=True)
    return [team for _, (team, _) in sorted_thirds[:8]]

def armar_16vos_prode(winners, runners, best_thirds):
    matches = []
    grupos_contra_terceros = ["A", "B", "C", "D", "E", "F", "G", "H"]
    for i in range(8): matches.append((winners[grupos_contra_terceros[i]], best_thirds[i]))
    
    ganadores_restantes = [winners["I"], winners["J"], winners["K"], winners["L"]]
    todos_los_segundos = list(runners.values())
    
    for i in range(4): matches.append((ganadores_restantes[i], todos_los_segundos[i]))
    segundos_restantes = todos_los_segundos[4:]
    for i in range(0, 8, 2): matches.append((segundos_restantes[i], segundos_restantes[i+1]))
    return matches

def simular_tanda_penales(team_a, team_b):
    rate_a = PENALTY_WIN_RATES.get(team_a, 0.50)
    rate_b = PENALTY_WIN_RATES.get(team_b, 0.50)
    
    # Ajuste por muestra pequeña (mínimo 3 tandas para confiar en el rate)
    if PENALTY_PLAYED.get(team_a, 0) < 3: rate_a = 0.50
    if PENALTY_PLAYED.get(team_b, 0) < 3: rate_b = 0.50

    goles_a, goles_b = 0, 0
    
    # Simulamos los primeros 5 penales obligatorios
    for _ in range(5):
        if np.random.random() < rate_a: goles_a += 1
        if np.random.random() < rate_b: goles_b += 1
    
    # Muerte súbita si siguen empatados
    while goles_a == goles_b:
        if np.random.random() < rate_a: goles_a += 1
        if np.random.random() < rate_b: goles_b += 1
        
    return goles_a, goles_b

def simular_cruce_prode(team_a, team_b, es_final=False):
    # 1. Obtenemos lambdas de XGBoost
    lambda_a, lambda_b = get_xgb_lambdas(team_a, team_b, is_knockout=True)
    
    # 2. Simulamos el millón de partidos
    sims_a = np.random.poisson(lambda_a, N_SIMULACIONES)
    sims_b = np.random.poisson(lambda_b, N_SIMULACIONES)
    
    # 3. Contamos todas las ocurrencias
    resultados = zip(sims_a, sims_b)
    conteo = Counter(resultados)
    
    # El Top 1 (Consenso)
    top_resultados = conteo.most_common(5)
    (goals_a, goals_b), frecuencia = top_resultados[0]
    prob = (frecuencia / N_SIMULACIONES) * 100

    print(f"  {team_a:>20} {goals_a} - {goals_b} {team_b:<20} [Prob: {prob:.1f}%]", end="")

    # --- BLOQUE NUEVO: TOP 5 PARA LA FINAL ---
    # --- BLOQUE ACTUALIZADO: TOP 5 CON DESEMPATE ---
    if es_final:
        print("\n\n📊 TOP 5 ESCENARIOS MÁS PROBABLES (ANÁLISIS DE LA FINAL):")
        for i, (res, freq) in enumerate(top_resultados, 1):
            p_resultado = (freq / N_SIMULACIONES) * 100
            goles_a, goles_b = res[0], res[1]
            
            info_extra = ""
            if goles_a == goles_b:
                # Si el escenario es empate, calculamos quién suele ganar los penales
                # Simulamos 10,000 tandas rápidas para obtener un % de éxito en ese cruce
                victorias_a_pen = sum(1 for _ in range(10000) if simular_tanda_penales(team_a, team_b)[0] > simular_tanda_penales(team_a, team_b)[1])
                prob_a_pen = victorias_a_pen / 100
                prob_b_pen = 100 - prob_a_pen
                ganador_pen = team_a if prob_a_pen > prob_b_pen else team_b
                info_extra = f" -> [En penales: {team_a} {prob_a_pen:.1f}% | {team_b} {prob_b_pen:.1f}%]"
            
            print(f"   {i}. {team_a} {goles_a} - {goles_b} {team_b} ({p_resultado:.2f}%){info_extra}")
        print("-" * 65)
    # -----------------------------------------

    if goals_a > goals_b:
        print(f" ---> Pasa: {team_a}")
        return team_a
    elif goals_b > goals_a:
        print(f" ---> Pasa: {team_b}")
        return team_b
    else:
        # === SIMULACIÓN DE TANDA DE PENALES ===
        pen_a, pen_b = simular_tanda_penales(team_a, team_b)
        ganador = team_a if pen_a > pen_b else team_b
        
        rate_ganador = PENALTY_WIN_RATES.get(ganador, 0.50) * 100
        print(f" ---> Empate ({pen_a} - {pen_b} en penales) | Gana: {ganador}")
        return ganador

def generar_prode_ideal():
    winners, runners, thirds_dict = resolver_grupos_prode()
    best_thirds = obtener_mejores_terceros_prode(thirds_dict)
    
    print("\n" + "="*65)
    print("📈 LOS 8 MEJORES TERCEROS QUE CLASIFICAN 📈")
    print("="*65)
    print(" | ".join(best_thirds))
    
    r32_matches = armar_16vos_prode(winners, runners, best_thirds)
    
    print("\n" + "="*65)
    print("⚔️  FASE ELIMINATORIA (MATA-MATA) ⚔️")
    print("="*65)
    
    print("\n--- 16vos DE FINAL ---")
    r16_qualifiers = [simular_cruce_prode(a, b) for a, b in r32_matches]
        
    print("\n--- OCTAVOS DE FINAL ---")
    r16_matches = list(zip(r16_qualifiers[::2], r16_qualifiers[1::2]))
    qf_qualifiers = [simular_cruce_prode(a, b) for a, b in r16_matches]

    print("\n--- CUARTOS DE FINAL ---")
    qf_matches = list(zip(qf_qualifiers[::2], qf_qualifiers[1::2]))
    sf_qualifiers = [simular_cruce_prode(a, b) for a, b in qf_matches]

    print("\n--- SEMIFINALES ---")
    sf_matches = list(zip(sf_qualifiers[::2], sf_qualifiers[1::2]))
    finalists = [simular_cruce_prode(a, b) for a, b in sf_matches]

    print("\n--- GRAN FINAL ---")
    # Agregamos el parámetro es_final=True
    campeon = simular_cruce_prode(finalists[0], finalists[1], es_final=True)
    
    print("\n" + "="*65)
    print(f"👑 CAMPEÓN MUNDIAL 2026 (XGBOOST V2): {campeon.upper()} 👑")
    print("="*65 + "\n")

if __name__ == "__main__":
    generar_prode_ideal()