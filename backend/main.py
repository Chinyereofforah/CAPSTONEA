from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "AI DeFi Risk Monitor Backend Active"
    }