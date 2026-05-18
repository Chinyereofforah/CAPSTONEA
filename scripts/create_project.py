from pathlib import Path

folders = [
    "backend/models",
    "backend/services",
    "backend/routes",
    "backend/data/models",
    "frontend/pages",
    "frontend/assets",
    "scripts"
]

for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)

files = [
    "backend/app.py",
    "backend/config.py",
    "backend/database.py",

    "backend/models/risk_model.py",
    "backend/models/shap_explainer.py",
    "backend/models/feature_engineering.py",

    "backend/services/ethereum_service.py",
    "backend/services/dexscreener_service.py",
    "backend/services/whale_tracker.py",
    "backend/services/smart_money.py",
    "backend/services/rugpull_detector.py",
    "backend/services/websocket_stream.py",
    "backend/services/telegram_alerts.py",

    "backend/routes/dashboard.py",
    "backend/routes/alerts.py",
    "backend/routes/analytics.py",

    "frontend/dashboard.py",

    "frontend/pages/home.py",
    "frontend/pages/analytics.py",
    "frontend/pages/whale_tracking.py",
    "frontend/pages/smart_money.py",
    "frontend/pages/alerts.py",
    "frontend/pages/settings.py",

    "scripts/train_model.py",
    "scripts/ingest_data.py",
    "scripts/start_all.py",

    "requirements.txt",
    ".env",
    "README.md"
]

for file in files:
    Path(file).touch(exist_ok=True)

print("PROJECT CREATED SUCCESSFULLY")