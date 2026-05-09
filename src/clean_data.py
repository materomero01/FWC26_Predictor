import pandas as pd

df = pd.read_csv("data/results.csv")

# Convertir fecha
df["date"] = pd.to_datetime(df["date"])

# Eliminar filas con goles faltantes
df = df.dropna(subset=["home_score", "away_score"])

# Crear columna resultado
def get_result(row):
    if row["home_score"] > row["away_score"]:
        return "H"
    elif row["home_score"] < row["away_score"]:
        return "A"
    return "D"

df["result"] = df.apply(get_result, axis=1)

# Ordenar cronológicamente
df = df.sort_values("date").reset_index(drop=True)

print(df.head())

print("\\nRango de fechas:")
print(df["date"].min(), "->", df["date"].max())

print("\\nDistribución resultados:")
print(df["result"].value_counts(normalize=True))

print("\\nTorneos más frecuentes:")
print(df["tournament"].value_counts().head(20))