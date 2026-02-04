from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv
from .auth import get_current_vendor_id
from .database import get_db

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/forecast")
def health_check():
    return {"status": "ok", "message": "Forecast Service is running"}


@app.get("/forecast/vendor-data")
def get_vendor_data(
    vendor_id: str = Depends(get_current_vendor_id),
    db: Session = Depends(get_db)
):
    try:
        query = text("SELECT * FROM product WHERE vendor_id = :vid")
        result = db.execute(query, {"vid": vendor_id}).fetchall()
        products = [row._asdict() for row in result]
        return {
            "vendor_id": vendor_id,
            "product_count": len(products),
            "products": products
        }
    except Exception as e:
        return {"error": str(e)}