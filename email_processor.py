import imaplib
import email
from email.header import decode_header
import re
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS
import chardet

def connect_to_email():
    mail = imaplib.IMAP4_SSL(EMAIL_HOST, EMAIL_PORT)
    mail.login(EMAIL_USER, EMAIL_PASS)
    return mail

def get_unread_emails(mail):
    mail.select('inbox')
    _, search_data = mail.search(None, 'UNSEEN')
    return search_data[0].split()

def decode_mime_words(s):
    return ''.join(
        word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
        for word, encoding in decode_header(s)
    )

def process_email(mail, email_id):
    try:
        _, msg_data = mail.fetch(email_id, '(RFC822)')
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)
        
        subject = email_message["Subject"]
        if subject:
            subject = decode_mime_words(subject)
        else:
            subject = "No Subject"
        
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset()
                    if charset is None:
                        charset = chardet.detect(payload)['encoding']
                    try:
                        body = payload.decode(charset, 'ignore')
                    except UnicodeDecodeError:
                        body = payload.decode('utf-8', 'ignore')
                    break
        else:
            payload = email_message.get_payload(decode=True)
            charset = email_message.get_content_charset()
            if charset is None:
                charset = chardet.detect(payload)['encoding']
            try:
                body = payload.decode(charset, 'ignore')
            except UnicodeDecodeError:
                body = payload.decode('utf-8', 'ignore')
        
        if "予約通知" in subject:
            return parse_reservation_email(body), subject, "new"
        elif "予約キャンセル通知" in subject:
            return parse_cancellation_email(body), subject, "cancel"
        else:
            print(f"Skip processing: {subject}")
            return None, subject, "skip"
    except Exception as e:
        print(f"Error processing email: {str(e)}")
        return None, "Error processing email", "error"

def parse_cancellation_email(body):
    reservation_number = re.search(r'\[予約番号\]:(\d+)', body)
    if reservation_number:
        return {"reservation_number": reservation_number.group(1)}
    return None

def parse_reservation_email(body):
    reservation = {}
    
    patterns = {
        'reservation_number': r'\[予約番号\]:(\d+)',
        'name': r'\[氏名\]:(.+?)様',
        'name_kana': r'\[氏名\]:.*?\((.*?)\)',
        'email': r'\[メール\]:(.+)',
        'birth_date': r'\[生年月日\]:(\d{4})年(\d{2})月(\d{2})日',
        'gender': r'\[性別\]:(.+)',
        'postal_code': r'\[郵便番号\]:(\d+)',
        'address': r'\[ご住所\]:(.+)',
        'phone_number': r'連絡先（主）\s*(\d+)',
        'check_in_date': r'\[宿泊日\]:(\d{4}/\d{2}/\d{2})',
        'num_nights': r'\[宿泊日\]:.*?から(\d+)泊',
        'num_guests': r'(\d+)名',
        'estimated_check_in_time': r'\[チェックイン予定時間\]:(.+)',
        'purpose': r'\[【ご利用目的】\]:(.+?)\s',
        'transportation_method': r'\[交通手段\]:(.+?)\s',
        'total_amount': r'合計:([\d,]+)円',
        'special_requests': r'\[その他ご要望など\]:(.+)',
        'past_stay': r'\[過去のご宿泊\]:(.+)'
    }
    
    print("Debug: Parsing email body")
    print(f"Email body: {body}")
    
    for key, pattern in patterns.items():
        match = re.search(pattern, body)
        if match:
            if key == 'birth_date':
                reservation[key] = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            elif key == 'total_amount':
                reservation[key] = float(match.group(1).replace(',', ''))
            elif key in ['num_nights', 'num_guests']:
                reservation[key] = int(match.group(1))
            elif key == 'past_stay':
                reservation[key] = match.group(1) != "今回が初めてです。"
            elif key == 'gender':
                reservation[key] = 'male' if '男性' in match.group(1) else 'female'
            elif key == 'purpose':
                purpose_map = {
                    'ご旅行': 'travel',
                    '記念日': 'anniversary',
                    '大人の誕生日': 'birthday_adult',
                    'お子様の誕生日': 'birthday_minor'
                }
                raw_purpose = match.group(1).strip()
                reservation[key] = purpose_map.get(raw_purpose, 'other')
            elif key == 'transportation_method':
                method_map = {
                    '車': 'car',
                    '電車': 'train'
                }
                raw_method = match.group(1).split()[0]  # 最初の単語のみ取得
                reservation[key] = method_map.get(raw_method, 'other')
            else:
                reservation[key] = match.group(1).strip()
        else:
            print(f"Debug: No match found for {key}")
    
    # 都道府県と市区町村を分離
    if 'address' in reservation:
        address_parts = reservation['address'].split(' ', 1)
        if len(address_parts) == 2:
            reservation['prefecture'] = address_parts[0]
            reservation['city_address'] = address_parts[1][:255]  # 255文字で切り取り
        else:
            print("Debug: Unable to split address into prefecture and city_address")
            reservation['prefecture'] = reservation['address'][:20]  # 20文字で切り取り
            reservation['city_address'] = ''
    
    # 男性と女性の人数を設定
    reservation['num_male'] = reservation.get('num_guests', 0) if reservation.get('gender') == 'male' else 0
    reservation['num_female'] = reservation.get('num_guests', 0) if reservation.get('gender') == 'female' else 0
    
    print(f"Debug: Parsed reservation data: {reservation}")
    
    reservation['num_units'] = 1
    reservation['total_guests'] = reservation.get('num_guests', 0)
    reservation['reservation_status'] = 'pending'
    reservation['num_child_with_bed'] = 0
    reservation['num_child_no_bed'] = 0
    reservation['room_rate'] = reservation.get('total_amount', 0)
    reservation['guests_with_meals'] = reservation.get('total_guests', 0)
    reservation['total_meal_price'] = 0
    
    return reservation