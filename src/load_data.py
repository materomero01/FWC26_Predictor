import pandas as pd

df = pd.read_csv("data/results.csv")

print(df.head())

print("\\nColumnas:")
print(df.columns.tolist())

print("\\nCantidad de partidos:")
print(len(df))