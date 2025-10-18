from datetime import datetime, timedelta, timezone

# 定义东八区时区
CHINA_TZ = timezone(timedelta(hours=8))

def get_china_time():
    """获取东八区当前时间"""
    return datetime.now(CHINA_TZ)

def utc_to_china_time(utc_time):
    """将UTC时间转换为东八区时间"""
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    return utc_time.astimezone(CHINA_TZ)
