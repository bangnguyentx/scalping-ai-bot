# 🤖 Scalping AI Trading Bot

Bot Telegram tự động phân tích và gửi tín hiệu giao dịch crypto với độ tin cậy 100%.

## 🌟 Tính năng

- ✅ Tự động phân tích 10 coin phổ biến mỗi 15 phút
- 🎯 Chỉ gửi tín hiệu khi có độ tin cậy 100%
- 📊 Tự động theo dõi Entry, Take Profit, Stop Loss
- 📈 Thống kê hàng ngày
- 👑 Quản lý admin đa cấp
- 📢 Broadcast tin nhắn/hình ảnh đến tất cả users

## 📁 Cấu trúc File

```
scalping-bot/
├── bot.py              # File chính của bot
├── config.py           # Cấu hình
├── analyzer.py         # Engine phân tích coin
├── database.py         # Quản lý database
├── signal_manager.py   # Quản lý tín hiệu
├── utils.py            # Các hàm tiện ích
├── requirements.txt    # Dependencies
├── Dockerfile          # Docker configuration
└── README.md           # Documentation
```

## 🚀 Cài đặt

### Yêu cầu
- Python 3.11+
- Telegram Bot Token
- Admin Telegram ID

### Bước 1: Clone Repository

```bash
git clone https://github.com/yourusername/scalping-bot.git
cd scalping-bot
```

### Bước 2: Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình

Tạo file `.env` hoặc sửa `config.py`:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id
```

### Bước 4: Chạy Bot

```bash
python bot.py
```

## 🐳 Deploy với Docker

```bash
docker build -t scalping-bot .
docker run -d --name scalping-bot \
  -e BOT_TOKEN=your_token \
  -e ADMIN_ID=your_id \
  scalping-bot
```

## ☁️ Deploy trên Render.com

1. Push code lên GitHub
2. Tạo Web Service mới trên Render
3. Connect với GitHub repository
4. Cấu hình:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Thêm Environment Variables:
   - `BOT_TOKEN`: Token của bot
   - `ADMIN_ID`: ID Telegram của admin

## 📊 Cách hoạt động

### Phân tích tự động
- Bot quét 10 coin phổ biến mỗi 15 phút (phút 1, 16, 31, 46)
- Phân tích đa khung thời gian (15m, 1h, 4h)
- Tính toán độ tin cậy dựa trên:
  - Xu hướng giá
  - Phân tích volume
  - Mức hỗ trợ/kháng cự
  - Đồng bộ giữa các khung thời gian

### Gửi tín hiệu
- Chỉ gửi khi độ tin cậy = 100%
- Tự động tính Entry, SL, TP
- Tỷ lệ RR tối thiểu 1.5:1
- Cooldown 2 giờ cho mỗi coin sau khi phân tích

### Theo dõi tín hiệu
- Quét mỗi 5 phút để kiểm tra Entry/TP/SL
- Tự động thông báo khi chạm TP
- Cập nhật trạng thái tín hiệu
- Tính toán % lãi/lỗ

### Tổng kết hàng ngày
- Gửi lúc 23:00 mỗi ngày
- Thống kê win/loss
- Tổng lợi nhuận
- Tỷ lệ thành công

## 👤 Lệnh cho User

- `/start` - Khởi động bot
- `/stats` - Xem thống kê
- `/help` - Trợ giúp

## 👑 Chức năng Admin

1. **Broadcast**: Gửi tin nhắn/hình ảnh đến tất cả users
2. **Quản lý user**: Chặn/mở chặn người dùng
3. **Quản lý admin**: Thêm/xóa admin
4. **Xóa tín hiệu**: Xóa tín hiệu đã gửi

## ⚙️ Cấu hình

Sửa file `config.py` để thay đổi:

- Danh sách coin phân tích
- Khoảng thời gian quét
- Độ tin cậy tối thiểu
- Các ngưỡng phân tích
- Tỷ lệ TP/SL

## 📝 Lưu ý

- Bot chỉ để tham khảo
- Luôn có quản lý rủi ro (1-2% risk)
- Win 3 lệnh nên nghỉ
- Không sử dụng đòn bẩy quá cao

## 🐛 Troubleshooting

### Bot không khởi động
- Kiểm tra Token và Admin ID
- Xem logs để tìm lỗi

### Không nhận tín hiệu
- Kiểm tra đã /start chưa
- Xem có bị block không

### Database lỗi
- Xóa file `trading_bot.db` và khởi động lại

## 📞 Liên hệ

- Telegram: [@HOANGDUNGG789](https://t.me/HOANGDUNGG789)
- Email: support@example.com

## 📄 License

MIT License - Tự do sử dụng và chỉnh sửa

---

Made with ❤️ by Hoàng Dũng
