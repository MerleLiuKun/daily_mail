"""
    拼接并发送邮件
"""
from datetime import datetime

import requests
from jinja2 import Environment, PackageLoader

import config
from app.utils.entities import Content, Image
from app.utils.weather_crawler import WeatherCrawler
from app.utils.screenshot_lib import Driver


def render_html() -> str:
    """
    获取数据并渲染 HTML 文件
    """
    # 准备数据
    # 初始化基础信息类
    content = Content()

    # 获取天气信息
    with WeatherCrawler() as wea:
        wea: WeatherCrawler
        content.title = f"早安，{wea.get_tips()}"
        weather_data = wea.get_days_wea()

    # 获取截图
    image = get_image_code()

    # 获取一言
    content.hitokoto_say = get_hitokoto_say()

    # 获取 one
    content.one_say = get_one_say()

    # 生成 HTML 文件
    env = Environment(loader=PackageLoader("app"))
    template = env.get_template("hei.html")
    html_content = template.render(
        content=content, weather_data=weather_data, image=image
    )
    return html_content


def get_hitokoto_say() -> str:
    default_msg = "看，你的眼里有星辰大海！"
    try:
        resp = requests.get(config.HITOKOTO_URL)
        if resp.status_code == 200:
            data = resp.json()
            return data["hitokoto"]
        else:
            return default_msg
    except Exception as e:
        print(f"Exception in get hitokoto say, errors: {e}")
        return default_msg


def get_one_say() -> str:
    today = datetime.today()
    if today.day % 2 == 0:
        return "One Is Enough!"
    else:
        return "一个，就够了！"


def get_image_code() -> Image:
    """
    获取 一个 和 星座屋的截图
    """
    img = Image()

    # one
    one_filename = f"{config.IMAGE_FILE_PATH}/one.png"
    with Driver() as webdriver:
        webdriver.save_screenshot(
            url=config.ONE_URL, filename=one_filename, class_name="carousel-inner"
        )
        img.one = f"data:image/png;base64,{webdriver.to_base64(one_filename)}"

    # xingzuowu
    xzw_filename = f"{config.IMAGE_FILE_PATH}/xzw.png"
    with Driver() as webdriver:
        webdriver.save_screenshot(
            url=config.XINGZUOWU_URL,
            filename=xzw_filename,
            class_name="c_main",
            height=535,  # 写死的高度
        )
        img.xingzuowu = f"data:image/png;base64,{webdriver.to_base64(xzw_filename)}"

    return img


def handler():
    """
    流程处理函数
    """

    # HTML 文件
    html = render_html()
    print(html)

    # 下发邮件


if __name__ == "__main__":
    handler()