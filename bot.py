import asyncio
import time
from datetime import datetime
import schedule
import requests
from bs4 import BeautifulSoup
import re
import threading
import os

from flask import Flask
from pyrobale import Client

# ================== تنظیمات ==================
BOT_TOKEN = "1559701924:ZfiHv0-17U9MRn8dekd__nMKWn_bcRuCT_0"
CHAT_ID   = "5564173481"
# =============================================

IMAGE_PATH = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTaK2wAOe9CeU-FP_MES8V-tnNCzc7IFF6fxT1kv-u9ew&s=10"

# 🧪 حالت تست: هر ۱ ساعت
TEST_MODE = True
SEND_TIMES = ["10:00", "18:00"]

# ================== وب‌سرور برای Render ==================
app = Flask(__name__)

@app.route('/')
def home():
    return "GoldBot is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# =========================================================

def get_price_from_estjt():
    """قیمت طلای ۱۸ عیار رو از سایت اتحادیه طلا استخراج می‌کنه"""
    url = "https://www.estjt.ir/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text()

        pattern = r"طلا\s*۱۸\s*عیار[\s\S]*?([\d۰-۹]+[٫,\.][\d۰-۹٫,\.]+)"
        match = re.search(pattern, page_text)

        if match:
            price_str = match.group(1)
            price_str = price_str.replace("٫", "").replace(",", "").replace(".", "").strip()
            persian = "۰۱۲۳۴۵۶۷۸۹"
            english = "0123456789"
            price_str = price_str.translate(str.maketrans(persian, english))
            price = int(price_str)
            print(f"📊 قیمت از estjt.ir: {price:,} تومان")
            return price
        else:
            print("⚠️ الگو در estjt.ir پیدا نشد")
            return None
    except Exception as e:
        print(f"⚠️ خطا در estjt.ir: {e}")
        return None

def calculate_and_build_text(gheimat):
    payeh = gheimat + 100_000

    nim_gerami  = payeh * 1.07  * 0.5
    yek_gerami  = payeh * 1.05  * 1
    do_gerami   = payeh * 1.04  * 2
    se_gerami   = payeh * 1.04  * 3
    panj_gerami = payeh * 1.036 * 5

    payeh_fmt = f"{payeh:,.0f}"
    nim       = f"{nim_gerami:,.0f}"
    yek       = f"{yek_gerami:,.0f}"
    do        = f"{do_gerami:,.0f}"
    se        = f"{se_gerami:,.0f}"
    panj      = f"{panj_gerami:,.0f}"

    text = (
        f"💸 قیمت امروز شمش های گلدمایند به ازای هرگرم طلا ی عیار ۷۵۰\n"
        f"✔️در وزن های ۰/۵ تا ۵ گرم موجود است\n"
        f"💸 قیمت لحظه ای یک گرم طلا : {payeh_fmt}\n\n"
        f"✓ ۰/۵گرمی گلدمایند : {nim}ت\n\n"
        f"✓ ۱ گرم : {yek}ت\n\n"
        f"✓ ۲ گرم : {do}ت\n\n"
        f"✓ ۳ گرم : {se} ت\n\n"
        f"✓ ۵ گرم : {panj} ت\n\n"
        f"💎ارتباط با ما:\n"
        f"@GOLDMIND_ADMIN\n\n"
        f"☎️تماس:09121202331 قاسمی\n\n"
        f"🆔: ble.ir/join/2pqRkYqS17\n"
        f"#شمش\n"
        f"#گلدمایند"
    )
    return text

async def send_to_channel():
    try:
        gheimat = get_price_from_estjt()
        if gheimat is None:
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ❌ قیمت از سایت خونده نشد → ارسال لغو شد")
            return

        text = calculate_and_build_text(gheimat)
        client = Client(BOT_TOKEN)

        try:
            await client.send_photo(
                chat_id=CHAT_ID,
                photo=IMAGE_PATH,
                caption=text,
            )
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ✅ عکس + متن ارسال شد")
        except Exception as photo_error:
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ⚠️ عکس ارسال نشد ({photo_error}) → تلاش برای ارسال فقط متن")
            await client.send_message(
                chat_id=CHAT_ID,
                text=text,
            )
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ✅ فقط متن ارسال شد")

    except Exception as e:
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ❌ خطا: {e}")

def job():
    asyncio.run(send_to_channel())

def main():
    # اجرای وب‌سرور در thread جداگانه (برای Render)
    threading.Thread(target=run_web_server, daemon=True).start()
    print("🌐 وب‌سرور روی پورت", os.environ.get("PORT", 8080), "اجرا شد")

    if TEST_MODE:
        schedule.every(1).hours.do(job)
        print("🧪 حالت تست فعال است: هر ۱ ساعت یک پیام ارسال می‌شود")
    else:
        for t in SEND_TIMES:
            schedule.every().day.at(t).do(job)
        print(f"⏰ ربات فعال شد. ساعت‌های ارسال: {SEND_TIMES}")

    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    main()