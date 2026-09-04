# Aptis Speaking Coach

## Chạy ứng dụng

```powershell
python -m pip install -r requirements.txt
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

Điền API key thật vào `.streamlit/secrets.toml`. File này đã được bỏ qua trong
`.gitignore`, không đưa key lên GitHub hoặc đặt trực tiếp trong `app.py`.

## Bộ đề ngẫu nhiên đủ 4 kỹ năng

Chọn **🎲 Tạo bộ đề ngẫu nhiên** trong thanh bên để lấy một lượt luyện hoàn chỉnh:

- Speaking: 3 câu Part 1 và một đề cho mỗi Part 2, 3, 4.
- Listening: một bài ở mỗi Part 1–4.
- Reading: một bài ở mỗi Part 1–4.
- Writing: Part 2, một câu Part 3 và Part 4 của cùng một chủ đề.

Bộ đề được giữ cố định trong phiên để có thể mở từng bài, luyện tập và chấm bằng
các màn hình hiện có. Chỉ nút **Tạo một bộ đề khác** mới bốc lại đề. Việc tạo đề
chạy hoàn toàn từ ngân hàng cục bộ, không gọi Gemini và không tốn quota.

## Dùng một tài khoản/project Gemini

Một API key là đủ:

```toml
GEMINI_API_KEY = "your-api-key"
```

Ứng dụng gửi WAV 16 kHz từ backend đến Gemini trong một request để chép lời và
chấm điểm bằng model cố định `gemini-3.5-flash-lite`. Dữ liệu ghi âm không được
gửi qua tài khoản đăng nhập ở trình duyệt.

## Tối ưu tốc độ và chất lượng

- Speaking và Writing đều chỉ dùng **một request Gemini cho mỗi lần chấm
  thành công**. Retry chỉ phát sinh khi Gemini trả lỗi 408/429/5xx.
- Gemini client và HTTP client được cache theo process để tái sử dụng kết nối,
  không tạo lại TLS connection sau mỗi lần Streamlit rerun.
- Gemini 3.x dùng `thinking_level=LOW`: nhanh hơn mức mặc định nhưng vẫn đủ
  suy luận cho chép lời, chấm Aptis và sửa bài. Không ép `temperature` hoặc
  `candidate_count`; quy tắc chấm và JSON schema giữ đầu ra ổn định.
- JSON đề thi, ảnh từ xa và các gợi ý cục bộ được cache. Bản WAV cũ không
  bị decode/hash lại khi người học chỉ thao tác trên giao diện.
- Phiên bản dependency được khóa trong `requirements.txt` để deploy có hành vi
  nhất quán. Kết quả hiển thị cả số request và thời gian xử lý thực tế.

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

## Đưa ảnh lên Streamlit Community Cloud

Streamlit Cloud lấy file trực tiếp từ GitHub, vì vậy ảnh cũng phải được commit
trong cùng repository. Tải ba file sau lên thư mục `assets/mock_exam/`:

```text
assets/mock_exam/image1.png
assets/mock_exam/image2.png
assets/mock_exam/image3.png
```

Trên GitHub: mở repository → vào `assets/mock_exam` → **Add file** →
**Upload files** → kéo ba ảnh vào → **Commit changes**. Streamlit Cloud sẽ tự
phát hiện commit và cập nhật app. Nếu chưa thấy thay đổi, vào **Manage app** và
chọn **Reboot app**.

Không tải `.streamlit/secrets.toml` hoặc API key lên GitHub.
