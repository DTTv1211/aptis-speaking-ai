# Aptis Speaking Coach

## Chạy ứng dụng

```powershell
python -m pip install -r requirements.txt
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

Điền API key thật vào `.streamlit/secrets.toml`. File này đã được bỏ qua trong
`.gitignore`, không đưa key lên GitHub hoặc đặt trực tiếp trong `app.py`.

## Dùng một tài khoản/project Gemini

Một API key là đủ:

```toml
GEMINI_API_KEY = "your-api-key"
GEMINI_MODEL = "gemini-3.5-flash"
```

Ứng dụng gửi WAV 16 kHz từ backend đến Gemini trong một request để chép lời và
chấm điểm. Dữ liệu ghi âm không được gửi qua tài khoản đăng nhập ở trình duyệt.

Nếu cấu hình nhiều key, cần lưu ý rate limit của Gemini áp dụng theo Google Cloud
project, không áp dụng riêng cho từng key. Hai key cùng project vẫn dùng chung
RPM, TPM và RPD.

## Phân biệt lỗi Gemini

- `429`: chạm rate limit/quota; đợi rồi thử lại. Key ở project khác có thể failover.
- `503`: Gemini/model đang quá tải hoặc tạm thời không khả dụng, không phải hết quota.
  Ứng dụng tự retry với exponential backoff trước khi hiện lỗi.
- `401/403`: key không hợp lệ hoặc project không có quyền dùng model.

Gemini giới hạn tổng request inline ở 20 MB. Ứng dụng dành tối đa 18 MB cho audio
và ảnh để chừa chỗ cho prompt/schema. Bản WAV 16 kHz dài 120 giây thông thường chỉ
khoảng 3.7 MB, nên không còn bị chặn bởi ngưỡng 5 MB cũ.
