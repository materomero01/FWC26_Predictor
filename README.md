
# World Cup 2026 PRODE Optimizer

Proyecto para maximizar aciertos en un PRODE del Mundial 2026.

## Objetivo
Predecir resultados 1X2 (local / empate / visitante) para todo el Mundial
desde un único estado inicial.

## Arquitectura

1. Datos históricos de selecciones
2. Ratings Elo
3. Modelo Poisson de goles
4. Simulación Monte Carlo
5. Generación automática de picks

## Stack
- pandas
- numpy
- scipy
- scikit-learn

## Próximos pasos

### 1. Conseguir datasets
- resultados históricos
- Elo ratings
- odds históricas/opcionales

### 2. Ejecutar:
python src/example.py
