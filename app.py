import streamlit as st
import json
import tempfile
import os
from audio_recorder_streamlit import audio_recorder
from google import genai
from google.genai import types

# ==============================================================================
# CẤU HÌNH API KEY (Tương thích cả khi chạy cục bộ lẫn Deploy Streamlit Cloud)
# ==============================================================================
# Tự động lấy từ Streamlit Secrets khi deploy web, hoặc biến môi trường/key nội bộ
DEFAULT_KEY = ""  # Có thể dán trực tiếp API key của bạn vào đây nếu chỉ chạy trên máy cá nhân
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", DEFAULT_KEY))

# Cấu hình trang giao diện
st.set_page_config(
    page_title="Luyện thi Speaking Aptis - AI Coach",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tùy biến CSS để giao diện trực quan, rõ ràng
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .question-box {
        background-color: #EFF6FF;
        border-left: 5px solid #2563EB;
        padding: 16px;
        border-radius: 8px;
        font-size: 1.25rem;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 28 câu hỏi Part 1 chuẩn Aptis trích xuất từ đề thi
QUESTIONS = [
    {"id": 1, "topic": "Family", "question": "Please tell me about your family?"},
    {"id": 2, "topic": "Personal Introduction", "question": "Please tell me about yourself?"},
    {"id": 3, "topic": "Hometown & Places", "question": "Tell me about your hometown / the place that you live? / A famous place in your country?"},
    {"id": 4, "topic": "Travel in Country", "question": "Tell me the best way to travel about around your country?"},
    {"id": 5, "topic": "Friend & Family Member", "question": "Tell me about your friend / a member in your family"},
    {"id": 6, "topic": "Weather & Seasons", "question": "What is the weather like today? / What is your favorite season?"},
    {"id": 7, "topic": "Good Memories", "question": "Please tell me about one of your good memories"},
    {"id": 8, "topic": "Activities with Friends", "question": "What do you like doing with your friends?"},
    {"id": 9, "topic": "Free Time Activities", "question": "What do you like doing in your free time?"},
    {"id": 10, "topic": "Past Activities", "question": "What did you do last night / on the weekend?"},
    {"id": 11, "topic": "First School", "question": "Please tell me about your first school?"},
    {"id": 12, "topic": "Current Room", "question": "Describe the room you are in?"},
    {"id": 13, "topic": "Journey Today", "question": "Describe your journey here today?"},
    {"id": 14, "topic": "Clothing & Outfit", "question": "What are you wearing today?"},
    {"id": 15, "topic": "Feeling Tired", "question": "When do you feel tired?"},
    {"id": 16, "topic": "Vietnamese Meal", "question": "Describe a typical Vietnamese meal?"},
    {"id": 17, "topic": "Typical Day", "question": "Describe your typical day?"},
    {"id": 18, "topic": "Free Time Hobbies", "question": "What do you like to do in your free time?"},
    {"id": 19, "topic": "Favorite Places", "question": "Describe your favorite places"},
    {"id": 20, "topic": "Conversation with Mother", "question": "Tell me about the last time you talked with your mother"},
    {"id": 21, "topic": "Sports in Country", "question": "People like sport in your country"},
    {"id": 22, "topic": "New House", "question": "What are you looking for in your new house?"},
    {"id": 23, "topic": "Learning English", "question": "Why are you learning English?"},
    {"id": 24, "topic": "Work & Profession", "question": "Describe your job"},
    {"id": 25, "topic": "Food & Cuisine", "question": "What is the food like in your country?"},
    {"id": 26, "topic": "Stress & Pressure", "question": "When do you feel stressed?"},
    {"id": 27, "topic": "Travel Interests", "question": "Tell me why you are interested in travel?"},
    {"id": 28, "topic": "Favorite Books", "question": "Favorite book in your country?"}
]

# Prompt CEFR chuẩn Aptis Speaking
APTIS_SYSTEM_PROMPT = """
Bạn là một giám khảo chấm thi kỳ thi Aptis Speaking (British Council).
Nhiệm vụ: Lắng nghe trực tiếp file ghi âm của thí sinh trả lời câu hỏi Part 1 (chuẩn thời gian trả lời 30 giây) và đưa ra đánh giá toàn diện theo thang CEFR (A1, A2, B1, B2, C1, C2).

Yêu cầu tiêu chí chấm:
1. transcript: Chép lại chính xác lời nói của thí sinh từ file ghi âm.
2. cefr_band: Bậc điểm tổng thể (A1 | A2 | B1 | B2 | C1).
3. grammar: Nhận xét lỗi sai ngữ pháp và liệt kê danh sách các câu sai -> câu sửa đúng tương ứng.
4. vocabulary: Nhận xét vốn từ vựng và gợi ý từ vựng/thành ngữ nâng cao thay thế (better_words).
5. fluency: Nhận xét độ trôi chảy, nhịp điệu, tốc độ nói và độ ngập ngừng.
6. pronunciation: Nhận xét về phát âm, trọng âm từ và âm cuối (ending sounds).
7. general_feedback: Nhận xét động viên, chỉ dẫn ngắn gọn cách cải thiện nhanh nhất.
8. model_answer: Bài mẫu chuẩn band B2/C1 cho 30 giây (độ dài khoảng 45-60 từ, từ vựng tự nhiên).

BẮT BUỘC trả về DUY NHẤT một chuỗi JSON hợp lệ theo đúng cấu trúc sau:
{
  "transcript": "...",
  "cefr_band": "B1",
  "criteria": {
    "grammar": {
      "score": "B1",
      "comment": "...",
      "corrections": ["Lỗi sai -> Cách sửa đúng"]
    },
    "vocabulary": {
      "score": "B1",
      "comment": "...",
      "better_words": ["Từ đơn giản -> Từ nâng cao hơn"]
    },
    "fluency": {
      "score": "A2",
      "comment": "..."
    },
    "pronunciation": {
      "score": "B1",
      "comment": "..."
    }
  },
  "general_feedback": "...",
  "model_answer": "..."
}
"""

def evaluate_audio(audio_bytes: bytes, question_text: str, api_key: str):
    client = genai.Client(api_key=api_key)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
        
    try:
        audio_file = client.files.upload(file=temp_audio_path)
        
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[
                audio_file,
                f"Aptis Part 1 Question: {question_text}\nHãy nghe và đánh giá chi tiết bài nói theo chuẩn CEFR."
            ],
            config=types.GenerateContentConfig(
                system_instruction=APTIS_SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

# --- KHỞI TẠO STATE ---
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/microphone.png", width=110)
    st.title("Aptis Speaking")
    st.caption("Bộ đề ôn tập Part 1 tự động")
    
    st.markdown("---")
    if not GEMINI_API_KEY:
        input_key = st.text_input("🔑 Nhập Gemini API Key:", type="password")
        if input_key:
            GEMINI_API_KEY = input_key
            
    st.subheader("📋 Chọn câu hỏi luyện tập")
    options = [f"Câu {q['id']}: {q['topic']}" for q in QUESTIONS]
    selected_option = st.selectbox(
        "Danh sách 28 câu hỏi Part 1:",
        options=options,
        index=st.session_state.current_idx
    )
    st.session_state.current_idx = options.index(selected_option)
    
    st.markdown("---")
    st.markdown("""
    **💡 Hướng dẫn 3 bước cực dễ:**
    1. Bấm vào biểu tượng **Micro** 🎙️ để bắt đầu nói.
    2. Trả lời câu hỏi trong khoảng **30 giây**.
    3. Bấm lại micro để dừng, rồi bấm **🚀 Chấm điểm ngay**.
    """)

# --- GIAO DIỆN CHÍNH ---
current_q = QUESTIONS[st.session_state.current_idx]

st.markdown('<div class="main-title">🎙️ Luyện thi Speaking Aptis Part 1</div>', unsafe_allow_html=True)
st.write("Hệ thống chấm điểm phát âm, ngữ pháp, từ vựng và độ trôi chảy theo khung chuẩn Châu Âu CEFR.")

col_main, col_res = st.columns([1, 1], gap="large")

with col_main:
    st.markdown(f"### 🎯 Chủ đề: **{current_q['topic']}**")
    st.markdown(f'<div class="question-box">❓ {current_q["question"]}</div>', unsafe_allow_html=True)
    
    st.markdown("#### ⏱️ Thu âm câu trả lời (Khoảng 30 giây)")
    st.caption("Nhấn vào biểu tượng Micro để ghi âm:")
    
    audio_bytes = audio_recorder(
        text="",
        recording_color="#EF4444",
        neutral_color="#3B82F6",
        icon_size="3x",
        pause_threshold=30.0
    )
    
    if audio_bytes:
        st.success("✅ Đã ghi âm thành công! Bạn có thể nghe lại bên dưới:")
        st.audio(audio_bytes, format="audio/wav")
        
        btn_eval = st.button("🚀 Chấm điểm ngay với AI", type="primary", use_container_width=True)
        if btn_eval:
            if not GEMINI_API_KEY:
                st.error("⚠️ Vui lòng nhập hoặc cấu hình GEMINI_API_KEY để AI chấm điểm!")
            else:
                with st.spinner("⏳ Giám khảo AI đang lắng nghe và phân tích bài nói của bạn..."):
                    try:
                        result = evaluate_audio(audio_bytes, current_q["question"], GEMINI_API_KEY)
                        st.session_state[f"result_{current_q['id']}"] = result
                    except Exception as e:
                        st.error(f"Đã có lỗi xảy ra trong quá trình chấm: {str(e)}")

with col_res:
    st.markdown("### 📊 Kết quả đánh giá chi tiết")
    
    active_result_key = f"result_{current_q['id']}"
    if active_result_key in st.session_state:
        res = st.session_state[active_result_key]
        
        band = res.get("cefr_band", "B1")
        st.metric(label="🏆 Ước tính trình độ (CEFR Band)", value=f"Band {band}")
        
        with st.expander("📝 Lời thoại bạn đã nói (Transcript)", expanded=True):
            st.write(res.get("transcript", "Không nghe rõ giọng nói."))
            
        criteria = res.get("criteria", {})
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**🔤 Ngữ pháp ({criteria.get('grammar', {}).get('score', '')})**")
            st.write(criteria.get('grammar', {}).get('comment', ''))
            corrections = criteria.get('grammar', {}).get('corrections', [])
            if corrections:
                st.caption("Các câu cần sửa:")
                for item in corrections:
                    st.markdown(f"- `{item}`")
                    
            st.markdown(f"**🗣️ Độ trôi chảy ({criteria.get('fluency', {}).get('score', '')})**")
            st.write(criteria.get('fluency', {}).get('comment', ''))
            
        with c2:
            st.markdown(f"**📖 Từ vựng ({criteria.get('vocabulary', {}).get('score', '')})**")
            st.write(criteria.get('vocabulary', {}).get('comment', ''))
            better_words = criteria.get('vocabulary', {}).get('better_words', [])
            if better_words:
                st.caption("Gợi ý từ vựng hay hơn:")
                for w in better_words:
                    st.markdown(f"- `{w}`")
                    
            st.markdown(f"**🔊 Phát âm ({criteria.get('pronunciation', {}).get('score', '')})**")
            st.write(criteria.get('pronunciation', {}).get('comment', ''))
            
        st.markdown("---")
        st.info(f"**💡 Lời khuyên của giám khảo:** {res.get('general_feedback', '')}")
        
        with st.expander("🌟 Câu trả lời tham khảo chuẩn Band B2/C1", expanded=False):
            st.write(res.get("model_answer", ""))
    else:
        st.info("👈 Chưa có bài chấm. Hãy bấm vào Micro ở cột bên trái để trả lời và nhấn nút chấm điểm!")
