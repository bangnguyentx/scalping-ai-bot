# bot.py - Main Bot File
import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import json

from config import TOKEN, ADMIN_ID, TOP_COINS, SCAN_INTERVALS
from analyzer import CryptoAnalyzer
from database import Database
from signal_manager import SignalManager
from utils import format_signal_message, format_tp_message, format_daily_summary

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ScalpingBot:
    def __init__(self):
        self.app = Application.builder().token(TOKEN).build()
        self.db = Database()
        self.analyzer = CryptoAnalyzer()
        self.signal_manager = SignalManager(self.db)
        self.is_scanning = True
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "Unknown"
        
        # Save user to database
        self.db.add_user(user_id, username, user.first_name)
        
        # Check if user is blocked
        if self.db.is_user_blocked(user_id):
            await update.message.reply_text("❌ Bạn đã bị chặn sử dụng bot này.")
            return
        
        # Welcome message
        welcome_message = f"""👋 Chào {user.first_name}!
🧠 AI SCALPING TRADING COINS.

⚡ AI đang trong quá trình phát triển, theo AI tối đa 1% risk.
👑 Bot được tạo bởi Hoàng Dũng: @HOANGDUNGG789

🤖 Bot sẽ tự động gửi tín hiệu khi phát hiện cơ hội giao dịch có độ tin cậy 100%.

📊 Lệnh có sẵn:
/start - Khởi động bot
/stats - Xem thống kê
/help - Trợ giúp"""
        
        await update.message.reply_text(welcome_message)
        
        # Notify admin about new user
        if user_id != ADMIN_ID:
            keyboard = [[
                InlineKeyboardButton("🚫 Chặn người dùng", callback_data=f"block_{user_id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            admin_notification = f"""🆕 Người dùng mới!
👤 Tên: {user.first_name}
🆔 ID: {user_id}
📱 Username: @{username}
⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_notification,
                reply_markup=reply_markup
            )
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        stats = self.db.get_daily_stats()
        
        stats_message = f"""📊 Thống kê hôm nay:
        
✅ Tổng tín hiệu: {stats['total_signals']}
🎯 Thắng: {stats['wins']} ({stats['win_rate']:.1f}%)
❌ Thua: {stats['losses']}
📈 Đang theo dõi: {stats['active_signals']}
💰 Tổng lợi nhuận: {stats['total_profit']:.2f}%"""
        
        await update.message.reply_text(stats_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = """🤖 Hướng dẫn sử dụng bot:

📌 Bot tự động phân tích và gửi tín hiệu
⏰ Quét mỗi 15 phút (1, 16, 31, 46 phút)
🎯 Chỉ gửi tín hiệu có độ tin cậy 100%
📊 Tự động theo dõi Entry, TP, SL

⚠️ Lưu ý quan trọng:
• Chỉ risk tối đa 1-2%
• Win 3 lệnh nên nghỉ
• Bot chỉ để tham khảo
• Luôn có Stop Loss

📞 Liên hệ: @HOANGDUNGG789"""
        
        await update.message.reply_text(help_text)
    
    async def handle_admin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages from admin to broadcast"""
        if update.effective_user.id not in self.db.get_all_admins():
            return
        
        # Get message content
        message = update.message
        users = self.db.get_all_active_users()
        
        success_count = 0
        fail_count = 0
        
        for user_id in users:
            try:
                if message.photo:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=message.photo[-1].file_id,
                        caption=message.caption
                    )
                elif message.text:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message.text
                    )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {user_id}: {e}")
                fail_count += 1
            
            await asyncio.sleep(0.05)  # Avoid rate limit
        
        await update.message.reply_text(
            f"✅ Đã gửi đến {success_count} người dùng\n❌ Thất bại: {fail_count}"
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Bạn không có quyền thực hiện thao tác này.")
            return
        
        data = query.data
        
        if data.startswith("block_"):
            user_id = int(data.split("_")[1])
            self.db.block_user(user_id)
            await query.edit_message_text(f"✅ Đã chặn người dùng {user_id}")
        
        elif data.startswith("unblock_"):
            user_id = int(data.split("_")[1])
            self.db.unblock_user(user_id)
            await query.edit_message_text(f"✅ Đã mở chặn người dùng {user_id}")
        
        elif data.startswith("delete_signal_"):
            signal_id = int(data.split("_")[2])
            # Delete signal logic here
            await query.edit_message_text(f"✅ Đã xóa tín hiệu #{signal_id}")
    
    async def scan_and_send_signals(self, context: ContextTypes.DEFAULT_TYPE):
        """Main scanning function - runs every minute"""
        now = datetime.now()
        minute = now.minute
        
        # Check if it's time to scan (1, 16, 31, 46 minutes)
        scan_minutes = [1, 16, 31, 46]
        
        if minute in scan_minutes and self.is_scanning:
            logger.info(f"Starting coin scan at {now.strftime('%H:%M:%S')}")
            
            for coin in TOP_COINS:
                try:
                    # Skip if coin was analyzed in last 2 hours
                    if self.signal_manager.was_recently_analyzed(coin):
                        continue
                    
                    # Analyze coin
                    analysis = await self.analyzer.analyze_coin(coin)
                    
                    # Check if confidence is 100%
                    if analysis['confidence'] == 100:
                        # Get signal number for today
                        signal_number = self.db.get_today_signal_count() + 1
                        
                        # Save signal to database
                        signal_id = self.db.add_signal(
                            coin=coin,
                            direction=analysis['direction'],
                            entry=analysis['entry'],
                            stop_loss=analysis['stop_loss'],
                            take_profits=analysis['take_profits'],
                            rr_ratio=analysis['rr_ratio']
                        )
                        
                        # Format and send signal to all users
                        signal_msg = format_signal_message(
                            signal_number=signal_number,
                            coin=coin,
                            direction=analysis['direction'],
                            entry=analysis['entry'],
                            take_profits=analysis['take_profits'],
                            stop_loss=analysis['stop_loss'],
                            rr_ratio=analysis['rr_ratio'],
                            sent_by="AI Bot"
                        )
                        
                        # Send to all active users
                        await self.broadcast_message(context, signal_msg)
                        
                        # Mark coin as analyzed
                        self.signal_manager.mark_as_analyzed(coin)
                        
                        logger.info(f"Signal sent for {coin} - Signal #{signal_number}")
                
                except Exception as e:
                    logger.error(f"Error analyzing {coin}: {e}")
                
                await asyncio.sleep(2)  # Small delay between coins
    
    async def monitor_active_signals(self, context: ContextTypes.DEFAULT_TYPE):
        """Monitor active signals every 5 minutes"""
        active_signals = self.db.get_active_signals()
        
        for signal in active_signals:
            try:
                coin = signal['coin']
                current_price = await self.analyzer.get_current_price(coin)
                
                # Check if TP hit
                tp_hit = self.signal_manager.check_take_profit(
                    signal, 
                    current_price
                )
                
                if tp_hit:
                    profit_percent = self.signal_manager.calculate_profit(
                        signal['entry'],
                        current_price,
                        signal['direction']
                    )
                    
                    # Update database
                    self.db.update_signal_status(signal['id'], 'completed', profit_percent)
                    
                    # Send TP notification
                    tp_msg = format_tp_message(
                        signal_number=signal['signal_number'],
                        coin=coin,
                        profit_percent=profit_percent
                    )
                    
                    await self.broadcast_message(context, tp_msg)
                    
                    logger.info(f"TP hit for {coin} - Profit: {profit_percent:.2f}%")
                
                # Check if SL hit
                elif self.signal_manager.check_stop_loss(signal, current_price):
                    loss_percent = self.signal_manager.calculate_profit(
                        signal['entry'],
                        current_price,
                        signal['direction']
                    )
                    
                    # Update database
                    self.db.update_signal_status(signal['id'], 'stopped', loss_percent)
                    
                    logger.info(f"SL hit for {coin} - Loss: {loss_percent:.2f}%")
            
            except Exception as e:
                logger.error(f"Error monitoring signal {signal['id']}: {e}")
    
    async def send_daily_summary(self, context: ContextTypes.DEFAULT_TYPE):
        """Send daily summary at 11 PM"""
        now = datetime.now()
        
        if now.hour == 23 and now.minute == 0:
            stats = self.db.get_daily_stats()
            summary_msg = format_daily_summary(stats)
            
            await self.broadcast_message(context, summary_msg)
            logger.info("Daily summary sent")
    
    async def broadcast_message(self, context: ContextTypes.DEFAULT_TYPE, message: str):
        """Broadcast message to all active users"""
        users = self.db.get_all_active_users()
        
        for user_id in users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Failed to send to {user_id}: {e}")
    
    async def scheduled_tasks(self, context: ContextTypes.DEFAULT_TYPE):
        """Run all scheduled tasks"""
        while True:
            try:
                # Scan for signals (every minute, but only scans at specific minutes)
                await self.scan_and_send_signals(context)
                
                # Monitor active signals (every 5 minutes)
                if datetime.now().minute % 5 == 0:
                    await self.monitor_active_signals(context)
                
                # Send daily summary
                await self.send_daily_summary(context)
                
            except Exception as e:
                logger.error(f"Error in scheduled tasks: {e}")
            
            # Wait 60 seconds before next check
            await asyncio.sleep(60)
    
    def run(self):
        """Run the bot"""
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("stats", self.stats))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & filters.User(user_id=self.db.get_all_admins()),
                self.handle_admin_message
            )
        )
        self.app.add_handler(
            MessageHandler(
                filters.PHOTO & filters.User(user_id=self.db.get_all_admins()),
                self.handle_admin_message
            )
        )
        
        # Start scheduled tasks
        self.app.job_queue.run_once(self.scheduled_tasks, 0)
        
        logger.info("Bot started successfully!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = ScalpingBot()
    bot.run()
