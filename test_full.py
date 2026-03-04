import os
import requests
from dotenv import load_dotenv
from zhipuai import ZhipuAI
load_dotenv()

# 城市经纬度映射
CITY_COORDS = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "东莞": (23.0207, 113.7518),
    "杭州": (30.2741, 120.1551),
}

WEATHER_CODES = {
    0: "晴朗", 1: "基本晴朗", 2: "多云", 3: "阴天",
    45: "有雾", 61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    95: "雷暴",
}

def get_weather(city: str) -> str:
    coords = CITY_COORDS.get(city)
    if not coords:
        return f"❌ 暂不支持 {city}"
    
    lat, lon = coords
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=Asia/Shanghai"
    
    response = requests.get(url, timeout=10)
    data = response.json()
    current = data.get("current", {})
    
    temp = current.get("temperature_2m", "未知")
    feels_like = current.get("apparent_temperature", "未知")
    humidity = current.get("relative_humidity_2m", "未知")
    weather_code = current.get("weather_code", 0)
    weather_desc = WEATHER_CODES.get(weather_code, "未知")
    
    return f"🌍 {city} | 🌡️ {temp}°C（体感{feels_like}°C）| ☁️ {weather_desc} | 💧 {humidity}%"

# 初始化 GLM
glm_client = ZhipuAI(api_key=os.getenv("GLM_API_KEY"))

# 测试天气查询
print("🧪 测试天气查询功能：")
print(get_weather("东莞"))
print()

# 测试带天气的对话
def ask_with_weather(question: str):
    weather_keywords = ["天气", "气温", "温度"]
    is_weather = any(kw in question for kw in weather_keywords)
    
    city = None
    for c in CITY_COORDS.keys():
        if c in question:
            city = c
            break
    
    if is_weather and city:
        weather = get_weather(city)
        prompt = f"{question}\n\n【实时天气】\n{weather}\n\n请基于以上信息回答。"
    else:
        prompt = question
    
    response = glm_client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return response.choices[0].message.content

print("🧪 测试带天气的对话：")
print(f"问：东莞今天天气怎么样？")
print(f"答：{ask_with_weather('东莞今天天气怎么样？')}")
