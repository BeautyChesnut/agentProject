"""LangChain Tool 版本的天气工具"""
import logging
import requests
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class WeatherInput(BaseModel):
    """天气查询工具的输入参数"""
    city: str = Field(description="要查询天气的城市名称，如：北京、上海、广州等")


class WeatherTool(BaseTool):
    """
    天气查询工具（LangChain Tool 版本）
    
    使用 Open-Meteo API 查询实时天气信息
    """
    
    name: str = "weather"
    description: str = "查询指定城市的实时天气信息。输入城市名称，返回温度、湿度、天气状况等信息。"
    args_schema: Type[BaseModel] = WeatherInput
    
    # 天气代码映射
    WEATHER_CODES: dict = {
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
    
    # 城市经纬度映射
    CITY_COORDS: dict = {
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
        "重庆": (29.4316, 106.9123),
        "天津": (39.0842, 117.2009),
        "长沙": (28.2282, 112.9388),
    }
    
    def _run(self, city: str) -> str:
        """
        执行天气查询
        
        Args:
            city: 城市名称
            
        Returns:
            天气信息字符串
        """
        logger.info(f"🌤️ 调用天气工具: city='{city}'")
        
        if city not in self.CITY_COORDS:
            return f"❌ 暂不支持查询 {city} 的天气，支持的城市：{', '.join(self.CITY_COORDS.keys())}"
        
        try:
            lat, lon = self.CITY_COORDS[city]
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&"
                f"current=temperature_2m,relative_humidity_2m,"
                f"apparent_temperature,weather_code,"
                f"wind_speed_10m,wind_direction_10m&"
                f"timezone=Asia/Shanghai"
            )
            
            response = requests.get(url, timeout=20)
            
            if response.status_code != 200:
                return f"❌ 无法获取 {city} 的天气信息"
            
            data = response.json()
            current = data.get("current", {})
            
            temp = current.get("temperature_2m", "未知")
            feels_like = current.get("apparent_temperature", "未知")
            humidity = current.get("relative_humidity_2m", "未知")
            weather_code = current.get("weather_code", 0)
            weather_desc = self.WEATHER_CODES.get(weather_code, "未知")
            wind_speed = current.get("wind_speed_10m", "未知")
            wind_dir_deg = current.get("wind_direction_10m", 0)
            
            directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
            wind_dir = directions[int((wind_dir_deg + 22.5) // 45) % 8]
            
            result = f"""🌍 城市：{city}
🌡️ 温度：{temp}°C（体感 {feels_like}°C）
☁️ 天气：{weather_desc}
💧 湿度：{humidity}%
🌬️ 风向：{wind_dir}风，风速 {wind_speed} km/h"""
            
            logger.info(f"✅ 天气查询成功")
            return result
            
        except requests.exceptions.Timeout:
            return f"❌ 查询 {city} 天气超时，请稍后重试"
        except Exception as e:
            logger.error(f"❌ 天气查询失败: {e}")
            return f"❌ 查询天气时出错：{str(e)}"
    
    async def _arun(self, city: str) -> str:
        """异步执行（暂时使用同步实现）"""
        return self._run(city)
