"""
    和风天气
    https://dev.qweather.com/docs/api/weather/weather-daily-forecast/
"""
from typing import List

import requests

import config
from .entities import Weather


class WeatherHeFeng:

    def __init__(self):
        self.base_url = (
            "https://devapi.qweather.com/v7/weather/3d"
            f"?location={config.HEFENG_LOCATION}&key={config.HEFENG_KEY}"
        )
        self.data = None

    def __enter__(self):
        try:
            resp = requests.get(url=self.base_url)
            if resp.ok:
                self.data = resp.json()["daily"]
            else:
                print(f"Hefeng weather response failed: {resp.text}")
        except Exception as e:
            print(f"Hefeng weather response failed: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

    def get_days_wea(self) -> List[Weather]:
        data_set = []
        if not self.data:
            return data_set
        days = {0: "今天", 1: "明天", 2: "后天"}
        for idx in range(3):
            item = self.data[idx]
            day_wea = Weather(
                day=days[idx],
                wea=item["textDay"],
                wea_icon="",
                temp=f"{int(item['tempMin'])}° / {int(item['tempMax'])}°",
                wind=f"{item['windDirDay']} {item['windScaleDay']}级",
                air="",
                air_level="",
            )
            day_wea.air_level = day_wea.get_air_level()
            data_set.append(day_wea)
        return self.data
