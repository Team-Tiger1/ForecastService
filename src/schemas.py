from pydantic import BaseModel

class SimulationRequest(BaseModel):
    price: float
    discount: float
    lead_time: float
    window_length: float
    weather: str
    category: str
    day: str
    time_of_day: int