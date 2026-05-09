import numpy as np
from collections import Counter, defaultdict
from groups import (
    GROUP_A, GROUP_B, GROUP_C, GROUP_D,
    GROUP_E, GROUP_F, GROUP_G, GROUP_H,
    GROUP_I, GROUP_J, GROUP_K, GROUP_L
)
from elo import ratings
from poisson_model import get_lambdas
from penalties import get_penalty_winner, PENALTY_WIN_RATES, PENALTY_PLAYED

# =========================
# CONFIGURACIÓN
# =========================
N_SIMULACIONES = 1000000  # 1 Millón de universos paralelos por partido

GROUPS = {
    "A": GROUP_A, "B": GROUP_B, "C": GROUP_C, "D": GROUP_D,
    "E": GROUP_E, "F": GROUP_F, "G": GROUP_G, "H": GROUP_H,
    "I": GROUP_I, "J": GROUP_J, "K": GROUP_K, "L": GROUP_L,
}

# =========================
# MOTOR DE CONSENSO MONTE CARLO
# =========================
def obtener_consenso(team_a, team_b, n=N_SIMULACIONES, is_knockout=False):
    # Le pasamos el parámetro a get_lambdas
    lambda_a, lambda_b = get_lambdas(team_a, team_b, is_knockout=is_knockout)

    sims_a = np.random.poisson(lambda_a, n)
    sims_b = np.random.poisson(lambda_b, n)

    resultados = zip(sims_a, sims_b)
    conteo = Counter(resultados)
    mas_comun, frecuencia = conteo.most_common(1)[0]

    probabilidad = (frecuencia / n) * 100
    return mas_comun[0], mas_comun[1], probabilidad

# =========================
# 1. FASE DE GRUPOS MONTE CARLO
# =========================
def resolver_grupos_prode():
    winners = {}
    runners = {}
    thirds_dict = {}
    
    print("="*65)
    print(f"🏆 FASE DE GRUPOS ({N_SIMULACIONES:,} SIMULACIONES/PARTIDO) 🏆")
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
            print(f"  {a:>20} {goals_a} - {goals_b} {b:<20} [Dato: Ocurrió el {prob:.1f}% de las veces]")
            
            standings[a]["gf"] += goals_a
            standings[a]["ga"] += goals_b
            standings[b]["gf"] += goals_b
            standings[b]["ga"] += goals_a
            
            standings[a]["gd"] = standings[a]["gf"] - standings[a]["ga"]
            standings[b]["gd"] = standings[b]["gf"] - standings[b]["ga"]
            
            if goals_a > goals_b:
                standings[a]["pts"] += 3
            elif goals_b > goals_a:
                standings[b]["pts"] += 3
            else:
                standings[a]["pts"] += 1
                standings[b]["pts"] += 1

        tabla = sorted(
            standings.items(),
            key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]),
            reverse=True
        )
        
        print(f"  -> Pasan: 1° {tabla[0][0]} | 2° {tabla[1][0]} | 3° {tabla[2][0]}")
        
        winners[group_name] = tabla[0][0]
        runners[group_name] = tabla[1][0]
        thirds_dict[group_name] = (tabla[2][0], tabla[2][1])
        
    return winners, runners, thirds_dict

# =========================
# 2. MEJORES TERCEROS
# =========================
def obtener_mejores_terceros_prode(thirds_dict):
    sorted_thirds = sorted(
        thirds_dict.items(),
        key=lambda x: (x[1][1]["pts"], x[1][1]["gd"], x[1][1]["gf"]),
        reverse=True
    )
    return [team for _, (team, _) in sorted_thirds[:8]]

# =========================
# 3. LÓGICA DE 16vos DE FINAL
# =========================
def armar_16vos_prode(winners, runners, best_thirds):
    matches = []
    grupos_contra_terceros = ["A", "B", "C", "D", "E", "F", "G", "H"]
    for i in range(8):
        matches.append((winners[grupos_contra_terceros[i]], best_thirds[i]))
    
    ganadores_restantes = [winners["I"], winners["J"], winners["K"], winners["L"]]
    todos_los_segundos = list(runners.values())
    
    for i in range(4):
        matches.append((ganadores_restantes[i], todos_los_segundos[i]))
        
    segundos_restantes = todos_los_segundos[4:]
    for i in range(0, 8, 2):
         matches.append((segundos_restantes[i], segundos_restantes[i+1]))
    return matches

# =========================
# 4. PARTIDO KNOCKOUT (ELIMINACIÓN DIRECTA)
# =========================
# =========================
# 4. PARTIDO KNOCKOUT (ELIMINACIÓN DIRECTA)
# =========================
def simular_cruce_prode(team_a, team_b):
    goals_a, goals_b, prob = obtener_consenso(team_a, team_b, is_knockout=True)
    
    print(f"  {team_a:>20} {goals_a} - {goals_b} {team_b:<20} [Prob: {prob:.1f}%]", end="")
    
    if goals_a > goals_b:
        print(f" ---> Pasa: {team_a}")
        return team_a
    elif goals_b > goals_a:
        print(f" ---> Pasa: {team_b}")
        return team_b
    else:
        # === NUEVA LÓGICA DE PENALES ===
        ganador = get_penalty_winner(team_a, team_b, ratings[team_a], ratings[team_b])
        
        # Extraemos la data para mostrarla en el print
        rate_ganador = PENALTY_WIN_RATES.get(ganador, 0.50) * 100
        jugados_ganador = PENALTY_PLAYED.get(ganador, 0)
        
        print(f" ---> Empate (Pasa por penales: {ganador} | Historial: {rate_ganador:.0f}% en {jugados_ganador} tandas)")
        return ganador

# =========================
# 5. GENERAR EL PRODE COMPLETO
# =========================
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
    campeon = simular_cruce_prode(finalists[0], finalists[1])
    
    print("\n" + "="*65)
    print(f"👑 CAMPEÓN DEL MUNDIAL 2026 (CONSENSO): {campeon.upper()} 👑")
    print("="*65 + "\n")

if __name__ == "__main__":
    generar_prode_ideal()