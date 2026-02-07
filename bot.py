#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telegram
from flask import Flask, request, jsonify
import json
from datetime import datetime
import logging

# ==================== تنظیمات از محیط ====================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("لطفا TELEGRAM_TOKEN و TELEGRAM_CHAT_ID را در Environment Variables تنظیم کنید")

# ==================== راه‌اندازی ====================
bot = telegram.Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== منطق ترکیب سیگنال ====================
def check_combined_signal(lorentzian_signal, rsi_value):
    """
    ترکیب سیگنال Lorentzian و RSI طبق قانون شما
    """
    try:
        rsi = float(rsi_value)
        
        if lorentzian_signal == "buy" and rsi < 20:
            return "خرید ترکیبی"
        elif lorentzian_signal == "sell" and rsi > 80:
            return "فروش ترکیبی"
        else:
            return None
    except:
        return None

# ==================== Webhook TradingView ====================
@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    دریافت وب‌هوک از TradingView
    """
    try:
        # دریافت داده
        data = request.get_json()
        logger.info(f"📩 دریافت داده: {data}")
        
        # استخراج اطلاعات
        ticker = data.get('ticker', 'نامشخص')
        price = data.get('price', '0')
        rsi_value = data.get('rsi', '50')
        signal = data.get('signal', '').lower()
        
        # تشخیص سیگنال Lorentzian
        lorentzian_signal = None
        if 'buy' in signal or 'خرید' in signal:
            lorentzian_signal = "buy"
        elif 'sell' in signal or 'فروش' in signal:
            lorentzian_signal = "sell"
        
        # بررسی ترکیب سیگنال
        combined = check_combined_signal(lorentzian_signal, rsi_value)
        
        if combined:
            # ساخت پیام
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if combined == "خرید ترکیبی":
                emoji = "🟢"
                signal_type = "خرید"
                reason = "Lorentzian خرید + RSI زیر ۲۰"
            else:
                emoji = "🔴"
                signal_type = "فروش"
                reason = "Lorentzian فروش + RSI بالای ۸۰"
            
            message = f"{emoji} **سیگنال ترکیبی** {emoji}\n\n"
            message += f"📊 **نماد:** {ticker}\n"
            message += f"💰 **قیمت:** {price}\n"
            message += f"🎯 **نوع:** {signal_type}\n"
            message += f"📈 **RSI:** {rsi_value}\n"
            message += f"📌 **دلیل:** {reason}\n"
            message += f"⏰ **زمان:** {timestamp}\n"
            message += f"🔗 **منبع:** TradingView"
            
            # ارسال به تلگرام
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ سیگنال ارسال شد: {combined} برای {ticker}")
            return jsonify({"status": "success", "signal": combined}), 200
        
        logger.info(f"⏭️ سیگنال ترکیبی ایجاد نشد. Lorentzian: {lorentzian_signal}, RSI: {rsi_value}")
        return jsonify({"status": "skipped"}), 200
        
    except Exception as e:
        logger.error(f"❌ خطا: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== صفحه تست ====================
@app.route('/test', methods=['GET'])
def test_bot():
    """تست ربات"""
    try:
        message = "🤖 **ربات فعال است!**\n\nاین یک پیام تست از سرور است."
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        return jsonify({"status": "test_sent"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """بررسی سلامت"""
    return jsonify({"status": "active", "service": "TradingView Telegram Bot"}), 200

# ==================== صفحه اصلی ====================
@app.route('/')
def home():
    return """
    <h1>🤖 ربات TradingView-تلگرام</h1>
    <p>ربات فعال است! آدرس‌های موجود:</p>
    <ul>
        <li><a href="/health">/health</a> - بررسی سلامت</li>
        <li><a href="/test">/test</a> - تست ربات تلگرام</li>
        <li><strong>/webhook</strong> - دریافت سیگنال از TradingView (POST)</li>
    </ul>
    <p>برای تنظیم TradingView، آدرس: <code>https://آدرس-شما.onrender.com/webhook</code></p>
    """

# ==================== اجرا ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
