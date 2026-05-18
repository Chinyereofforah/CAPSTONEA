import os

os.system(
    "start powershell uvicorn backend.app:app --reload"
)

os.system(
    "start powershell streamlit run frontend/dashboard.py"
)