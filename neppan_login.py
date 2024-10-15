# neppan_login.py

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium_stealth import stealth
from dotenv import load_dotenv
from test_reservation_data import test_reservation

# 環境変数をロード
load_dotenv()

# ログイン情報を環境変数から取得
KEIYAKU_CODE = os.getenv('KEIYAKU_CODE')
USER_ID = os.getenv('USER_ID')
PASSWORD = os.getenv('PASSWORD')

# ChromeDriverのパスを指定
driver_path = 'C:\\Users\\OWNER\\Desktop\\neppan_automation\\chromedriver.exe'

# Chromeオプションの設定
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

# Serviceオブジェクトの作成
service = Service(executable_path=driver_path)

# ブラウザの起動
driver = webdriver.Chrome(service=service, options=options)

# selenium-stealthの適用
stealth(driver,
        languages=["ja-JP", "ja"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

# NEPPANのログインページにアクセス
driver.get('https://www38.neppan.net/login.php')

# 待機時間を延長
wait = WebDriverWait(driver, 30)  # 30秒に延長

# フォーム要素の取得と入力
wait.until(EC.presence_of_element_located((By.NAME, "loginForm:clientCode"))).send_keys(KEIYAKU_CODE)
wait.until(EC.presence_of_element_located((By.NAME, "loginForm:loginId"))).send_keys(USER_ID)
wait.until(EC.presence_of_element_located((By.NAME, "loginForm:password"))).send_keys(PASSWORD)

# ログインボタンのクリック
wait.until(EC.element_to_be_clickable((By.ID, "LoginBtn"))).click()

# ページ遷移の待機
time.sleep(5)

# ログイン後、eaTop.phpページに遷移
driver.get('https://www38.neppan.net/ea/eaTop.php')

# ページ読み込み待機
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "display_header_title")))

# 新規予約ボタンを見つけてクリック
new_reservation_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "newReservebutton")))
new_reservation_button.click()

# iframeが読み込まれるのを待つ
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cboxIframe")))

# iframeに切り替え
iframe = driver.find_element(By.CLASS_NAME, "cboxIframe")
driver.switch_to.frame(iframe)

# 予約フォームの要素が読み込まれるのを待つ
wait.until(EC.presence_of_element_located((By.ID, "txtCheckInDateSub")))

# 予約情報を入力
checkin_input = wait.until(EC.presence_of_element_located((By.ID, "txtCheckInDateSub")))
checkin_input.clear()
checkin_input.send_keys(test_reservation["check_in_date"])

# 泊数を入力
nights_input = wait.until(EC.presence_of_element_located((By.ID, "txtHakuNum")))
nights_input.clear()
nights_input.send_keys(str(test_reservation["nights"]))

# 人数を選択
adult_input = wait.until(EC.presence_of_element_located((By.ID, "txtAdultNum")))
adult_input.clear()
adult_input.send_keys(str(test_reservation["adult_count"]))

child_input = wait.until(EC.presence_of_element_located((By.ID, "txtChildNum")))
child_input.clear()
child_input.send_keys(str(test_reservation["child_count"]))

# プランを選択
plan_select = Select(wait.until(EC.presence_of_element_located((By.ID, "accountSubject"))))
plan_options = [option.text for option in plan_select.options]
print("利用可能なプラン:", plan_options)  # デバッグ用

# 完全一致するプランがない場合、部分一致で探す
target_plan = test_reservation["plan"]
matching_plans = [plan for plan in plan_options if target_plan in plan]

if matching_plans:
    plan_select.select_by_visible_text(matching_plans[0])
else:
    print(f"エラー: '{target_plan}' に一致するプランが見つかりません。")

# 予約者情報を入力
wait.until(EC.presence_of_element_located((By.ID, "txtReserveTel"))).send_keys(test_reservation["phone"])
wait.until(EC.presence_of_element_located((By.ID, "txtReserveKana"))).send_keys(test_reservation["name_kana"])
wait.until(EC.presence_of_element_located((By.ID, "txtReserveName"))).send_keys(test_reservation["name"])
wait.until(EC.presence_of_element_located((By.ID, "biko"))).send_keys(test_reservation["notes"])

# 予約登録ボタンをクリック
register_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "updatebutton")))
register_button.click()

print("予約登録ボタンがクリックされました。")

# アラートが表示されるのを待つ
wait.until(EC.alert_is_present())

# アラートを受け入れる
alert = driver.switch_to.alert
alert.accept()

print("アラートが受け入れられました。")

# 明示的な待機を追加
time.sleep(5)

print(f"Current URL after alert: {driver.current_url}")

# 「明細入力へ」ボタンを見つけてクリック
try:
    detail_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'updatebutton') and text()='明細入力へ']"))
    )
    print("「明細入力へ」ボタンが見つかりました。")
    detail_button.click()
    print("「明細入力へ」ボタンがクリックされました。")
except Exception as e:
    print(f"「明細入力へ」ボタンが見つからないか、クリックできませんでした。エラー: {str(e)}")
    print("Current page source:")
    print(driver.page_source)
    driver.save_screenshot("error_screenshot_2.png")
    print("スクリーンショットを保存しました。")

# 明細入力画面への遷移を待つ
try:
    WebDriverWait(driver, 10).until(EC.url_contains("reservationUpdate.php"))
    print("明細入力画面に遷移しました。")
except Exception as e:
    print(f"明細入力画面への遷移に失敗しました。エラー: {str(e)}")
    print(f"Current URL: {driver.current_url}")
    print("Current page source:")
    print(driver.page_source)
    driver.save_screenshot("error_screenshot_3.png")
    print("スクリーンショットを保存しました。")

# iframeから抜ける（親フレームに戻る）
driver.switch_to.default_content()

print("親フレームに戻りました。")

# 明細入力画面への遷移を待つ
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "maintable")))
    print("明細入力画面に遷移しました。")
except:
    print("明細入力画面への遷移に失敗しました。")
    print(f"Current URL: {driver.current_url}")
    print("Current page source:")
    print(driver.page_source)
    driver.save_screenshot("error_screenshot_3.png")
    print("スクリーンショットを保存しました。")

# セレクトボックスが含まれるセルを見つける
cell = wait.until(EC.presence_of_element_located((By.XPATH, "//td[@name='col1_2_1']")))

# セルをクリックしてセレクトボックスを表示させる
driver.execute_script("arguments[0].click();", cell)

# セレクトボックスが表示されるまで待つ
select_element = wait.until(EC.visibility_of_element_located((By.ID, "selMeisaiKamoku1_1")))

# JavaScriptを使用して直接値を設定
driver.execute_script("arguments[0].value = '102';", select_element)  # '102'は「1泊素泊まり」のvalue属性値

# 値が変更されたことをトリガーするためにchange eventを発火
driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", select_element)

# 追加料理の選択
# 新しい行を追加
add_detail_button = wait.until(EC.element_to_be_clickable((By.ID, "newbutton1")))
add_detail_button.click()

# 新しい行のセレクトボックスを操作
new_cell = wait.until(EC.presence_of_element_located((By.XPATH, "//td[@name='col1_2_2']")))
driver.execute_script("arguments[0].click();", new_cell)

new_select_element = wait.until(EC.visibility_of_element_located((By.ID, "selMeisaiKamoku1_2")))
driver.execute_script("arguments[0].value = '108';", new_select_element)  # '108'は「追加料理」のvalue属性値
driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", new_select_element)

# 予約登録ボタンをクリック
register_button = wait.until(EC.element_to_be_clickable((By.ID, "btnReserveUpdate")))
register_button.click()

print("予約登録ボタンがクリックされました。")

# アラートが表示される可能性があるため、待機して処理
try:
    WebDriverWait(driver, 5).until(EC.alert_is_present())
    alert = driver.switch_to.alert
    alert.accept()
    print("予約登録のアラートが受け入れられました。")
except:
    print("予約登録時にアラートは表示されませんでした。")

# 明示的な待機を追加
time.sleep(5)

# トップページに直接遷移
driver.get('https://www38.neppan.net/ea/eaTop.php')

# トップページの読み込みを待機
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "display_header_title")))

print("予約が正常に登録され、トップページに戻りました。")

# 現在のURLを表示（デバッグ用）
print(f"Current URL: {driver.current_url}")

# ブラウザを開いたままにする
input("Press Enter to close the browser...")