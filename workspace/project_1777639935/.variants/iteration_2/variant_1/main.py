from fastapi import FastAPI

app = FastAPI()

@app.get("/status")
def status():
    return {"status": "operational"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)