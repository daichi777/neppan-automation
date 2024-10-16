# models.py

from pydantic import BaseModel

class Reservation(BaseModel):
    check_in_date: str
    nights: int
    room_type: str
    room_count: int
    adult_count: int
    child_count: int
    plan: str
    phone: str
    name_kana: str
    name: str
    notes: str
