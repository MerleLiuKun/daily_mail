"""
    墨迹天气爬虫模块
"""

from typing import Optional, List

import requests
from bs4 import BeautifulSoup

import config
from .entities import Weather


class WeatherCrawler:
    def __init__(self):
        self.base_url = "https://tianqi.moji.com/weather/"
        self.area = config.AREA
        self.html: Optional[BeautifulSoup] = None

    def __enter__(self) -> "WeatherCrawler":
        self.html = self.get_weather_html()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_weather_html(self) -> Optional[BeautifulSoup]:
        try:
            headers = {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            }
            resp = requests.get(self.base_url + self.area, headers=headers)
            soup = BeautifulSoup(resp.text, "lxml")
            return soup
        except Exception as e:
            print(f"Exception in get html. errors: {e}")
            return None

    def get_tips(self) -> str:
        return self.html.select(".left > .wea_tips.clearfix > em")[0].get_text()

    def get_days_wea(self) -> List[Weather]:
        days_forecast: List[BeautifulSoup] = self.html.select(".wrap.clearfix")[
            2
        ].select(".left > .forecast.clearfix > .days.clearfix")

        data_set = []
        for day_f in days_forecast:
            day = day_f.select("li")[0].get_text().strip()
            wea = day_f.select("li")[1].get_text().strip()
            wea_icon = day_f.select("li > span > img")[0]["src"]
            temp = day_f.select("li")[2].get_text().strip()
            wind = day_f.select("li")[3].select("em")[0].get_text()
            wind_level = day_f.select("li")[3].select("b")[0].get_text()
            air = day_f.select("li")[4].get_text().strip()
            air_level = day_f.select("li")[4].select("strong")[0]["class"][0]

            data_set.append(
                Weather(
                    day=day,
                    wea=wea,
                    wea_icon=wea_icon,
                    temp=temp,
                    wind=f"{wind}--{wind_level}",
                    air=air,
                    air_level=air_level,
                )
            )

        return data_set
