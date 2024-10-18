import os
import time
import traceback
import re
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth
from dotenv import load_dotenv

def create_reservation_in_neppan(reservation_data):
    # 環境変数をロード
    load_dotenv()

    # ログイン情報を環境変数から取得
    KEIYAKU_CODE = os.getenv('KEIYAKU_CODE')
    USER_ID = os.getenv('USER_ID')
    PASSWORD = os.getenv('PASSWORD')

    # KEIYAKU_CODE, USER_ID, PASSWORDが取得できているか確認
    if not all([KEIYAKU_CODE, USER_ID, PASSWORD]):
        print("環境変数が正しく設定されていません。")
        return

    # ChromeDriverのパスを指定
    driver_path = 'C:\\Users\\OWNER\\Desktop\\neppan_automation\\chromedriver.exe'

    # Chromeオプションの設定
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument('--headless')  # ヘッドレスモードを無効化

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

    # 待機時間を延長
    wait = WebDriverWait(driver, 60)  # 60秒に延長

    try:
        # NEPPANのログインページにアクセス
        driver.get('https://www38.neppan.net/login.php')

        # フォーム要素の取得と入力
        wait.until(EC.presence_of_element_located((By.NAME, "loginForm:clientCode"))).send_keys(KEIYAKU_CODE)
        wait.until(EC.presence_of_element_located((By.NAME, "loginForm:loginId"))).send_keys(USER_ID)
        wait.until(EC.presence_of_element_located((By.NAME, "loginForm:password"))).send_keys(PASSWORD)

        # ログインボタンのクリック
        wait.until(EC.element_to_be_clickable((By.ID, "LoginBtn"))).click()

        # ページ遷移の待機
        time.sleep(5)

        # ログイン後のページタイトルとURLを出力
        print("ログイン後のページタイトル:", driver.title)
        print("ログイン後のURL:", driver.current_url)

        # ログインが成功しているか確認
        if "ログイン失敗" in driver.title:
            print("ログインに失敗しました。")
            driver.save_screenshot("login_failed.png")
            return

        # ログイン後、eaTop.phpページに遷移
        driver.get('https://www38.neppan.net/ea/eaTop.php')

        # ページ読み込み待機
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "display_header_title")))

        # 新規予約ボタンを見つけてクリック
        new_reservation_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "newReservebutton")))
        new_reservation_button.click()

        # iframeが読み込まれるのを待つ
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cboxIframe")))

        # iframeの一覧を取得
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"見つかったiframeの数: {len(iframes)}")
        for index, iframe in enumerate(iframes):
            print(f"iframe {index}: {iframe.get_attribute('id')} {iframe.get_attribute('name')}")

        # 最後に追加されたiframeに切り替え
        driver.switch_to.frame(iframes[-1])

        # 予約フォームの要素が読み込まれるのを待つ
        wait.until(EC.presence_of_element_located((By.ID, "txtCheckInDateSub")))

        # 予約データのフィールドをマッピング
        check_in_date = reservation_data["check_in_date"].replace('-', '/')
        num_nights = reservation_data["num_nights"]
        room_type = 'ヴィラ'  # デフォルト値
        num_units = reservation_data["num_units"]
        adult_count = reservation_data["num_male"] + reservation_data["num_female"]
        child_count = reservation_data["num_child_with_bed"] + reservation_data["num_child_no_bed"]
        plan = '1泊素泊まり'  # デフォルト値
        phone = reservation_data["phone_number"]
        name_kana = reservation_data["name_kana"]
        name = reservation_data["name"]
        special_requests = reservation_data.get("special_requests", "")
        total_guests = reservation_data["total_guests"]
        num_male = reservation_data["num_male"]
        num_female = reservation_data["num_female"]
        num_child_with_bed = reservation_data["num_child_with_bed"]
        num_child_no_bed = reservation_data["num_child_no_bed"]
        meal_plans = reservation_data.get("meal_plans", {})
        past_stay = reservation_data.get("past_stay", False)
        purpose = reservation_data.get("purpose", 'other')
        estimated_check_in_time = reservation_data.get("estimated_check_in_time")
        room_rate = reservation_data["room_rate"]  # 新しく追加

        # 備考欄の作成
        past_stay_text = '過去の宿泊あり' if past_stay else '過去の宿泊なし'

        purpose_mapping = {
            'travel': '旅行',
            'anniversary': '記念日',
            'birthday_adult': '誕生日(20歳以上)',
            'birthday_minor': '誕生日(20歳以下)',
            'other': 'その他'
        }
        purpose_text = purpose_mapping.get(purpose, 'その他')

        notes = f"""・利用人数{total_guests}人
・男性{num_male}人
・女性{num_female}人
・寝具あり子供{num_child_with_bed}人
・寝具なし子供{num_child_no_bed}人
・{past_stay_text}
・利用目的: {purpose_text}
"""

        if special_requests:
            notes += f"\nその他の要望:\n{special_requests}"

        # meal_plansの情報を備考欄に追加
        if meal_plans:
            notes += "\n\n食事プラン詳細:\n"
            for plan_name, plan_details in meal_plans.items():
                notes += f"\n{plan_name.upper()}　（{plan_details['count']}人）\n"
                if 'menuSelections' in plan_details:
                    for category, items in plan_details['menuSelections'].items():
                        for item, count in items.items():
                            notes += f"{item} {count}つ\n"

        # 予約情報を入力
        # 利用期間（チェックイン日）を入力
        checkin_input = wait.until(EC.presence_of_element_located((By.ID, "txtCheckInDateSub")))
        checkin_input.clear()
        checkin_input.send_keys(check_in_date)

        # 泊数を入力
        nights_input = wait.until(EC.presence_of_element_located((By.ID, "txtHakuNum")))
        nights_input.clear()
        nights_input.send_keys(str(num_nights))

        # 部屋タイプを選択
        room_type_select = Select(wait.until(EC.presence_of_element_located((By.ID, "roomType"))))
        room_options = [option.text for option in room_type_select.options]
        matching_rooms = [r for r in room_options if room_type in r]
        if matching_rooms:
            room_type_select.select_by_visible_text(matching_rooms[0])
        else:
            print(f"エラー: 部屋タイプ '{room_type}' が見つかりません。")

        # 部屋数を入力
        room_count_input = wait.until(EC.presence_of_element_located((By.ID, "txtRoomNum")))
        room_count_input.clear()
        room_count_input.send_keys(str(num_units))

        # 人数を入力
        adult_input = wait.until(EC.presence_of_element_located((By.ID, "txtAdultNum")))
        adult_input.clear()
        adult_input.send_keys(str(adult_count))

        child_input = wait.until(EC.presence_of_element_located((By.ID, "txtChildNum")))
        child_input.clear()
        child_input.send_keys(str(child_count))

        # プランを選択
        plan_select = Select(wait.until(EC.presence_of_element_located((By.ID, "accountSubject"))))
        plan_options = [option.text for option in plan_select.options]
        matching_plans = [p for p in plan_options if plan in p]
        if matching_plans:
            plan_select.select_by_visible_text(matching_plans[0])
        else:
            print(f"エラー: プラン '{plan}' が見つかりません。")

        # 予約者情報を入力
        wait.until(EC.presence_of_element_located((By.ID, "txtReserveTel"))).send_keys(phone)
        wait.until(EC.presence_of_element_located((By.ID, "txtReserveKana"))).send_keys(name_kana)
        wait.until(EC.presence_of_element_located((By.ID, "txtReserveName"))).send_keys(name)

        # 備考欄に情報を入力
        biko_input = wait.until(EC.presence_of_element_located((By.ID, "biko")))
        biko_input.clear()
        biko_input.send_keys(notes)

        # 予約登録ボタンをクリック
        register_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'updatebutton') and text()='予約登録']")))
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

        # 「明細入力へ」ボタンを見つけてクリック
        try:
            detail_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'updatebutton') and text()='明細入力へ']"))
            )
            print("「明細入力へ」ボタンが見つかりました。")
            detail_button.click()
            print("「明細入力へ」ボタンがクリックされました。")
        except Exception as e:
            print(f"「明細入力へ」ボタンが見つからないか、クリックできませんでした。エラー: {str(e)}")
            save_debug_info(driver, "error_detail_button")
            driver.quit()
            return

        # 明細入力画面への遷移を待つ
        try:
            wait.until(EC.url_contains("reservationUpdate.php"))
            print("明細入力画面に遷移しました。")
        except Exception as e:
            print(f"明細入力画面への遷移に失敗しました。エラー: {str(e)}")
            print(f"Current URL: {driver.current_url}")
            save_debug_info(driver, "error_reservation_update")
            driver.quit()
            return

        # フレームの切り替えが必要な場合はここで行う
        driver.switch_to.default_content()
        print("親フレームに戻りました。")

        # 明細入力画面の要素が表示されるのを待つ
        try:
            wait.until(EC.presence_of_element_located((By.ID, "input1")))
            print("明細入力画面に遷移しました。")
        except:
            print("明細入力画面への遷移に失敗しました。")
            print(f"Current URL: {driver.current_url}")
            save_debug_info(driver, "error_reservation_input")
            driver.quit()
            return

        # 明細入力画面の初期化
        actions = ActionChains(driver)

         # チェックイン時刻を設定
        if estimated_check_in_time:
            hour, minute = estimated_check_in_time.split(":")
            
            # 時間を設定
            checkin_time1 = wait.until(EC.presence_of_element_located((By.ID, "txtCheckinTime1")))
            driver.execute_script("arguments[0].value = arguments[1];", checkin_time1, hour)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", checkin_time1)

            # 分を設定
            checkin_time2 = wait.until(EC.presence_of_element_located((By.ID, "txtCheckinTime2")))
            driver.execute_script("arguments[0].value = arguments[1];", checkin_time2, minute)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", checkin_time2)

            print(f"チェックイン時刻を {estimated_check_in_time} に設定しました。")


        # セレクトボックスが含まれるセルを見つける
        cell = wait.until(EC.element_to_be_clickable((By.XPATH, "//td[@name='col1_2_1']")))

        # セルをクリックしてセレクトボックスを表示させる
        actions.move_to_element(cell).click().perform()

        # セレクトボックスが表示されるまで待つ
        select_element = wait.until(EC.visibility_of_element_located((By.ID, "selMeisaiKamoku1_1")))

        # JavaScriptを使用して直接値を設定（'102'は「1泊素泊まり」のvalue属性値）
        driver.execute_script("arguments[0].value = '102';", select_element)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", select_element)

        # 1泊素泊まりの単価（room_rate）を設定
        room_rate = reservation_data['room_rate']
        price_cell = wait.until(EC.element_to_be_clickable((By.XPATH, "//td[@name='col1_6_1']")))
        actions.move_to_element(price_cell).click().perform()
        time.sleep(0.5)  # 入力フィールドが表示されるのを待機

        # 単価入力フィールドが表示され、操作可能になるまで待機
        price_input = wait.until(EC.element_to_be_clickable((By.ID, "txtMeisaiPrice1_1")))

        # JavaScriptで単価を設定
        driver.execute_script("arguments[0].value = arguments[1];", price_input, str(room_rate))
        # 変更を反映させるためにイベントを発火
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", price_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('blur'));", price_input)

        print(f"1泊素泊まりの単価を {room_rate} に設定しました。")

        # 追加料理の明細を追加する関数を定義
        def add_additional_meal(quantity, unit_price):
            # 新しい明細行を追加
            add_detail_button = wait.until(EC.element_to_be_clickable((By.ID, "newbutton1")))
            add_detail_button.click()
            time.sleep(1)  # 行が追加されるのを待機

            # 新しい行のインデックスを取得
            rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'index1_')]")
            indices = []
            for row in rows:
                class_name = row.get_attribute("class")
                match = re.search(r'index1_(\d+)', class_name)
                if match:
                    indices.append(int(match.group(1)))
            new_index = max(indices)

            # 科目セルをクリックして科目を選択
            new_cell = wait.until(EC.element_to_be_clickable((By.XPATH, f"//td[@name='col1_2_{new_index}']")))
            actions.move_to_element(new_cell).click().perform()

            # 科目のセレクトボックスを操作
            new_select_element = wait.until(EC.visibility_of_element_located((By.ID, f"selMeisaiKamoku1_{new_index}")))
            driver.execute_script("arguments[0].value = '108';", new_select_element)  # '108'は「追加料理」のvalue属性値
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", new_select_element)

            # 数量を設定
            quantity_cell = wait.until(EC.element_to_be_clickable((By.XPATH, f"//td[@name='col1_5_{new_index}']")))
            actions.move_to_element(quantity_cell).click().perform()
            time.sleep(0.5)  # 入力フィールドが表示されるのを待機

            # 数量入力フィールドが表示され、操作可能になるまで待機
            quantity_input = wait.until(EC.element_to_be_clickable((By.ID, f"txtMeisaiCount1_{new_index}")))

            # JavaScriptで数量を設定
            driver.execute_script("arguments[0].value = arguments[1];", quantity_input, str(quantity))
            # 変更を反映させるためにイベントを発火
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", quantity_input)
            driver.execute_script("arguments[0].dispatchEvent(new Event('blur'));", quantity_input)

            # 単価を設定
            price_cell = wait.until(EC.element_to_be_clickable((By.XPATH, f"//td[@name='col1_6_{new_index}']")))
            actions.move_to_element(price_cell).click().perform()
            time.sleep(0.5)  # 入力フィールドが表示されるのを待機

            # 単価入力フィールドが表示され、操作可能になるまで待機
            price_input = wait.until(EC.element_to_be_clickable((By.ID, f"txtMeisaiPrice1_{new_index}")))

            # JavaScriptで単価を設定
            driver.execute_script("arguments[0].value = arguments[1];", price_input, str(unit_price))
            # 変更を反映させるためにイベントを発火
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", price_input)
            driver.execute_script("arguments[0].dispatchEvent(new Event('blur'));", price_input)

            print(f"追加料理の数量を {quantity} 、単価を {unit_price} に設定しました。")

        # meal_plansが空でない場合のみ追加料理を追加
        if meal_plans:
            plan_a_count = meal_plans.get('plan-a', {}).get('count', 0)
            plan_b_count = meal_plans.get('plan-b', {}).get('count', 0)
            plan_c_count = meal_plans.get('plan-c', {}).get('count', 0)

            # Plan A と Plan B の合計数を入力
            total_ab_count = plan_a_count + plan_b_count
            if total_ab_count > 0:
                unit_price_ab = 6500  # Plan A と Plan B の単価
                add_additional_meal(total_ab_count, unit_price_ab)
                print(f"追加料理（Plan A と Plan B）の数量を {total_ab_count} 、単価を {unit_price_ab} に設定しました。")

            # Plan C の処理（必要なら）
            if plan_c_count > 0:
                unit_price_c = 3000  # Plan C の単価
                add_additional_meal(plan_c_count, unit_price_c)
                print(f"追加料理（Plan C）の数量を {plan_c_count} 、単価を {unit_price_c} に設定しました。")

                 # 変更理由入力
        change_reason_input = wait.until(EC.presence_of_element_located((By.ID, "txtChangeMemo")))
        driver.execute_script("arguments[0].value = 'チェックイン時刻入力';", change_reason_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", change_reason_input)

        print("変更理由を入力しました。")

        # 予約登録ボタンをクリック
        register_button = wait.until(EC.element_to_be_clickable((By.ID, "btnReserveUpdate")))
        register_button.click()

        print("予約登録ボタンがクリックされました。")

        # アラートが表示される可能性があるため、待機して処理
        try:
            wait.until(EC.alert_is_present())
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
        print(f"Current URL: {driver.current_url}")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        traceback.print_exc()
        save_debug_info(driver, "error_exception")
    finally:
        # ブラウザを閉じる
        driver.quit()

def save_debug_info(driver, filename_prefix):
    # タイムスタンプを取得
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # スクリーンショットを保存
    screenshot_filename = f"{filename_prefix}_screenshot_{timestamp}.png"
    driver.save_screenshot(screenshot_filename)
    print(f"スクリーンショットを保存しました: {screenshot_filename}")
    # ページソースを保存
    page_source_filename = f"{filename_prefix}_page_source_{timestamp}.html"
    with open(page_source_filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"ページソースを保存しました: {page_source_filename}")