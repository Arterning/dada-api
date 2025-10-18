from flask import Blueprint, jsonify
import requests
from models import db, Weather
from datetime import datetime, timedelta
from utils import get_china_time

weather_bp = Blueprint('weather', __name__)

# 天气 API 配置
WEATHER_API_URL = 'http://data-api.91weather.com/zoomlion2022/realtime'
WEATHER_API_PARAMS = {
    'lat': '28.2278',
    'lon': '112.9389'
}

# 获取天气数据的函数
def fetch_weather_data():
    """从外部 API 获取天气数据并保存到数据库"""
    try:
        response = requests.get(WEATHER_API_URL, params=WEATHER_API_PARAMS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 200 and data.get('data'):
            weather_data = data['data']

            # 创建新的天气记录
            weather = Weather(
                city='长沙',
                temperature=weather_data.get('tmp'),
                weather=weather_data.get('wp'),
                future_weather=weather_data.get('future_wp'),
                wind_direction=weather_data.get('wind_describe'),
                wind_speed=weather_data.get('wins'),
                sunrise=weather_data.get('sunrise'),
                sunset=weather_data.get('sunset')
            )

            db.session.add(weather)
            db.session.commit()

            print(f"天气数据已更新: {weather.weather}, {weather.temperature}°C")
            return True
        else:
            print(f"天气 API 返回错误: {data}")
            return False

    except Exception as e:
        print(f"获取天气数据失败: {str(e)}")
        return False

# 获取最新天气
@weather_bp.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """获取最新的天气数据"""
    # 获取最近1小时内的天气数据
    one_hour_ago = get_china_time() - timedelta(hours=1)
    weather = Weather.query.filter(
        Weather.created_at >= one_hour_ago
    ).order_by(Weather.created_at.desc()).first()

    # 如果没有最近的数据，尝试获取新数据
    if not weather:
        fetch_weather_data()
        weather = Weather.query.order_by(Weather.created_at.desc()).first()

    if not weather:
        return jsonify({'message': '暂无天气数据'}), 404

    return jsonify({
        'id': weather.id,
        'city': weather.city,
        'temperature': weather.temperature,
        'weather': weather.weather,
        'future_weather': weather.future_weather,
        'wind_direction': weather.wind_direction,
        'wind_speed': weather.wind_speed,
        'sunrise': weather.sunrise,
        'sunset': weather.sunset,
        'created_at': weather.created_at.isoformat(),
        'updated_at': weather.updated_at.isoformat()
    }), 200

# 手动更新天气
@weather_bp.route('/api/weather/refresh', methods=['POST'])
def refresh_weather():
    """手动刷新天气数据"""
    success = fetch_weather_data()
    if success:
        return jsonify({'message': '天气数据已更新'}), 200
    else:
        return jsonify({'message': '天气数据更新失败'}), 500

# 获取历史天气统计
@weather_bp.route('/api/weather/statistics', methods=['GET'])
def get_weather_statistics():
    """获取历史天气统计数据"""
    try:
        # 获取今年的天气数据（东八区）
        current_time = get_china_time()
        current_year = current_time.year
        start_of_year = current_time.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # 查询今年的所有天气数据，按日期去重（每天只取最新的一条）
        from sqlalchemy import func

        # 使用子查询获取每天最新的天气记录
        subquery = db.session.query(
            func.date(Weather.created_at).label('date'),
            func.max(Weather.id).label('max_id')
        ).filter(
            Weather.created_at >= start_of_year
        ).group_by(
            func.date(Weather.created_at)
        ).subquery()

        weather_records = db.session.query(Weather).join(
            subquery,
            Weather.id == subquery.c.max_id
        ).order_by(Weather.created_at.asc()).all()

        # 温度范围分类
        temp_ranges = {
            '0度以下': {'min': float('-inf'), 'max': 0, 'count': 0, 'color': '#4A90E2'},
            '0-10度': {'min': 0, 'max': 10, 'count': 0, 'color': '#7ED321'},
            '10-20度': {'min': 10, 'max': 20, 'count': 0, 'color': '#F5A623'},
            '20-30度': {'min': 20, 'max': 30, 'count': 0, 'color': '#F8E71C'},
            '30-35度': {'min': 30, 'max': 35, 'count': 0, 'color': '#FF6B6B'},
            '35度以上': {'min': 35, 'max': float('inf'), 'count': 0, 'color': '#D0021B'}
        }

        # 时间序列数据
        time_series = []

        # 统计数据
        for record in weather_records:
            if record.temperature is not None:
                # 时间序列数据
                time_series.append({
                    'date': record.created_at.strftime('%Y-%m-%d'),
                    'temperature': round(record.temperature, 1),
                    'weather': record.weather
                })

                # 温度范围统计
                temp = record.temperature
                for range_name, range_info in temp_ranges.items():
                    if range_info['min'] <= temp < range_info['max']:
                        range_info['count'] += 1
                        break

        # 转换温度范围数据为前端需要的格式
        temp_distribution = [
            {
                'name': range_name,
                'count': range_info['count'],
                'color': range_info['color']
            }
            for range_name, range_info in temp_ranges.items()
        ]

        return jsonify({
            'time_series': time_series,
            'temp_distribution': temp_distribution,
            'total_days': len(weather_records)
        }), 200

    except Exception as e:
        print(f"获取天气统计失败: {str(e)}")
        return jsonify({'message': '获取天气统计失败'}), 500
