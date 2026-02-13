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

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    docs_url="/forecastservice/docs",
    openapi_url="/forecastservice/openapi.json",
    root_path="/api"
)

# Configures CORS
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
    """
    Simulate a forecast based on fake data inputted by the user.
    :param request: The fake bundle parameters.
    :param vendor_id: The id of the vendor.
    :param db: Database session.
    :return: A dictionary containing the forecast result for both reservation and collection.
    """

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
    """
    Generates a forecast based on an existing bundle in the database.
    :param bundle_id: ID of the bundle.
    :param vendor_id: ID of the vendor.
    :param db: Database session.
    :return: A dictionary containing the forecast result for both reservation and collection.
    :raises: HTTPException 500 if models cannot be loaded or if there is an error with accessing the database or if the prediction fails.
             HTTPException 404 if the bundle does not exist in the database.
    """

    # Raises a HTTPException if the models cannot be loaded.
    if not model_reservation or not model_collection:
        raise HTTPException(status_code=500, detail="ML Models not found")

    try:
        # Gets all data about the bundle using parameterised query
        query = text("SELECT * FROM bundles WHERE bundle_id = :bid AND vendor_id = :vid")
        bundle = db.execute(query, {'bid': bundle_id, 'vid': vendor_id}).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    try:
        # Gets the weather conditions and temperature using a helper function
        weather, temperature = get_current_weather(vendor_id, db)

        # Gets the required input data from the returned bundle data
        collection_start = pd.to_datetime(bundle['collection_start'])
        posting_time = pd.to_datetime(bundle['posting_time'])
        collection_end = pd.to_datetime(bundle['collection_end'])

        retail_price = bundle['retail_price']
        price = bundle['price']

        discount = max(0, (retail_price - price) / retail_price)

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

        # The input data dictionary is converted into a dataframe and passed to the predict helper function
        input_df = pd.DataFrame([input_data])
        result = predict(input_df)
        result['bundle_id'] = bundle_id

        # The prediction result is returned
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction Failed: {e}")


@app.get("/forecast/actuator")
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "message": "Forecast Service is running"}
