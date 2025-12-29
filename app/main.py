"""
    拼接并发送邮件
"""
import smtplib
from datetime import datetime, date
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from pathlib import Path

import psycopg2
import requests
import sentry_sdk
from jinja2 import Environment, PackageLoader

import config
from app.utils.entities import Content, Image
from app.utils.weather_crawler import WeatherCrawler
# from app.utils.weather_caiyun import WeatherCaiyun as WeatherCrawler
# from app.utils.weather_hefeng import WeatherHeFeng as WeatherCrawler
from app.utils.screenshot_lib import Driver

sentry_sdk.init(dsn=config.sentry_dsn)


def get_edm_config(day: str):
    conn = psycopg2.connect(
        database=config.PG_DB, user=config.PG_USER,
        password=config.PG_PASSWORD, host=config.PG_HOST
    )
    with conn.cursor() as cur:
        cur.execute(
            "SELECT subject,title,poetry,hitokoto FROM official_edmconfig "
            "WHERE day=%s;",
            (day,)
        )
        row = cur.fetchone()
        if row:
            return row
    conn.close()
    return "", "", "", ""


def update_edm_config(day, subject, title, poetry, hitokoto):
    conn = psycopg2.connect(
        database=config.PG_DB, user=config.PG_USER,
        password=config.PG_PASSWORD, host=config.PG_HOST
    )
    now = datetime.utcnow()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT day FROM official_edmconfig "
                "WHERE day=%s",
                (day,)
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO official_edmconfig "
                    "(day,subject,title,poetry,hitokoto,created,modified) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (day, subject, title, poetry, hitokoto, now, now)
                )
            else:
                cur.execute(
                    "UPDATE official_edmconfig "
                    "SET subject=%s,title=%s,poetry=%s,hitokoto=%s,modified=%s "
                    "WHERE day=%s",
                    (subject, title, poetry, hitokoto, day, now)
                )
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Update db error: {e}")
    finally:
        conn.close()


def render_html() -> (str, str):
    """
    获取数据并渲染 HTML 文件
    """
    # 准备数据
    # 初始化基础信息类
    content = Content()

    day = date.today().isoformat()

    # 获取自定义配置
    subject, title, poetry, hitokoto = get_edm_config(day=day)

    # 处理 subject
    if not subject:
        subject = "玲玲大宝宝"

    # 获取天气信息
    with WeatherCrawler() as wea:
        wea: WeatherCrawler
        if not title:
            content.title = "早安，亲爱的你"
        else:
            content.title = title
        wea_tips = "快来看今天的天气呀"
        weather_data = wea.get_days_wea()

    # 获取截图
    image = get_image_code()

    # 获取一言
    if hitokoto:
        content.hitokoto_say = hitokoto
    else:
        content.hitokoto_say = get_hitokoto_say()
        print(f"获得一言： {content.hitokoto_say}")

    # 获取今日诗词
    if poetry:
        content.shici_say = poetry
    else:
        content.shici_say = get_gushici_say()

    update_edm_config(
        day=day,
        subject=subject,
        title=content.title,
        poetry=content.shici_say, hitokoto=content.hitokoto_say
    )

    # 生成 HTML 文件
    env = Environment(loader=PackageLoader("app"))
    template = env.get_template("hei.html")
    html_content = template.render(
        content=content, weather_data=weather_data, image=image,
        wea_tips=wea_tips,
    )
    return html_content, subject


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


def get_gushici_say() -> str:
    default_msg = "北方有佳人，绝世而独立。"
    try:
        resp = requests.get(config.JINRISHICI_URL)
        if resp.status_code == 200:
            data = resp.json()
            return data["content"]
        else:
            return default_msg
    except Exception as e:
        print(f"Exception in get jinri shici, errors: {e}")
        return default_msg


def get_image_code() -> Image:
    """
    获取 一个 和 星座屋的截图
    """
    img = Image()

    # one
    one_filename = f"{config.IMAGE_FILE_PATH}/one.png"
    with Driver() as webdriver:
        webdriver.save_screenshot(
            url=config.ONE_URL, filename=one_filename, class_name="carousel-inner",
            one=True,
        )
        img.one = f"data:image/png;base64,{webdriver.to_base64(one_filename)}"

    # xingzuowu
    xzw_filename = f"{config.IMAGE_FILE_PATH}/xzw.png"
    with Driver() as webdriver:
        webdriver.save_screenshot(
            url=config.XINGZUOWU_URL,
            filename=xzw_filename,
            class_name="c_main",
            xzw=True
        )
        img.xingzuowu = f"data:image/png;base64,{webdriver.to_base64(xzw_filename)}"

    return img


def send_email(subject, html):
    def _format_address(name, addr):
        return formataddr((Header(name, "utf-8").encode(), addr))

    message = MIMEText(html, "html", "utf-8")
    message["From"] = _format_address("Ikaros", config.sender)
    message["To"] = _format_address("柠柠", config.receiver)
    message["Subject"] = Header(subject, "utf-8")

    try:
        smtp_obj = smtplib.SMTP("", port=587)
        smtp_obj.ehlo("smtp.qq.com")
        smtp_obj.starttls()
        smtp_obj.login(config.sender, config.email_password)
        smtp_obj.sendmail(config.sender, [config.receiver], message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        print("Error: 无法发送邮件")


def handler():
    """
    流程处理函数
    """
    print(f"Begin task at {datetime.now().isoformat()}")
    # HTML 文件
    try:
        html, subject = render_html()
        # 存储一下每日的html源
        month = date.today().strftime("%Y%m")
        p = Path(config.IMAGE_FILE_PATH) / month
        if not p.exists():
            p.mkdir(parents=True)
        with open(f"{p}/{date.today().isoformat()}.html", "w") as f:
            f.write(html)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        print(f"Exception in render html. errors: {e}")
        return False

    # 下发邮件
    send_email(
        subject=subject,
        html=html,
    )
    print(f"End task at {datetime.now().isoformat()}")


if __name__ == "__main__":
    handler()
