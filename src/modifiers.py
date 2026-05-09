# ==========================================
# modifiers.py
# Ajustes contextuales para el Mundial 2026
# ==========================================

# =====================================================================
# 1. VALOR DE MERCADO REAL (Transfermarkt 2024 - En Millones de Euros)
# =====================================================================
# Representa la jerarquía actual y talento bruto del plantel.
MARKET_VALUE_M = {
    "England": 1620, "France": 1360, "Spain": 1310, "Portugal": 864, 
    "Brazil": 778, "Germany": 773, "Netherlands": 766, "Argentina": 761, 
    "Belgium": 534, "Norway": 504, "Senegal": 474, "Morocco": 456, 
    "Turkey": 435, "Ivory Coast": 425, "Ecuador": 366, "Sweden": 363, 
    "Uruguay": 362, "United States": 356, "Switzerland": 322, "Colombia": 300, 
    "Croatia": 283, "Austria": 263, "Japan": 150, "Mexico": 140, 
    "South Korea": 110, "Canada": 90, "Algeria": 80, "Bosnia and Herzegovina": 80,
    "Ghana": 70, "Egypt": 60, "Tunisia": 50, "Australia": 50, "DR Congo": 50,
    "Iran": 45, "Saudi Arabia": 30, "Cape Verde": 15, "Uzbekistan": 15, 
    "Curaçao": 15, "New Zealand": 15, "Iraq": 10, "Jordan": 10, "Haiti": 10,
    # Los equipos que no estén en esta lista asumirán un valor base (ej. 10M) en el cálculo.
}

# =====================================================================
# 2. VENTAJA DE LOCALÍA Y "HINCHADA" 
# =====================================================================
# Bonos de ELO estáticos basados en el arrastre de público a Norteamérica.
HOST_ADVANTAGE = {
    # Tier 1: Organizadores oficiales (Juegan en casa, máxima ventaja)
    "United States": 50, 
    "Mexico": 50, 
    "Canada": 50,
    
    # Tier 2: Potencias con hinchada masiva e incondicional que viaja
    "Argentina": 35, 
    "Brazil": 30, 
    
    # Tier 3: Equipos con gran diáspora en Norteamérica o mucho arrastre regional
    "Colombia": 20, 
    "Uruguay": 15, 
    "Morocco": 15, 
    "Japan": 10
}

# =====================================================================
# 3. PEDIGRÍ MUNDIALISTA (Peso de la camiseta)
# =====================================================================
# Multiplicador que SOLO se activa en fases eliminatorias (Mata-Mata).
# Simula el "achique" de las selecciones menores ante los campeones del mundo.
PEDIGREE_BONUS = {
    "Brazil": 1.05,      # 5 Mundiales
    "Germany": 1.04,     # 4 Mundiales
    "Argentina": 1.03,   # 3 Mundiales
    "France": 1.02,      # 2 Mundiales
    "Uruguay": 1.02,     # 2 Mundiales
    "England": 1.01,     # 1 Mundial
    "Spain": 1.01,       # 1 Mundial
}

# =====================================================================
# 4. REPORTE DE LESIONES / AUSENCIAS (MANUAL OVERRIDE)
# =====================================================================
# FÓRMULA DE CÁLCULO PARA PENALIZACIÓN:
# Puntos a restar = (Valor del Jugador Lesionado / Valor Total del Equipo) * 300
# 
# Ejemplos:
# - Mbappé (180M) se lesiona en Francia (1360M) -> (180 / 1360) * 300 = -39 puntos.
# - Dibu Martínez (28M) se lesiona en Argentina (761M) -> (28 / 761) * 300 = -11 puntos.
# 
# NOTA: Los números deben ser NEGATIVOS.
INJURY_PENALTY = {
    # Agrega a los equipos aquí los días previos al Mundial según las noticias.
    # "France": -39,
    # "Argentina": -11,
}