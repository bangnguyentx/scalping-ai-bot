module.exports = {
    // Top 10 coin yêu thích để quét
    COINS: [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 
        'ADAUSDT', 'DOGEUSDT', 'TRXUSDT', 'MATICUSDT', 'LTCUSDT'
    ],
    TIMEFRAME: '15m', // Khung thời gian phân tích
    RISK_PERCENT: 1,  // 1% risk
    // Giờ hoạt động (24h format)
    START_HOUR: 5,
    END_HOUR: 21,
    END_MINUTE: 31,
    // Cấu hình RR
    RR_RATIO: 2, // Risk/Reward tối thiểu
};
