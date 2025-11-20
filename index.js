const moment = require('moment-timezone');
const config = require('./config');
const { analyzeCoin } = require('./analysis');
const db = require('./database');
const { bot, broadcastMessage } = require('./bot');
const { getCandles } = require('./analysis'); // Lấy giá hiện tại để track

console.log('🚀 Bot Scalping AI Trading đang chạy...');

// --- HÀM GỬI TÍN HIỆU ---
function sendSignal(data) {
    db.dailyStats.totalSignals++;
    const signalIndex = db.dailyStats.totalSignals;
    
    // Tính RR hiển thị
    const rr = Math.abs((data.tp[3] - data.entry) / (data.entry - data.sl)).toFixed(2);
    const typeIcon = data.signal === 'LONG' ? '🟢' : '🔴';
    
    const msg = `🤖 <b>Tín hiệu thứ ${signalIndex} trong ngày</b>
#${data.symbol.replace('USDT', '')} – ${data.signal} 📌

${typeIcon} Entry: ${data.entry.toFixed(4)}
🆗 Take Profit: ${data.tp.map(p => p.toFixed(4)).join(', ')}
🙅‍♂️ Stop-Loss: ${data.sl.toFixed(4)}
🪙 Tỉ lệ RR: 1:${rr}

🧠 By Bot AI Scalping

<i>Nhất định phải tuân thủ quản lý rủi ro – Đi tối đa 1-2% risk, Bot chỉ để tham khảo, win 3 lệnh nên ngưng</i>`;

    broadcastMessage(msg);

    // Thêm vào danh sách theo dõi (Watchlist)
    db.watchList.push({
        symbol: data.symbol,
        signalId: signalIndex,
        type: data.signal,
        entry: data.entry,
        sl: data.sl,
        tp: data.tp, // Array 4 TP
        cooldown: moment().add(2, 'hours'), // Không quét lại trong 2h
        startTime: moment(),
        status: 'OPEN'
    });
}

// --- HÀM QUÉT COIN (15 Phút/lần) ---
async function scanMarket() {
    const now = moment().tz('Asia/Ho_Chi_Minh');
    const hour = now.hour();
    const minute = now.minute();

    // Kiểm tra thời gian hoạt động (5h - 21h31)
    if (hour < config.START_HOUR || (hour > config.END_HOUR && minute > 31)) return;

    console.log(`🔍 Đang quét thị trường lúc ${now.format('HH:mm')}...`);

    for (const coin of config.COINS) {
        // Kiểm tra xem coin này có đang bị cooldown (trong 2h sau tín hiệu) không
        const isCooldown = db.watchList.find(w => w.symbol === coin && moment().isBefore(w.cooldown));
        if (isCooldown) continue;

        const analysis = await analyzeCoin(coin);
        
        if (analysis && analysis.score === 100) {
            console.log(`✅ Tìm thấy tín hiệu: ${coin}`);
            sendSignal(analysis);
        }
    }
}

// --- HÀM THEO DÕI LỆNH (5 Phút/lần) ---
async function trackActiveTrades() {
    if (db.watchList.length === 0) return;

    console.log(`👀 Đang theo dõi ${db.watchList.length} lệnh...`);
    
    // Duyệt ngược để có thể xóa phần tử an toàn
    for (let i = db.watchList.length - 1; i >= 0; i--) {
        const trade = db.watchList[i];
        if (trade.status !== 'OPEN') continue;

        // Lấy giá hiện tại
        const candles = await getCandles(trade.symbol, '1m', 1);
        if (!candles.length) continue;
        const currentPrice = candles[candles.length - 1].close;

        let resultMsg = null;
        let profitPercent = 0;

        // Kiểm tra LONG
        if (trade.type === 'LONG') {
            // Chạm SL
            if (currentPrice <= trade.sl) {
                trade.status = 'LOSS';
                db.dailyStats.losses++;
                // Có thể gửi thông báo thua nếu muốn, nhưng yêu cầu chỉ ghi thông báo thắng
            }
            // Chạm TP (Kiểm tra từng mốc)
            else if (currentPrice >= trade.tp[0]) {
                trade.status = 'WIN'; // Đánh dấu đã thắng ít nhất TP1
                profitPercent = ((currentPrice - trade.entry) / trade.entry) * 100;
                resultMsg = `🎉🎉🎉 Tín hiệu thứ ${trade.signalId} đã chạm TP 🎉🎉🎉\n#${trade.symbol.replace('USDT', '')} +${profitPercent.toFixed(2)}% 🕯🔼`;
            }
        }
        // Kiểm tra SHORT
        else if (trade.type === 'SHORT') {
            if (currentPrice >= trade.sl) {
                trade.status = 'LOSS';
                db.dailyStats.losses++;
            }
            else if (currentPrice <= trade.tp[0]) {
                trade.status = 'WIN';
                profitPercent = ((trade.entry - currentPrice) / trade.entry) * 100;
                resultMsg = `🎉🎉🎉 Tín hiệu thứ ${trade.signalId} đã chạm TP 🎉🎉🎉\n#${trade.symbol.replace('USDT', '')} +${profitPercent.toFixed(2)}% 🕯🔽`;
            }
        }

        // Nếu thắng và chưa thông báo (hoặc thông báo cập nhật TP cao hơn - ở đây làm đơn giản là chạm TP1 là báo và xóa theo dõi)
        if (trade.status === 'WIN' && resultMsg) {
            broadcastMessage(resultMsg);
            db.dailyStats.wins++;
            // Xóa khỏi watchlist sau khi thắng để tránh spam (hoặc giữ lại để track TP2, TP3 tùy logic nâng cao)
            db.watchList.splice(i, 1); 
        }
        // Nếu thua xóa luôn
        if (trade.status === 'LOSS') {
            db.watchList.splice(i, 1);
        }
    }
}

// --- HÀM TỔNG KẾT NGÀY (23:00) ---
function dailyReport() {
    const now = moment().tz('Asia/Ho_Chi_Minh');
    if (now.hour() === 23 && now.minute() === 0) {
        const msg = `📊 <b>TỔNG KẾT NGÀY ${now.format('DD/MM/YYYY')}</b>
--------------
📢 Tổng tín hiệu: ${db.dailyStats.totalSignals}
✅ Thắng: ${db.dailyStats.wins}
❌ Thua: ${db.dailyStats.losses}
📈 Kết quả: ${db.dailyStats.wins >= db.dailyStats.losses ? 'Có lãi 🔥' : 'Lỗ nhẹ ❄️'}

<i>AI Scalping Trading chúc bạn ngủ ngon!</i>`;
        
        broadcastMessage(msg);
        
        // Reset stats cho ngày mới
        db.dailyStats = { totalSignals: 0, wins: 0, losses: 0, profitPercent: 0 };
        db.watchList = []; // Clear lệnh treo (tùy chọn)
    }
}

// --- LÊN LỊCH CHẠY (SCHEDULER) ---
// Kiểm tra mỗi phút
setInterval(() => {
    const now = moment().tz('Asia/Ho_Chi_Minh');
    const min = now.minute();

    // Logic quét: 7h01, 7h16, 7h31, 7h46... (Theo yêu cầu là 15p + 1)
    // Các phút cần quét: 1, 16, 31, 46
    if ([1, 16, 31, 46].includes(min)) {
        scanMarket();
    }

    // Logic theo dõi watchlist: 5 phút/lần
    // Các phút chia hết cho 5: 0, 5, 10, 15...
    if (min % 5 === 0) {
        trackActiveTrades();
    }

    // Tổng kết ngày lúc 23:00
    if (now.hour() === 23 && min === 0) {
        dailyReport();
    }

}, 60000); // Chạy mỗi 60s

