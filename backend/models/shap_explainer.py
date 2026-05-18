import shap
import joblib
import pandas as pd

model = joblib.load(
    "backend/data/models/risk_model.pkl"
)

def explain(features):

    explainer = shap.TreeExplainer(model)

    shap_values = explainer.shap_values(features)

    return shap_values