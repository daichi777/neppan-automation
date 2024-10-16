# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()

# CORS settings (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Pydantic models
class MealPlan(BaseModel):
    count: int
    menuSelections: Optional[Dict[str, Dict[str, int]]] = None

class Reservation(BaseModel):
    reservation_number: str
    name: str
    name_kana: str
    email: str
    gender: str
    birth_date: str
    phone_number: str
    postal_code: str
    prefecture: str
    city_address: str
    building_name: Optional[str] = None
    past_stay: bool
    check_in_date: str
    num_nights: int
    num_units: int
    num_male: int
    num_female: int
    num_child_with_bed: int
    num_child_no_bed: int
    estimated_check_in_time: str
    purpose: str
    special_requests: Optional[str] = None
    transportation_method: str
    room_rate: float
    meal_plans: Dict[str, Any]
    total_guests: int
    guests_with_meals: int
    total_meal_price: float
    total_amount: float
    reservation_status: str
    stripe_payment_intent_id: Optional[str] = None
    payment_amount: Optional[float] = None
    payment_status: Optional[str] = None
    payment_method: str

@app.post("/create_reservation")
async def create_reservation(reservation: Reservation):
    # Here you can process the reservation data
    # For now, we'll just print it
    print("Received reservation data:", reservation)
    return {"status": "success", "message": "Reservation data received."}
