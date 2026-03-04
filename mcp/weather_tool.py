"""MCP 天气工具"""
import logging
import requests
from typing import Dict, Any
from .base import BaseMCPTool

logger = logging.getLogger(__name__)


class WeatherTool(BaseMCPTool):
    """天气查询工具（基于 Open-Meteo MCP）"""
    
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
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.timeout = config.get("config", {}).get("timeout", 20)
        self.timezone = config.get("config", {}).get("timezone", "Asia/Shanghai")
        self.supported_cities = config.get("config", {}).get("supported_cities", {})
        
        logger.info(f"✅ 天气工具初始化完成: 支持 {len(self.supported_cities)} 个城市")
    
    def execute(self, city: str = None, **kwargs) -> str:
        """
        查询天气
        
        Args:
            city: 城市名称
            
        Returns:
            天气信息
        """
        if not city:
            return "❌ 请提供城市名称"
        
        if city not in self.supported_cities:
            return f"❌ 暂不支持查询 {city} 的天气，支持的城市：{', '.join(self.supported_cities.keys())}"
        
        try:
            logger.info(f"📡 MCP Tool Call: get_weather(city='{city}')")
            
            lat, lon = self.supported_cities[city]
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&"
                f"current=temperature_2m,relative_humidity_2m,"
                f"apparent_temperature,weather_code,"
                f"wind_speed_10m,wind_direction_10m&"
                f"timezone={self.timezone}"
            )
            
            response = requests.get(url, timeout=self.timeout)
            
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
🌬️ 风向：{wind_dir}风，风速 {wind_speed} km/h
📡 来源：MCP Weather Service (open-meteo)"""
            
            logger.info(f"✅ MCP Tool Response received")
            return result
            
        except requests.exceptions.Timeout:
            return f"❌ 查询 {city} 天气超时，请稍后重试"
        except Exception as e:
            logger.error(f"❌ 天气查询失败: {e}")
            return f"❌ 查询天气时出错：{str(e)}"
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的 JSON Schema"""
        return {
            "name": self.name,
            "description": "查询指定城市的实时天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称",
                        "enum": list(self.supported_cities.keys())
                    }
                },
                "required": ["city"]
            }
        }
