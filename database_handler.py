import psycopg2
from psycopg2 import sql
from config import DATABASE_URL
import json

def connect_to_db():
    return psycopg2.connect(DATABASE_URL)

def insert_reservation(conn, reservation):
    with conn.cursor() as cur:
        query = sql.SQL("""
            INSERT INTO reservations (
                reservation_number, name, name_kana, email, gender, birth_date,
                phone_number, postal_code, prefecture, city_address, past_stay,
                check_in_date, num_nights, num_units, num_male, num_female,
                num_child_with_bed, num_child_no_bed, estimated_check_in_time,
                purpose, special_requests, transportation_method, room_rate,
                total_guests, guests_with_meals, total_meal_price, total_amount,
                reservation_status, room_rates  -- ここを追加
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s  -- %s を追加
            )
            ON CONFLICT (reservation_number) DO NOTHING
            RETURNING id
        """)

        cur.execute(query, (
            reservation['reservation_number'],
            reservation['name'],
            reservation['name_kana'],
            reservation['email'],
            reservation['gender'],
            reservation['birth_date'],
            reservation['phone_number'],
            reservation['postal_code'],
            reservation['prefecture'],
            reservation['city_address'],
            reservation['past_stay'],
            reservation['check_in_date'],
            reservation['num_nights'],
            reservation['num_units'],
            reservation['num_male'],
            reservation['num_female'],
            reservation['num_child_with_bed'],
            reservation['num_child_no_bed'],
            reservation['estimated_check_in_time'],
            reservation['purpose'],
            reservation.get('special_requests', None),
            reservation['transportation_method'],
            reservation['room_rate'],
            reservation['total_guests'],
            reservation['guests_with_meals'],
            reservation['total_meal_price'],
            reservation['total_amount'],
            reservation['reservation_status'],
            json.dumps(reservation.get('room_rates', []))   # ここを修正
        ))

        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None

def update_reservation_status(conn, reservation_number, new_status):
    with conn.cursor() as cur:
        query = sql.SQL("""
            UPDATE reservations
            SET reservation_status = %s
            WHERE reservation_number = %s
            RETURNING id
        """)

        cur.execute(query, (new_status, reservation_number))
        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None
