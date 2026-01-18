from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/forecast")
def get_forecast():
    return{"Prediction":"Prediction Here"}

if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port = 5000)