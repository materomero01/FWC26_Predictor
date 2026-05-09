import random
from collections import defaultdict

from groups import (
    GROUP_A, GROUP_B, GROUP_C, GROUP_D,
    GROUP_E, GROUP_F, GROUP_G, GROUP_H,
    GROUP_I, GROUP_J, GROUP_K, GROUP_L
)
from simular_grupo import simulate_group
from poisson_model import predict_score

# =========================
# CONFIG
# =========================

N_SIMULATIONS = 10000

GROUPS = {
    "A": GROUP_A,
    "B": GROUP_B,
    "C": GROUP_C,
    "D": GROUP_D,
    "E": GROUP_E,
    "F": GROUP_F,
    "G": GROUP_G,
    "H": GROUP_H,
    "I": GROUP_I,
    "J": GROUP_J,
    "K": GROUP_K,
    "L": GROUP_L,
}

# =========================
# CRUCES FIJOS DEL ROUND OF 32
# (ganadores vs runners-up — independientes de los 3ros)
# Fuente: FIFA World Cup 2026 Regulations
#
# Estructura: (ganador_grupo_X, segundo_grupo_Y)
# =========================

FIXED_MATCHUPS = [
    ("winner_A", "runner_B"),   # M33
    ("winner_C", "runner_D"),   # M34
    ("winner_E", "runner_F"),   # M35
    ("winner_G", "runner_H"),   # M36
    ("winner_I", "runner_J"),   # M37
    ("winner_K", "runner_L"),   # M38
    ("winner_B", "runner_A"),   # M39
    ("winner_D", "runner_C"),   # M40
    ("winner_F", "runner_E"),   # M41
    ("winner_H", "runner_G"),   # M42
    ("winner_J", "runner_I"),   # M43
    ("winner_L", "runner_K"),   # M44
]

# Los 8 mejores terceros se enfrentan a los 12 ganadores restantes
# según las combinaciones de grupos de donde vienen.
# Para simplificar la simulación usamos los grupos donde van los 3ros
# según el reglamento FIFA (tabla de posibles cruces)

# Tabla oficial FIFA: según qué grupos clasifican los 8 mejores 3ros,
# se asignan a cruces específicos. Usamos una simplificación:
# los 8 terceros clasificados se sortean aleatoriamente contra
# los 4 ganadores que no tienen cruce fijo con runners-up
# (M45-M48 en el bracket oficial)

# =========================
# SIMULATE ONE MATCH (knockout — sin empate)
# =========================

def simulate_ko_match(team_a, team_b):
    """Simula un partido eliminatorio. Si hay empate, penales (50/50)."""

    goals_a, goals_b = predict_score(team_a, team_b)

    if goals_a > goals_b:
        return team_a
    elif goals_b > goals_a:
        return team_b
    else:
        # penales: 50/50 con leve ventaja al favorito por ELO
        from elo import ratings
        elo_a = ratings[team_a]
        elo_b = ratings[team_b]
        prob_a = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
        return team_a if random.random() < prob_a else team_b

# =========================
# SIMULATE GROUP STAGE
# retorna: {
#   "winners": {grupo: equipo},
#   "runners": {grupo: equipo},
#   "thirds": {grupo: (equipo, stats)}
# }
# =========================

def simulate_group_stage():

    winners = {}
    runners = {}
    thirds = {}

    for group_name, teams in GROUPS.items():

        table, stats = simulate_group(teams, verbose=False)

        winners[group_name] = table[0]
        runners[group_name] = table[1]
        thirds[group_name] = (table[2], stats[table[2]])

    return winners, runners, thirds

# =========================
# RANKING DE TERCEROS
# retorna los 8 mejores terceros por pts → gd → gf
# =========================

def get_best_thirds(thirds):

    sorted_thirds = sorted(
        thirds.items(),
        key=lambda x: (
            x[1][1]["pts"],
            x[1][1]["gd"],
            x[1][1]["gf"]
        ),
        reverse=True
    )

    # retorna lista de equipos (los 8 mejores)
    return [team for _, (team, _) in sorted_thirds[:8]]

# =========================
# ARMAR ROUND OF 32
# =========================

def build_round_of_32(winners, runners, best_thirds):

    matches = []

    # 12 cruces fijos: ganador vs runner-up
    for w_key, r_key in FIXED_MATCHUPS:
        group_w = w_key.split("_")[1].upper()
        group_r = r_key.split("_")[1].upper()
        matches.append((winners[group_w], runners[group_r]))

    # 8 cruces de ganadores vs mejores 3ros
    # los 4 ganadores restantes son los que no aparecen en FIXED_MATCHUPS
    # En el bracket oficial, los 8 mejores 3ros se asignan según tabla FIFA
    # Simplificación: sorteo aleatorio entre los ganadores sin cruce de 3ro
    # (en la práctica esto varía según qué grupos clasifica el 3ro)
    thirds_shuffled = best_thirds[:]
    random.shuffle(thirds_shuffled)

    # winners que van contra 3ros (todos los 12 grupos tienen un ganador,
    # pero 12 ya tienen cruce contra runner-up — los mismos ganadores
    # tienen cruce doble en el bracket oficial FIFA)
    # Según el reglamento: los 8 mejores 3ros van contra 8 ganadores específicos
    # asignados según de qué grupo vienen. Usamos los primeros 8 ganadores
    # que no tienen ya un cruce de 3ro asignado.
    all_winners = list(winners.values())
    random.shuffle(all_winners)
    for i, third in enumerate(thirds_shuffled):
        matches.append((all_winners[i % 12], third))

    return matches

# =========================
# SIMULATE KNOCKOUT ROUND
# =========================

def simulate_knockout_round(matches):
    return [simulate_ko_match(a, b) for a, b in matches]

# =========================
# SIMULATE FULL TOURNAMENT
# =========================

def simulate_tournament():

    # --- FASE DE GRUPOS ---
    winners, runners, thirds = simulate_group_stage()
    best_thirds = get_best_thirds(thirds)

    # 32 clasificados de grupos
    group_qualifiers = (
        set(winners.values()) |
        set(runners.values()) |
        set(best_thirds)
    )

    # --- ROUND OF 32 (32 → 16) ---
    r32_matches = build_round_of_32(winners, runners, best_thirds)
    r16_qualifiers = simulate_knockout_round(r32_matches)   # 16 que pasan

    # --- ROUND OF 16 (16 → 8) ---
    r16_matches = list(zip(r16_qualifiers[::2], r16_qualifiers[1::2]))
    qf_qualifiers = simulate_knockout_round(r16_matches)    # 8 que pasan

    # --- CUARTOS (8 → 4) ---
    qf_matches = list(zip(qf_qualifiers[::2], qf_qualifiers[1::2]))
    sf_qualifiers = simulate_knockout_round(qf_matches)     # 4 semifinalistas

    # --- SEMIFINALES (4 → 2) ---
    sf_matches = list(zip(sf_qualifiers[::2], sf_qualifiers[1::2]))
    finalists = simulate_knockout_round(sf_matches)         # 2 finalistas

    # --- FINAL ---
    champion = simulate_ko_match(finalists[0], finalists[1])

    return {
        "r32": group_qualifiers,          # 32 clasificados de grupos
        "r16": set(r16_qualifiers),       # 16 que ganaron R32
        "qf":  set(qf_qualifiers),        # 8 que ganaron R16
        "sf":  set(sf_qualifiers),        # 4 semifinalistas
        "final": set(finalists),          # 2 finalistas
        "champion": champion,
    }

# =========================
# MONTE CARLO MUNDIAL
# =========================

def simulate_world_cup_mc(n=N_SIMULATIONS):

    print(f"\n[mundial] Simulando {n:,} mundiales...\n")

    counters = {
        "r32": defaultdict(int),
        "r16": defaultdict(int),
        "qf": defaultdict(int),
        "sf": defaultdict(int),
        "final": defaultdict(int),
        "champion": defaultdict(int),
    }

    for i in range(n):
        if (i + 1) % 1000 == 0:
            print(f"[mundial] Iteración {i+1:,}/{n:,}...")

        result = simulate_tournament()

        for team in result["r32"]:
            counters["r32"][team] += 1
        for team in result["r16"]:
            counters["r16"][team] += 1
        for team in result["qf"]:
            counters["qf"][team] += 1
        for team in result["sf"]:
            counters["sf"][team] += 1
        for team in result["final"]:
            counters["final"][team] += 1
        counters["champion"][result["champion"]] += 1

    # =========================
    # IMPRIMIR RESULTADOS
    # =========================

    all_teams = list(counters["champion"].keys())

    # ordenar por probabilidad de ser campeón
    all_teams = sorted(
        all_teams,
        key=lambda t: counters["champion"][t],
        reverse=True
    )

    print(f"\n{'EQUIPO':<25} {'R32':>6} {'R16':>6} {'QF':>6} {'SF':>6} {'FINAL':>7} {'CAMPEÓN':>8}")
    print("-" * 75)

    for team in all_teams:
        r32  = counters["r32"][team] / n * 100
        r16  = counters["r16"][team] / n * 100
        qf   = counters["qf"][team] / n * 100
        sf   = counters["sf"][team] / n * 100
        fin  = counters["final"][team] / n * 100
        champ = counters["champion"][team] / n * 100

        print(
            f"{team:<25} "
            f"{r32:>5.1f}% "
            f"{r16:>5.1f}% "
            f"{qf:>5.1f}% "
            f"{sf:>5.1f}% "
            f"{fin:>6.1f}% "
            f"{champ:>7.1f}%"
        )

    return counters

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    simulate_world_cup_mc(N_SIMULATIONS)