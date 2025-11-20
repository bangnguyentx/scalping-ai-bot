const TelegramBot = require('node-telegram-bot-api');
require('dotenv').config();
const db = require('./database');

const bot = new TelegramBot(process.env.TELEGRAM_TOKEN, { polling: true });

// Hàm gửi tin nhắn broadcast
const broadcastMessage = (msg) => {
    db.users.forEach(chatId => {
        if (!db.blockedUsers.includes(chatId)) {
            bot.sendMessage(chatId, msg, { parse_mode: 'HTML' }).catch(err => console.log(`Lỗi gửi tới ${chatId}`));
        }
    });
};

// Xử lý lệnh /start
bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    const username = msg.from.username ? `@${msg.from.username}` : msg.from.first_name;

    // Lưu user nếu chưa tồn tại
    if (!db.users.includes(chatId)) {
        db.users.push(chatId);
        
        // Thông báo cho Admin
        bot.sendMessage(db.SUPER_ADMIN, `🔔 <b>User mới:</b> ${username} (ID: ${chatId})\n/block_${chatId} để chặn.`, { parse_mode: 'HTML' });
    }

    if (db.blockedUsers.includes(chatId)) return;

    const welcomeMsg = `👋 Chào ${username}!\n🧠 <b>AI SCALPING TRADING COINS.</b>\n\n⚡AI đang trong quá trình phát triển, theo AI tối đa 1% risk.\n👑 Bot được tạo bởi Hoàng Dũng: @HOANGDUNGG789`;
    bot.sendMessage(chatId, welcomeMsg, { parse_mode: 'HTML' });
});

// Xử lý các lệnh Admin
bot.on('message', (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;
    
    // Kiểm tra quyền Admin
    if (!db.admins.includes(chatId)) return;

    // 1. Block User: /block_123456
    if (text && text.startsWith('/block_')) {
        const userIdToBlock = parseInt(text.split('_')[1]);
        if (!db.blockedUsers.includes(userIdToBlock)) {
            db.blockedUsers.push(userIdToBlock);
            bot.sendMessage(chatId, `🚫 Đã chặn user ${userIdToBlock}`);
        }
    }

    // 2. Broadcast: Gửi tin nhắn bắt đầu bằng "SENDALL:"
    if (text && text.startsWith('SENDALL:')) {
        const content = text.replace('SENDALL:', '').trim();
        broadcastMessage(content);
        bot.sendMessage(chatId, '✅ Đã gửi thông báo tới tất cả users.');
    }

    // 3. Thêm Admin: /addadmin_123456
    if (text && text.startsWith('/addadmin_')) {
        const newAdminId = parseInt(text.split('_')[1]);
        if (!db.admins.includes(newAdminId)) {
            db.admins.push(newAdminId);
            bot.sendMessage(chatId, `👮‍♂️ Đã thêm admin ${newAdminId}`);
        }
    }
    
    // 3. Xóa Admin: /deladmin_123456
    if (text && text.startsWith('/deladmin_')) {
        const delId = parseInt(text.split('_')[1]);
        if (delId == db.SUPER_ADMIN) {
            bot.sendMessage(chatId, '❌ Không thể xóa Super Admin.');
        } else {
            db.admins = db.admins.filter(id => id !== delId);
            bot.sendMessage(chatId, `🗑 Đã xóa quyền admin của ${delId}`);
        }
    }
});

module.exports = { bot, broadcastMessage };
