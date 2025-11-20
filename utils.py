# utils.py - Utility Functions
from datetime import datetime
from typing import List, Dict
from config import SIGNAL_MESSAGE_TEMPLATE, TP_MESSAGE_TEMPLATE, DAILY_SUMMARY_TEMPLATE

def format_signal_message(signal_number: int, coin: str, direction: str,
                          entry: float, take_profits: List[float],
                          stop_loss: float, rr_ratio: float, sent_by: str = "AI Bot") -> str:
    """Format trading signal message"""
    
    # Format take profits
    tp_str = ", ".join([f"{tp:.4f}" for tp in take_profits])
    
    message = f"""🤖 Tín hiệu {signal_number}
#{coin.replace('USDT', '')} – {direction} 📌

🟢 Entry: {entry:.4f}
🆗 Take Profit: {tp_str}
🙅‍♂️ Stop-Loss: {stop_loss:.4f}
🪙 Tỉ lệ RR: {rr_ratio:.2f}:1

🧠 By {sent_by}

⚠️ Nhất định phải tuân thủ quản lý rủi ro – Đi tối đa 1-2% risk, Bot chỉ để tham khảo, win 3 lệnh nên ngưng"""
    
    return message

def format_tp_message(signal_number: int, coin: str, profit_percent: float) -> str:
    """Format take profit hit message"""
    
    message = f"""🎉🎉🎉 Tín hiệu thứ {signal_number} đã chạm TP 🎉🎉🎉
#{coin.replace('USDT', '')} +{profit_percent:.2f}% 🕯🔼"""
    
    return message

def format_daily_summary(stats: Dict) -> str:
    """Format daily summary message"""
    
    today = datetime.now().strftime('%d/%m/%Y')
    
    # Calculate success rate
    completed = stats['wins'] + stats['losses']
    success_rate = (stats['wins'] / completed * 100) if completed > 0 else 0
    
    # Determine if profitable
    profitable = "✅ CÓ" if stats['total_profit'] > 0 else "❌ KHÔNG"
    
    message = f"""📊 TỔNG KẾT NGÀY {today}

📈 Tổng tín hiệu: {stats['total_signals']}
✅ Thắng: {stats['wins']} ({stats['win_rate']:.1f}%)
❌ Thua: {stats['losses']}
💰 Tổng lợi nhuận: {stats['total_profit']:.2f}%
📊 Lợi nhuận trung bình: {stats['avg_profit']:.2f}%

🎯 Tỷ lệ thành công: {success_rate:.1f}%
💵 Có lãi: {profitable}

---
⚡ Cảm ơn bạn đã tin tưởng AI Trading Bot!
👑 @HOANGDUNGG789"""
    
    return message

def format_number(number: float, decimals: int = 4) -> str:
    """Format number with specified decimals"""
    return f"{number:.{decimals}f}"

def calculate_position_size(account_balance: float, risk_percent: float,
                            entry: float, stop_loss: float) -> float:
    """Calculate position size based on risk management"""
    risk_amount = account_balance * (risk_percent / 100)
    price_diff = abs(entry - stop_loss)
    
    if price_diff > 0:
        position_size = risk_amount / price_diff
        return round(position_size, 6)
    
    return 0.0

def format_time_ago(timestamp: str) -> str:
    """Format timestamp to 'time ago' string"""
    try:
        dt = datetime.fromisoformat(timestamp)
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)} giây trước"
        elif seconds < 3600:
            return f"{int(seconds / 60)} phút trước"
        elif seconds < 86400:
            return f"{int(seconds / 3600)} giờ trước"
        else:
            return f"{int(seconds / 86400)} ngày trước"
    except:
        return "Unknown"

def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format"""
    # Basic validation: should end with USDT and be uppercase
    if not symbol:
        return False
    
    if not symbol.endswith('USDT'):
        return False
    
    if not symbol.isupper():
        return False
    
    if len(symbol) < 6:  # Minimum: BTUSDT
        return False
    
    return True

def get_coin_emoji(coin: str) -> str:
    """Get emoji for popular coins"""
    coin_emojis = {
        'BTC': '₿',
        'ETH': 'Ξ',
        'BNB': '🔶',
        'SOL': '◎',
        'XRP': '✕',
        'ADA': '₳',
        'DOGE': '🐕',
        'MATIC': '🔷',
        'DOT': '●',
        'AVAX': '🔺'
    }
    
    coin_name = coin.replace('USDT', '')
    return coin_emojis.get(coin_name, '💎')
