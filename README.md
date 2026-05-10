# ⚽ FWC 2026 AI Predictor (Console Edition)

Este proyecto es un motor de predicción avanzado para el Mundial 2026, basado en **Machine Learning (XGBoost)** y simulaciones de **Monte Carlo**. 

## 🧠 El Cerebro del Modelo
A diferencia de otros predictores, este sistema utiliza:
* **XGBoost Regressor:** Entrenado con resultados históricos para predecir Lambdas (goles esperados).
* **Distribución de Poisson:** Para convertir esos Lambdas en probabilidades de resultados exactos.
* **Algoritmo de Penales:** Simulación penal por penal basada en efectividad histórica real.

## 🛠️ Cómo usarlo
Para generar tu Prode, simplemente ejecutá el script principal:
```bash
python src/simular_prode_v2.py