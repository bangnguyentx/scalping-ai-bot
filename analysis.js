const axios = require('axios');
const { RSI, EMA } = require('technicalindicators');

const BINANCE_API = 'https://fapi.binance.com/fapi/v1';

async function getCandles(symbol, interval, limit = 100) {
    try {
        const response = await axios.get(`${BINANCE_API}/klines`, {
            params: { symbol, interval, limit }
        });
        // Convert data Binance
        return response.data.map(c => ({
            open: parseFloat(c[1]),
            high: parseFloat(c[2]),
            low: parseFloat(c[3]),
            close: parseFloat(c[4]),
            volume: parseFloat(c[5]),
            time: c[0]
        }));
    } catch (error) {
        console.error(`Lỗi lấy data ${symbol}:`, error.message);
        return [];
    }
}

async function analyzeCoin(symbol) {
    const candles = await getCandles(symbol, '15m', 100);
    if (candles.length < 50) return null;

    const closes = candles.map(c => c.close);
    const currentPrice = closes[closes.length - 1];

    // 1. Tính RSI (14)
    const rsiInput = { values: closes, period: 14 };
    const rsiValues = RSI.calculate(rsiInput);
    const currentRSI = rsiValues[rsiValues.length - 1];

    // 2. Tính EMA (50) và EMA (200) để xác định xu hướng
    const ema50 = EMA.calculate({ period: 50, values: closes }).pop();
    const ema200 = EMA.calculate({ period: 200, values: closes }).pop();

    // 3. Logic Confidence Score (Giả lập logic AI)
    let score = 0;
    let signal = null; // 'LONG' or 'SHORT'

    // Logic LONG: Giá > EMA 200 (Uptrend) và RSI bị bán quá mức (<35) hoặc phân kỳ
    if (currentPrice > ema200 && currentRSI < 35) {
        score = 100; // Điều kiện tuyệt đối
        signal = 'LONG';
    }
    // Logic SHORT: Giá < EMA 200 (Downtrend) và RSI mua quá mức (>65)
    else if (currentPrice < ema200 && currentRSI > 65) {
        score = 100; // Điều kiện tuyệt đối
        signal = 'SHORT';
    } else {
        // Các trường hợp khác điểm thấp hơn
        score = 50; 
    }

    if (score === 100 && signal) {
        // Tính toán Entry, SL, TP
        const atrRaw = candles.slice(-14).reduce((sum, c) => sum + (c.high - c.low), 0) / 14; // Simple ATR simulation
        
        let entry = currentPrice;
        let sl, tp1, tp2, tp3, tp4;

        if (signal === 'LONG') {
            sl = entry - (atrRaw * 1.5); // SL dựa trên biến động
            const risk = entry - sl;
            tp1 = entry + risk;
            tp2 = entry + (risk * 1.5);
            tp3 = entry + (risk * 2);
            tp4 = entry + (risk * 3);
        } else {
            sl = entry + (atrRaw * 1.5);
            const risk = sl - entry;
            tp1 = entry - risk;
            tp2 = entry - (risk * 1.5);
            tp3 = entry - (risk * 2);
            tp4 = entry - (risk * 3);
        }

        return {
            symbol,
            score,
            signal,
            entry,
            sl,
            tp: [tp1, tp2, tp3, tp4],
            price: currentPrice
        };
    }

    return { symbol, score: score || 0 };
}

module.exports = { analyzeCoin, getCandles };
