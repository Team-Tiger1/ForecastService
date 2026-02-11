import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text

from .auth import get_current_vendor_id
from .database import get_db
from .schemas import SimulationRequest
from .services import predict, get_current_weather, model_reservation, model_collection

load_dotenv()

app = FastAPI(
    docs_url="/forecastservice/docs",
    openapi_url="/forecastservice/openapi.json",
    root_path="/api"
)

origins = ["http://localhost:3000", "http://localhost:8080", "https://thelastfork.shop"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/forecast/simulate")
def simulate_forecast(
        request: SimulationRequest,
        vendor_id: str = Depends(get_current_vendor_id),
        db: Session = Depends(get_db)
):
    weather, temperature = get_current_weather(vendor_id, db)

    input_data = {
        'discount': request.discount,
        'price': request.price,
        'weather': weather,
        'category': request.category,
        'temperature': temperature,
        'day': request.day,
        'lead_time': max(0.0, request.lead_time),
        'window_length': max(1.0, request.window_length),
        'time_of_day': request.time_of_day
    }

    input_df = pd.DataFrame([input_data])
    return predict(input_df)


@app.get("/forecast/predict/{bundle_id}")
def predict_bundle(
        bundle_id: str,
        vendor_id: str = Depends(get_current_vendor_id),
        db: Session = Depends(get_db)
):
    if not model_reservation or not model_collection:
        raise HTTPException(status_code=500, detail="ML Models not found")

    try:
        query = text("SELECT * FROM bundles WHERE bundle_id = :bid AND vendor_id = :vid")
        bundle = db.execute(query, {'bid': bundle_id, 'vid': vendor_id}).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    try:
        weather, temperature = get_current_weather(vendor_id, db)

        collection_start = pd.to_datetime(bundle['collection_start'])
        posting_time = pd.to_datetime(bundle['posting_time'])
        collection_end = pd.to_datetime(bundle['collection_end'])

        retail_price = bundle['retail_price']
        price = bundle['price']

        if retail_price > 0:
            discount = max(0, (retail_price - price) / retail_price)
        else:
            discount = 1.0

        input_data = {
            'discount': discount,
            'price': float(bundle['price']),
            'weather': weather,
            'category': bundle['category'],
            'temperature': temperature,
            'day': collection_start.strftime('%A'),
            'lead_time': (collection_start - posting_time).total_seconds() / 3600,
            'window_length': (collection_end - collection_start).total_seconds() / 3600,
            'time_of_day': collection_start.hour
        }

        input_df = pd.DataFrame([input_data])
        result = predict(input_df)
        result['bundle_id'] = bundle_id
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail="Prediction Failed: {e}")


@app.get("/forecast/actuator")
def health_check():
    return {"status": "ok", "message": "Forecast Service is running"}