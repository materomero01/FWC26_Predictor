from collections import defaultdict
from groups import (
    GROUP_A, GROUP_B, GROUP_C, GROUP_D,
    GROUP_E, GROUP_F, GROUP_G, GROUP_H,
    GROUP_I, GROUP_J, GROUP_K, GROUP_L
)
from elo import ratings
from poisson_model import predict_score
from poisson_model import predict_score_prode
# =========================
# DICCIONARIO DE GRUPOS
# =========================
GROUPS = {
    "A": GROUP_A, "B": GROUP_B, "C": GROUP_C, "D": GROUP_D,
    "E": GROUP_E, "F": GROUP_F, "G": GROUP_G, "H": GROUP_H,
    "I": GROUP_I, "J": GROUP_J, "K": GROUP_K, "L": GROUP_L,
}

# =========================
# 1. FASE DE GRUPOS CON POISSON (RESULTADOS EXACTOS)
# =========================
def resolver_grupos_prode():
    winners = {}
    runners = {}
    thirds_dict = {}
    
    print("="*50)
    print("🏆 FASE DE GRUPOS (RESULTADOS ESPERADOS) 🏆")
    print("="*50)

    for group_name, teams in GROUPS.items():
        print(f"\n--- GRUPO {group_name} ---")
        standings = defaultdict(lambda: {"pts": 0, "gf": 0, "ga": 0, "gd": 0})
        
        # Calendario de 6 partidos
        matches = [
            (teams[0], teams[1]), (teams[0], teams[2]), (teams[0], teams[3]),
            (teams[1], teams[2]), (teams[1], teams[3]), (teams[2], teams[3])
        ]
        
        for a, b in matches:
            # Obtenemos los goles exactos usando tu modelo
            goals_a, goals_b = predict_score_prode(a, b)
            print(f"  {a:>20} {goals_a} - {goals_b} {b:<20}")
            
            # Actualizar goles
            standings[a]["gf"] += goals_a
            standings[a]["ga"] += goals_b
            standings[b]["gf"] += goals_b
            standings[b]["ga"] += goals_a
            
            standings[a]["gd"] = standings[a]["gf"] - standings[a]["ga"]
            standings[b]["gd"] = standings[b]["gf"] - standings[b]["ga"]
            
            # Asignar puntos
            if goals_a > goals_b:
                standings[a]["pts"] += 3
            elif goals_b > goals_a:
                standings[b]["pts"] += 3
            else:
                standings[a]["pts"] += 1
                standings[b]["pts"] += 1

        # Ordenar tabla del grupo
        tabla = sorted(
            standings.items(),
            key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]),
            reverse=True
        )
        
        print(f"  -> Pasan: 1° {tabla[0][0]} | 2° {tabla[1][0]} | 3° {tabla[2][0]}")
        
        winners[group_name] = tabla[0][0]
        runners[group_name] = tabla[1][0]
        # Guardamos al tercero junto con sus estadísticas reales
        thirds_dict[group_name] = (tabla[2][0], tabla[2][1])
        
    return winners, runners, thirds_dict

# =========================
# 2. MEJORES TERCEROS CON ESTADÍSTICAS REALES
# =========================
def obtener_mejores_terceros_prode(thirds_dict):
    """Ordena a todos los terceros por Puntos, luego Diferencia de Gol, luego Goles a Favor."""
    sorted_thirds = sorted(
        thirds_dict.items(),
        key=lambda x: (
            x[1][1]["pts"],
            x[1][1]["gd"],
            x[1][1]["gf"]
        ),
        reverse=True
    )
    return [team for _, (team, _) in sorted_thirds[:8]]

# =========================
# 3. NUEVA LÓGICA DE 16vos DE FINAL (SIN DUPLICADOS)
# =========================
def armar_16vos_prode(winners, runners, best_thirds):
    matches = []

    # 1. Emparejamos a los 8 mejores terceros contra 8 ganadores específicos.
    grupos_contra_terceros = ["A", "B", "C", "D", "E", "F", "G", "H"]
    
    for i in range(8):
        ganador = winners[grupos_contra_terceros[i]]
        tercero = best_thirds[i]
        matches.append((ganador, tercero))

    # 2. Nos quedan 4 ganadores de grupo (I, J, K, L)
    ganadores_restantes = [winners["I"], winners["J"], winners["K"], winners["L"]]
    
    # Nos quedan los 12 runners (segundos de grupo)
    todos_los_segundos = list(runners.values())
    
    # 3. Los 4 ganadores restantes juegan contra 4 segundos
    for i in range(4):
        matches.append((ganadores_restantes[i], todos_los_segundos[i]))
        
    # 4. Los 8 segundos restantes juegan entre ellos
    segundos_restantes = todos_los_segundos[4:]
    for i in range(0, 8, 2):
         matches.append((segundos_restantes[i], segundos_restantes[i+1]))

    return matches

# =========================
# 4. PARTIDO KNOCKOUT (ELIMINACIÓN DIRECTA)
# =========================
def simular_cruce_prode(team_a, team_b):
    goals_a, goals_b = predict_score_prode(team_a, team_b)
    
    # Imprimir el resultado sin salto de línea para agregar quién pasa
    print(f"  {team_a:>20} {goals_a} - {goals_b} {team_b:<20}", end="")
    
    if goals_a > goals_b:
        print(f" ---> Pasa: {team_a}")
        return team_a
    elif goals_b > goals_a:
        print(f" ---> Pasa: {team_b}")
        return team_b
    else:
        # En caso de empate en los goles esperados, asume que van a penales
        # El equipo con mejor ELO gana la tanda de penales matemáticamente
        ganador = team_a if ratings[team_a] > ratings[team_b] else team_b
        print(f" ---> Empate (Pasa por penales: {ganador})")
        return ganador

# =========================
# 5. GENERAR EL PRODE COMPLETO
# =========================
def generar_prode_ideal():
    winners, runners, thirds_dict = resolver_grupos_prode()
    best_thirds = obtener_mejores_terceros_prode(thirds_dict)
    
    print("\n" + "="*50)
    print("📈 LOS 8 MEJORES TERCEROS QUE CLASIFICAN 📈")
    print("="*50)
    print(" | ".join(best_thirds))
    
    # Armamos la llave de 32 (16vos de final)
    r32_matches = armar_16vos_prode(winners, runners, best_thirds)
    
    print("\n" + "="*50)
    print("⚔️  FASE ELIMINATORIA (MATA-MATA) ⚔️")
    print("="*50)
    
    print("\n--- 16vos DE FINAL ---")
    r16_qualifiers = []
    for a, b in r32_matches:
        r16_qualifiers.append(simular_cruce_prode(a, b))
        
    print("\n--- OCTAVOS DE FINAL ---")
    r16_matches = list(zip(r16_qualifiers[::2], r16_qualifiers[1::2]))
    qf_qualifiers = []
    for a, b in r16_matches:
        qf_qualifiers.append(simular_cruce_prode(a, b))

    print("\n--- CUARTOS DE FINAL ---")
    qf_matches = list(zip(qf_qualifiers[::2], qf_qualifiers[1::2]))
    sf_qualifiers = []
    for a, b in qf_matches:
        sf_qualifiers.append(simular_cruce_prode(a, b))

    print("\n--- SEMIFINALES ---")
    sf_matches = list(zip(sf_qualifiers[::2], sf_qualifiers[1::2]))
    finalists = []
    for a, b in sf_matches:
        finalists.append(simular_cruce_prode(a, b))

    print("\n--- GRAN FINAL ---")
    campeon = simular_cruce_prode(finalists[0], finalists[1])
    
    print("\n" + "="*50)
    print(f"👑 CAMPEÓN DEL MUNDIAL 2026: {campeon.upper()} 👑")
    print("="*50 + "\n")

if __name__ == "__main__":
    generar_prode_ideal()