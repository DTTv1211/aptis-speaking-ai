# Aptis Speaking AI Practice — Streamlit

Ứng dụng luyện Aptis Speaking với bộ câu hỏi được đồng bộ từ
[DTTv1211/aptis-speaking-ai](https://github.com/DTTv1211/aptis-speaking-ai).
Ứng dụng hỗ trợ thu âm hoặc nhập transcript, sau đó nhận feedback CEFR-oriented
bằng Gemini.

## Bộ câu hỏi

- Part 1: 44 câu hỏi cá nhân, khoảng 30 giây/câu.
- Part 2: 30 đề, mỗi đề gồm ảnh và 3 câu hỏi.
- Part 3: 49 đề, mỗi đề gồm 1–2 ảnh và 3 câu hỏi.
- Part 4: 34 đề long turn, mỗi đề gồm 3 ý cần trả lời trong một bài liền mạch.

Dữ liệu nằm trong `part1.json`, `part2.json`, `part3.json` và `part4.json`.
Ứng dụng kiểm tra cấu trúc các file này khi khởi động.

## Chạy local

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
# điền GEMINI_API_KEY vào .env
streamlit run app.py
```

## Deploy Streamlit Community Cloud

1. Push repo lên GitHub.
2. Chọn branch `main` và file `app.py` khi tạo app trên Streamlit Cloud.
3. Trong **Advanced settings → Secrets**, thêm:

```toml
GEMINI_API_KEY = "your_actual_api_key"
GEMINI_MODEL = "gemini-2.5-flash"
```

Không commit `.env`, `.streamlit/secrets.toml` hoặc API key.

## Kiểm tra

```powershell
python -m py_compile app.py question_bank.py
```

CEFR và điểm số chỉ là ước lượng phục vụ luyện tập, không phải kết quả chính thức
của British Council.
