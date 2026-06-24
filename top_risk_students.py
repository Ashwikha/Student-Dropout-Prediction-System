import pandas as pd

data = pd.read_csv("dataset.csv")

data["RiskScore"] = (
(100-data["Attendance"])
+
(data["Backlogs"]*10)
+
((10-data["CGPA"])*5)
)

top = data.sort_values(
"RiskScore",
ascending=False
)

print(
top[
["RollNo",
"Department",
"RiskScore"]
].head(10)
)

dept_summary = data.groupby(
"Department"
).size()

print(dept_summary)