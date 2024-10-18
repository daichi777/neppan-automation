import os
from dotenv import load_dotenv

load_dotenv()

KEIYAKU_CODE = os.getenv('KEIYAKU_CODE')
USER_ID = os.getenv('USER_ID')
PASSWORD = os.getenv('PASSWORD')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
DATABASE_URL = os.getenv('DATABASE_URL')