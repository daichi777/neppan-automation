import schedule
import time
from main import main

def job():
    main()

# 1時間ごとにジョブを実行
schedule.every(1).hours.do(job)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)