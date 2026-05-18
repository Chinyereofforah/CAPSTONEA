import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

def train_model():

    df = pd.read_csv("backend/data/training_data.csv")

    X = df.drop("target", axis=1)

    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print(classification_report(y_test, predictions))

    joblib.dump(
        model,
        "backend/data/models/risk_model.pkl"
    )

    print("MODEL TRAINED")