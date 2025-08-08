from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
def ping():
    return {"status": "ok"}

def start_api_server():
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
