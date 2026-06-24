import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("dataset.csv")

dropout_count = data["Dropout"].value_counts()

plt.pie(
    dropout_count,
    labels=["Low Risk", "High Risk"],
    autopct="%1.1f%%"
)

plt.title("Student Dropout Distribution")
plt.show()