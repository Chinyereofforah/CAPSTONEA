from fastapi import FastAPI

app = FastAPI(
    title="DeFi Risk Monitor"
)

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "DeFi Risk Monitor API is live"
    }

@app.get("/health")
def health():
    return {"health": "ok"}