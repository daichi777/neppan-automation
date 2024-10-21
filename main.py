# main.py

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from neppan_login import create_reservation_in_neppan
import logging
import schedule
import time
from email_processor import connect_to_email, get_unread_emails, process_email
from database_handler import connect_to_db, insert_reservation, update_reservation_status
import sys
import io
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS
from typing import List, Dict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Pydantic models
class MealPlan(BaseModel):
    count: int
    menuSelections: Optional[Dict[str, Dict[str, int]]] = None

class RoomRate(BaseModel):
    date: str
    price: float

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
    room_rates: List[RoomRate]  # この行を追加
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
async def create_reservation(reservation: Reservation, background_tasks: BackgroundTasks):
    # 予約データを受け取り、ログに出力
    logger.info(f"Received reservation data: {reservation.dict()}")
    
    # NEPPANへの予約作成をバックグラウンドで実行
    reservation_dict = reservation.dict()
    background_tasks.add_task(create_reservation_in_neppan, reservation_dict)
    
    return {"status": "success", "message": "Reservation data received, logged, and NEPPAN processing started."}

def process_email_reservations():
    try:
        logger.info("Starting email processing...")
        mail = connect_to_email()
        db_conn = connect_to_db()
        
        unread_emails = get_unread_emails(mail)
        logger.info(f"Total unread emails: {len(unread_emails)}")
        
        for i, email_id in enumerate(unread_emails):
            logger.info(f"Processing email {i+1} of {len(unread_emails)}")
            try:
                reservation_data, subject, action = process_email(mail, email_id)
                if action == "new":
                    try:
                        inserted_id = insert_reservation(db_conn, reservation_data)
                        if inserted_id:
                            logger.info(f"予約が挿入されました。ID: {inserted_id}")
                        else:
                            logger.info(f"予約番号 {reservation_data['reservation_number']} は既に存在します。")
                    except Exception as e:
                        logger.error(f"予約の挿入中にエラーが発生しました: {str(e)}")
                        logger.error(f"予約データ: {reservation_data}")
                elif action == "cancel":
                    try:
                        updated_id = update_reservation_status(db_conn, reservation_data['reservation_number'], 'customer_cancelled')
                        if updated_id:
                            logger.info(f"予約がキャンセルされました。ID: {updated_id}")
                        else:
                            logger.info(f"予約番号 {reservation_data['reservation_number']} は存在しません。")
                    except Exception as e:
                        logger.error(f"予約のキャンセル処理中にエラーが発生しました: {str(e)}")
                        logger.error(f"キャンセルデータ: {reservation_data}")
                else:
                    logger.info(f"処理対象外のメールです。スキップします。件名: {subject}")
            except Exception as e:
                logger.error(f"メール処理中にエラーが発生しました: {str(e)}")
                logger.exception("詳細なエラー情報:")
        
        mail.logout()
        db_conn.close()
        logger.info("Email processing completed")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        logger.exception("詳細なエラー情報:")

# スケジューラーの設定
def setup_scheduler():
    schedule.every(10).minutes.do(process_email_reservations)

@app.on_event("startup")
async def startup_event():
    setup_scheduler()
    # バックグラウンドでスケジューラーを実行
    import threading
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)
    threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test_email_process":
        print("Starting email processing test...")
        
        # メール接続情報のログ出力
        print(f"Connecting to email server: {EMAIL_HOST}")
        print(f"Using email account: {EMAIL_USER}")
        mail = connect_to_email()
        print("Connected successfully")
        
        # 未読メールの数を表示
        unread_emails = get_unread_emails(mail)
        print(f"Number of unread emails: {len(unread_emails)}")
        
        process_email_reservations()
        print("Email processing test completed.")
    else:
        print("Starting FastAPI server with scheduled email processing...")
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)