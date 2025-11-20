const http = require('http'); // Thêm thư viện tạo server ảo
const moment = require('moment-timezone');
const config = require('./config');
const { analyzeCoin } = require('./analysis');
const db = require('./database');
const { bot, broadcastMessage } = require('./bot');
const { getCandles } = require('./analysis');

// --- PHẦN MỚI THÊM: TẠO SERVER ẢO ĐỂ RENDER KHÔNG BÁO LỖI ---
const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Bot Scalping AI is running!');
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server ảo đang chạy trên cổng ${PORT}...`);
});
// -----------------------------------------------------------

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
    
    for (let i = db.watchList.length - 1; i >= 0; i--) {
        const trade = db.watchList[i];
        if (trade.status !== 'OPEN') continue;

        const candles = await getCandles(trade.symbol, '1m', 1);
        if (!candles.length) continue;
        const currentPrice = candles[candles.length - 1].close;

        let resultMsg = null;
        let profitPercent = 0;

        if (trade.type === 'LONG') {
            if (currentPrice <= trade.sl) {
                trade.status = 'LOSS';
                db.dailyStats.losses++;
            }
            else if (currentPrice >= trade.tp[0]) {
                trade.status = 'WIN';
                profitPercent = ((currentPrice - trade.entry) / trade.entry) * 100;
                resultMsg = `🎉🎉🎉 Tín hiệu thứ ${trade.signalId} đã chạm TP 🎉🎉🎉\n#${trade.symbol.replace('USDT', '')} +${profitPercent.toFixed(2)}% 🕯🔼`;
            }
        }
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

        if (trade.status === 'WIN' && resultMsg) {
            broadcastMessage(resultMsg);
            db.dailyStats.wins++;
            db.watchList.splice(i, 1); 
        }
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
        db.dailyStats = { totalSignals: 0, wins: 0, losses: 0, profitPercent: 0 };
        db.watchList = []; 
    }
}

// --- LÊN LỊCH CHẠY ---
setInterval(() => {
    const now = moment().tz('Asia/Ho_Chi_Minh');
    const min = now.minute();

    // Quét thị trường
    if ([1, 16, 31, 46].includes(min)) {
        scanMarket();
    }

    // Theo dõi lệnh
    if (min % 5 === 0) {
        trackActiveTrades();
    }

    // Tổng kết ngày
    if (now.hour() === 23 && min === 0) {
        dailyReport();
    }

}, 60000);
