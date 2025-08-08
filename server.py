from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def ping():
    return {"status": "ok"}

def start_api_server():
    uvicorn.run(app, host="0.0.0.0", port=10000)
