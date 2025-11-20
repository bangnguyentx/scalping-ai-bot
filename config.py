# config.py - Configuration settings
import os

# Bot credentials
TOKEN = os.getenv("BOT_TOKEN", "8458092977:AAHO8gb6nvtTVus573iQcHkw2SC1xgTaNmY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7760459637"))

# Top 10 favorite coins to analyze
TOP_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "MATICUSDT",
    "DOTUSDT",
    "AVAXUSDT"
]

# Scan intervals (minutes in hour)
SCAN_INTERVALS = [1, 16, 31, 46]

# Analysis timeframes
TIMEFRAMES = {
    '15m': {'weight': 1.0, 'limit': 100},
    '1h': {'weight': 1.2, 'limit': 100},
    '4h': {'weight': 1.5, 'limit': 100}
}

# Trading parameters
MIN_CONFIDENCE = 100  # Only send signals with 100% confidence
RISK_PERCENT = 1.0  # Maximum 1% risk per trade
MIN_RR_RATIO = 1.5  # Minimum Risk/Reward ratio

# Signal monitoring
MONITORING_INTERVAL = 5  # Check active signals every 5 minutes (in minutes)
ANALYSIS_COOLDOWN = 120  # Don't analyze same coin for 2 hours (in minutes)

# Daily summary
SUMMARY_HOUR = 23  # Send daily summary at 11 PM
SUMMARY_MINUTE = 0

# Database settings
DATABASE_FILE = "trading_bot.db"

# Binance API endpoints
BINANCE_API_BASE = "https://fapi.binance.com/fapi/v1"
BINANCE_ENDPOINTS = {
    'klines': f"{BINANCE_API_BASE}/klines",
    'ticker': f"{BINANCE_API_BASE}/ticker/24hr",
    'price': f"{BINANCE_API_BASE}/ticker/price",
    'depth': f"{BINANCE_API_BASE}/depth"
}

# Take profit levels (percentages from entry)
TP_LEVELS = {
    'TP1': 0.01,  # 1%
    'TP2': 0.025, # 2.5%
    'TP3': 0.045, # 4.5%
    'TP4': 0.10   # 10%
}

# Stop loss percentage
SL_PERCENT = 0.05  # 5% stop loss

# Volume analysis thresholds
VOLUME_SPIKE_THRESHOLD = 1.5  # 1.5x average volume
MIN_VOLUME_RATIO = 0.8  # Minimum volume compared to average

# Market structure thresholds
STRUCTURE_CONFIDENCE_THRESHOLD = 75
TREND_STRENGTH_THRESHOLD = 60

# Message templates
WELCOME_MESSAGE_TEMPLATE = """👋 Chào {name}!
🧠 AI SCALPING TRADING COINS.

⚡ AI đang trong quá trình phát triển, theo AI tối đa 1% risk.
👑 Bot được tạo bởi Hoàng Dũng: @HOANGDUNGG789"""

SIGNAL_MESSAGE_TEMPLATE = """🤖 Tín hiệu {signal_number}
#{coin} – {direction} 📌

🟢 Entry: {entry}
🆗 Take Profit: {tp1}, {tp2}, {tp3}, {tp4}
🙅‍♂️ Stop-Loss: {stop_loss}
🪙 Tỉ lệ RR: {rr_ratio}

🧠 By {sent_by}

⚠️ Nhất định phải tuân thủ quản lý rủi ro – Đi tối đa 1-2% risk, Bot chỉ để tham khảo, win 3 lệnh nên ngưng"""

TP_MESSAGE_TEMPLATE = """🎉🎉🎉 Tín hiệu thứ {signal_number} đã chạm TP 🎉🎉🎉
#{coin} +{profit_percent}% 🕯🔼"""

DAILY_SUMMARY_TEMPLATE = """📊 TỔNG KẾT NGÀY {date}

📈 Tổng tín hiệu: {total_signals}
✅ Thắng: {wins} ({win_rate}%)
❌ Thua: {losses}
💰 Tổng lợi nhuận: {total_profit}%
📊 Lợi nhuận trung bình: {avg_profit}%

🎯 Tỷ lệ thành công: {success_rate}%"""
