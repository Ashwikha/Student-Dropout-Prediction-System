import pandas as pd

data = pd.read_csv("dataset.csv")

ranking = data.groupby(
"Department"
)["CGPA"].mean()

ranking = ranking.sort_values(
ascending=False
)

print(ranking)