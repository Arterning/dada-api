import schedule
import time
import threading
from weather_api import fetch_weather_data

def start_scheduler(app):
    """启动定时任务调度器"""
    def run_schedule():
        # 每小时执行一次
        schedule.every(1).hours.do(lambda: fetch_weather_with_context(app))

        # 立即执行一次
        fetch_weather_with_context(app)

        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

    def fetch_weather_with_context(app):
        """在应用上下文中执行天气数据获取"""
        with app.app_context():
            fetch_weather_data()

    # 在后台线程中运行调度器
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    print("天气数据定时任务已启动，每小时更新一次")
