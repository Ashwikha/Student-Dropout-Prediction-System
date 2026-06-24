import pandas as pd
import requests
import os
from datetime import datetime

# 1. Load your student dataset
df = pd.read_csv('dataset.csv')
features = df.drop(columns=['Dropout'])

print(f"Starting predictions for {len(df)} students...")
predictions = []

# 2. Loop through each student record and send it to your local API
for index, row in features.iterrows():
    student_data = row.to_dict()
    try:
        response = requests.post('http://127.0.0.1:5000/predict', json=student_data)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and 'prediction' in result:
                predictions.append(result['prediction'])
            else:
                predictions.append(result)
        else:
            predictions.append("Error")
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Make sure your Flask app is running!")
        break

# 3. Process history storage
if len(predictions) == len(df):
    df['API_Prediction'] = predictions
    # Add a timestamp so you know when this prediction history was recorded
    df['Prediction_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    history_file = 'student_history.csv'
    
    # If the history file already exists, append to it without rewriting the header
    if os.path.exists(history_file):
        df.to_csv(history_file, mode='a', header=False, index=False)
        print(f"Predictions appended to existing history in '{history_file}'.")
    else:
        # Create a brand new history file
        df.to_csv(history_file, index=False)
        print(f"Created a new history file: '{history_file}'.")