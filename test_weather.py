import os
import requests
from dotenv import load_dotenv
load_dotenv()

# 城市经纬度映射
CITY_COORDS = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "东莞": (23.0207, 113.7518),
    "杭州": (30.2741, 120.1551),
    "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "南京": (32.0603, 118.7969),
    "苏州": (31.2990, 120.5853),
}

# 天气代码映射
WEATHER_CODES = {
    0: "晴朗",
    1: "基本晴朗", 2: "多云", 3: "阴天",
    45: "有雾", 48: "霜雾",
    51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "强冻雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    77: "雪粒",
    80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷暴", 96: "雷暴+小冰雹", 99: "雷暴+大冰雹",
}

def get_weather(city: str) -> str:
    """使用 Open-Meteo API 查询天气"""
    try:
        # 获取城市坐标
        coords = CITY_COORDS.get(city)
        if not coords:
            return f"❌ 暂不支持查询 {city} 的天气，支持的城市：{', '.join(CITY_COORDS.keys())}"
        
        lat, lon = coords
        
        # 调用 Open-Meteo API（免费、无需 API Key）
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m&timezone=Asia/Shanghai"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return f"❌ 无法获取 {city} 的天气信息"
        
        data = response.json()
        current = data.get("current", {})
        
        temp = current.get("temperature_2m", "未知")
        feels_like = current.get("apparent_temperature", "未知")
        humidity = current.get("relative_humidity_2m", "未知")
        weather_code = current.get("weather_code", 0)
        weather_desc = WEATHER_CODES.get(weather_code, "未知")
        wind_speed = current.get("wind_speed_10m", "未知")
        wind_dir_deg = current.get("wind_direction_10m", 0)
        
        # 风向转换
        directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
        wind_dir = directions[int((wind_dir_deg + 22.5) // 45) % 8]
        
        return f"""🌍 城市：{city}
🌡️ 温度：{temp}°C（体感 {feels_like}°C）
☁️ 天气：{weather_desc}
💧 湿度：{humidity}%
🌬️ 风向：{wind_dir}风，风速 {wind_speed} km/h"""
        
    except Exception as e:
        return f"❌ 查询天气时出错：{str(e)}"

# 测试
print("🌤️ 测试天气查询功能（Open-Meteo API）\n")
print(get_weather("东莞"))
print()
print(get_weather("北京"))
print()
print(get_weather("上海"))
