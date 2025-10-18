from flask import Blueprint, jsonify
import requests
from models import db, Weather
from datetime import datetime, timedelta

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
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
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
