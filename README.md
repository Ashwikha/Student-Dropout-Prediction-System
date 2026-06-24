# Student Dropout Prediction System

The Student Dropout Prediction System is a web-based application developed using Flask and Machine Learning. The main objective of this project is to identify students who may be at risk of dropping out by analyzing academic and institutional factors. This helps educational institutions take early action and provide support to students who need it.

## Features

* Secure student and administrator login system
* Dashboard for managing student records
* Machine Learning-based dropout risk prediction
* Risk classification into Low, Medium, and High categories
* Student history tracking and record maintenance
* PDF report generation
* Data visualization through charts and graphs
* Student search and management functionality

## Technologies Used

* Python
* Flask
* Scikit-Learn
* Pandas
* SQLite
* HTML
* CSS

## Installation and Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Student-Dropout-Prediction-System.git
cd Student-Dropout-Prediction-System
```

### Step 2: Install Required Packages

```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
python app.py
```

### Step 4: Access the Application

Open your web browser and navigate to:

```text
http://127.0.0.1:5000
```

## Student Data Input

To generate predictions, users must provide the following student information:

| Field          | Description                                |
| -------------- | ------------------------------------------ |
| Student Name   | Name of the student                        |
| Roll Number    | Unique roll number assigned to the student |
| Department     | Department of study (CSE, IT, ECE, etc.)   |
| Year           | Current year of study                      |
| Attendance (%) | Student attendance percentage              |
| CGPA           | Current cumulative grade point average     |
| Backlogs       | Number of pending subjects                 |
| Internal Marks | Average internal assessment marks          |
| Fee Paid       | Indicates whether fees have been paid      |

### Sample Record

| Student Name | Roll Number | Department | Year | Attendance (%) | CGPA | Backlogs | Internal Marks | Fee Paid |
| ------------ | ----------- | ---------- | ---- | -------------- | ---- | -------- | -------------- | -------- |
| Ashwikha S   | CSE2025001  | CSE        | 2    | 85             | 8.7  | 0        | 78             | Yes      |

## How to Use

1. Log in to the system using administrator credentials.
2. Enter student details through the input form.
3. Submit the information to generate a prediction.
4. View the student's predicted dropout risk level.
5. Access reports, charts, and historical records from the dashboard.

## Project Goal

This project aims to demonstrate how Machine Learning can be applied in the education sector to identify students who may require additional academic support. By predicting dropout risk at an early stage, institutions can make informed decisions and improve student retention.

## Future Improvements

* Email notifications for high-risk students
* Cloud database integration
* Department-wise analytics
* Advanced reporting features
* Student performance tracking over time
* AI-based recommendations for student improvement
* Accessible and usable to multiple users

## Developed By

Ashwikha S
