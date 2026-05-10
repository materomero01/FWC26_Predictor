import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import os
import numpy as np

# =====================================================================
# train_xgb.py - VERSIÓN AUDITABLE
# Entrenamiento y validación de los modelos de goles Local/Visitante
# =====================================================================

def train_models():
    if not os.path.exists("data/xgboost_dataset.csv"):
        print("❌ Error: No se encuentra 'data/xgboost_dataset.csv'. Corre build_dataset.py primero.")
        return

    print("📊 Cargando dataset histórico...")
    df = pd.read_csv("data/xgboost_dataset.csv")

    # 1. Definir Features (X) y Targets (y)
    features = ["home_elo", "away_elo", "elo_diff", "is_neutral", "is_worldcup"]
    X = df[features]
    y_home = df["home_score"]
    y_away = df["away_score"]

    # División 80/20
    X_train, X_test, y_home_train, y_home_test, y_away_train, y_away_test = train_test_split(
        X, y_home, y_away, test_size=0.2, random_state=42
    )

    # 2. Configuración de Hiperparámetros (Poisson Regression)
    params = {
        "objective": "count:poisson",
        "eval_metric": "poisson-nloglik",
        "learning_rate": 0.05,
        "max_depth": 4,
        "min_child_weight": 2,
        "subsample": 0.8,
        "n_estimators": 250,
        "random_state": 42
    }

    # 3. Entrenamiento del Modelo para el Equipo A (Home)
    print("\n🧠 Entrenando cerebro para el Equipo A...")
    model_home = xgb.XGBRegressor(**params)
    model_home.fit(
        X_train, y_home_train,
        eval_set=[(X_test, y_home_test)],
        verbose=False
    )

    # 4. Entrenamiento del Modelo para el Equipo B (Away)
    print("🧠 Entrenando cerebro para el Equipo B...")
    model_away = xgb.XGBRegressor(**params)
    model_away.fit(
        X_train, y_away_train,
        eval_set=[(X_test, y_away_test)],
        verbose=False
    )

    # =====================================================================
    # 5. AUDITORÍA DEL APRENDIZAJE
    # =====================================================================
    print("\n" + "="*60)
    print("🕵️ RESULTADOS DE LA AUDITORÍA DE INTELIGENCIA ARTIFICIAL")
    print("="*60)

    # A. Error Absoluto Medio (MAE)
    preds_h = model_home.predict(X_test)
    preds_a = model_away.predict(X_test)
    mae_h = mean_absolute_error(y_home_test, preds_h)
    mae_a = mean_absolute_error(y_away_test, preds_a)
    
    print(f"📈 MAE Local:     Le erra por {mae_h:.3f} goles en promedio.")
    print(f"📈 MAE Visitante: Le erra por {mae_a:.3f} goles en promedio.")
    print(f"💡 (Un valor cercano a 1.0 es excelente para fútbol)")

    # B. Sanity Checks (Potencia vs Débil)
    # Creamos un escenario ficticio: Brasil (2100) vs San Marino (1100)
    check_df = pd.DataFrame([{
        "home_elo": 2100, "away_elo": 1100, "elo_diff": 1000, 
        "is_neutral": 1, "is_worldcup": 1
    }])
    l_h = model_home.predict(check_df)[0]
    l_a = model_away.predict(check_df)[0]
    print(f"\n🧪 Sanity Check (2100 ELO vs 1100 ELO en Mundial):")
    print(f"   Goles Esperados -> Favorito: {l_h:.2f} | Débil: {l_a:.2f}")

    # C. Visualización de Importancia de Variables
    print("\n📈 Generando gráficos de importancia... (Cierra la ventana para continuar)")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    xgb.plot_importance(model_home, ax=ax1, title="Importancia de Variables (Goles Local)", grid=False)
    xgb.plot_importance(model_away, ax=ax2, title="Importancia de Variables (Goles Visitante)", grid=False)
    
    plt.tight_layout()
    plt.show()

    # 6. Guardar modelos
    print("\n💾 Guardando modelos en carpeta 'models/'...")
    os.makedirs("models", exist_ok=True)
    model_home.save_model("models/xgb_home.json")
    model_away.save_model("models/xgb_away.json")
    print("✅ Todo listo. Ya puedes correr simular_prode_v2.py")

if __name__ == "__main__":
    train_models()