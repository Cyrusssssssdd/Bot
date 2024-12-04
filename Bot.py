import ccxt
import telebot
import pandas as pd
import numpy as np
from flask import Flask

# تنظیمات Flask
app = Flask(name)

@app.route('/')
def home():
    return "ربات تلگرام فعال است!"

# توکن API تلگرام
API_TOKEN = '7935215736:AAFraa1FfdPguX3GT4oncJvIP3HwgRfDJWQ'
bot = telebot.TeleBot(API_TOKEN)

# اتصال به صرافی LBank
exchange = ccxt.lbank({
    'apiKey': '9a718819-00dd-4c53-92cf-c42653494306',
    'secret': 'D318E327664A9DD52F1398C82131FFE9'
})

# محاسبه میانگین متحرک
def calculate_moving_average(data, period):
    return pd.Series(data).rolling(window=period).mean().tolist()

# محاسبه RSI
def calculate_rsi(data, period=14):
    delta = np.diff(data)
    gains = np.where(delta > 0, delta, 0)
    losses = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gains).rolling(window=period).mean()
    avg_loss = pd.Series(losses).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()

# محاسبه حد ضرر و حد سود
def calculate_risk_reward(entry_price, risk=0.01, reward_ratio=3):
    stop_loss = entry_price * (1 - risk)  # حد ضرر
    take_profit1 = entry_price * (1 + reward_ratio * risk)  # حد سود ۱
    take_profit2 = entry_price * (1 + 2 * reward_ratio * risk)  # حد سود ۲
    take_profit3 = entry_price * (1 + 3 * reward_ratio * risk)  # حد سود ۳
    return stop_loss, take_profit1, take_profit2, take_profit3

# تحلیل بازار
def analyze_market(symbol):
    try:
        if not symbol.endswith("/USDT"):
            symbol += "/USDT"

        # دریافت داده‌های تاریخی
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        close_prices = [candle[4] for candle in ohlcv]

        # محاسبه اندیکاتورها
        ema_short = calculate_moving_average(close_prices, 10)
        ema_long = calculate_moving_average(close_prices, 30)
        rsi = calculate_rsi(close_prices)

        # قیمت فعلی
        last_price = close_prices[-1]

        # محاسبه حد ضرر و حد سود
        stop_loss, take_profit1, take_profit2, take_profit3 = calculate_risk_reward(last_price)

        # سیگنال ورود لانگ یا شورت
        if ema_short[-1] > ema_long[-1] and rsi[-1] < 70:
            entry_signal = "🔼 سیگنال لانگ: میانگین کوتاه‌مدت بالاتر از بلندمدت و RSI مناسب است."
        elif ema_short[-1] < ema_long[-1] and rsi[-1] > 30:
            entry_signal = "🔽 سیگنال شورت: میانگین کوتاه‌مدت پایین‌تر از بلندمدت و RSI مناسب است."
        else:
            entry_signal = "⚠️ هیچ سیگنال مشخصی یافت نشد."

        # بازگشت نتیجه
        return (f"{entry_signal}\n"
                f"💰 قیمت فعلی: {last_price:.2f} USDT\n"
                f"📈 RSI: {rsi[-1]:.2f}\n"
                f"🚨 حد ضرر: {stop_loss:.2f} USDT\n"
                f"🎯 حد سود ۱: {take_profit1:.2f} USDT\n"
                f"🎯 حد سود ۲: {take_profit2:.2f} USDT\n"
                f"🎯 حد سود ۳: {take_profit3:.2f} USDT")
    except Exception as e:
        return f"خطا در تحلیل: {e}"

# هندلر پیام‌های کاربر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "به ربات تحلیل ارز دیجیتال خوش آمدید!\n"
                          "برای دریافت تحلیل، نماد ارز مورد نظر خود را وارد کنید (مانند: BTC).")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    symbol = message.text.upper()  # تبدیل ورودی به حروف بزرگ
    result = analyze_market(symbol)  # تحلیل نماد
    bot.reply_to(message, result)  # ارسال نتیجه به کاربر

# اجرای سرور Flask و ربات تلگرام
if name == "main":
    from threading import Thread

    # اجرای Flask در یک ترد جداگانه
    Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()

    # اجرای ربات تلگرام
    bot.polling(none_stop=True)
