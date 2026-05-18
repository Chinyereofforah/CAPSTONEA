import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print("KEY LOADED:", api_key[:10] if api_key else None)