// File: database.js

// Lưu trữ trong bộ nhớ (RAM)
// Lưu ý: Khi server khởi động lại, dữ liệu này sẽ mất nếu không dùng Database thật (MongoDB).
// Nhưng để bot chạy được ngay thì dùng cách này.

let users = []; // Danh sách user ID đã ấn start
let blockedUsers = []; // Danh sách bị chặn
let admins = []; // Danh sách admin phụ
let watchList = []; // Danh sách coin đang theo dõi
let dailyStats = {
    totalSignals: 0,
    wins: 0,
    losses: 0,
    profitPercent: 0
};

// Lấy ID Admin từ biến môi trường hoặc để trống nếu chưa có
const SUPER_ADMIN = process.env.ADMIN_ID || 7760459637; 
admins.push(parseInt(SUPER_ADMIN));

module.exports = {
    users, 
    blockedUsers, 
    admins, 
    watchList, 
    dailyStats, 
    SUPER_ADMIN
};
