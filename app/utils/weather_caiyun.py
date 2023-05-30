"""
    彩云 天气
"""
from typing import List

import requests

import config
from .entities import Weather

WEA_MAPPING = {
    "CLEAR_DAY": "🌞晴",
    "CLEAR_NIGHT": "🌞晴",
    "PARTLY_CLOUDY_DAY": "⛅多云",
    "PARTLY_CLOUDY_NIGHT": "⛅多云",
    "CLOUDY": "☁️阴",
    "LIGHT_HAZE": "轻度雾霾",
    "MODERATE_HAZE": "中度雾霾",
    "HEAVY_HAZE": "重度雾霾",
    "LIGHT_RAIN": "🌧️小雨",
    "MODERATE_RAIN": "🌧️中雨",
    "HEAVY_RAIN": "🌧️大雨",
    "STORM_RAIN": "🌧️暴雨",
    "FOG": "🌫️雾",
    "LIGHT_SNOW": "🌨小雪",
    "MODERATE_SNOW": "🌨中雪",
    "HEAVY_SNOW": "🌨大雪",
    "STORM_SNOW": "🌨暴雪",
    "DUST": "浮尘",
    "SAND": "沙尘",
    "WIND": "🌪️大风",
}


class WeatherCaiyun:
    def __init__(self):
        self.base_url = f"https://api.caiyunapp.com/v2.6/TAkhjf8d1nlSlspN/{config.AREA_LOCATION}/daily?dailysteps=5"
        self.data = None

    def __enter__(self):
        try:
            resp = requests.get(
                url=self.base_url
            )
            if resp.ok:
                self.data = resp.json()["result"]["daily"]
            else:
                print(f"Weather response failed: {resp.text}")
        except Exception as e:
            print(f"Weather data got error: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

    def get_days_wea(self) -> List[Weather]:
        data_set = []
        if not self.data:
            return data_set

        days = {0: "今天", 1: "明天", 2: "后天"}
        for idx in range(3):

            temp_dict = self.data["temperature"][idx]
            info = Weather(
                day=days[idx],
                wea=WEA_MAPPING.get(self.data["skycon"][idx]["value"], "晴"),
                wea_icon="",
                temp=f"{int(temp_dict['min'])}° / {int(temp_dict['max'])}°",
                wind="",
                air=self.data["air_quality"]["aqi"][idx]["avg"]["chn"],
                air_level=""
            )
            info.air_level = info.get_air_level()
            data_set.append(info)
        return data_set
