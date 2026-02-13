from pydantic import BaseModel

class SimulationRequest(BaseModel):
    """
    Defines the input structure for the simulation request.
    """
    price: float
    discount: float
    lead_time: float
    window_length: float
    weather: str
    category: str
    day: str
    time_of_day: int