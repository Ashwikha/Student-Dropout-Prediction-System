import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib

# Load dataset
data = pd.read_csv("dataset.csv")

# Convert Department names into numbers
encoder = LabelEncoder()
data["Department"] = encoder.fit_transform(data["Department"])

# Features (inputs)
X = data[[
    "Department",
    "Year",
    "Attendance",
    "CGPA",
    "Backlogs",
    "InternalMarks",
    "FeePaid"
]]

# Target (output)
y = data["Dropout"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Create model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

# Train model
model.fit(X_train, y_train)

# Test accuracy
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", round(accuracy * 100, 2), "%")

# Save model
joblib.dump(model, "dropout_model.pkl")

# Save department encoder
joblib.dump(encoder, "department_encoder.pkl")

print("Model Saved Successfully")