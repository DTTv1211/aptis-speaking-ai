import streamlit as st
import json
import tempfile
import os
from audio_recorder_streamlit import audio_recorder
from google import genai
from google.genai import types

# ==========================================
# 1. ĐIỀN API KEY CỦA BẠN TRỰC TIẾP VÀO ĐÂY
# ==========================================
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# Cấu hình giao diện
st.set_page_config(
    page_title="Luyện thi Speaking Aptis Part 1",
    page_icon="🎙️",
    layout="wide"
)

# Khởi tạo câu hỏi mặc định
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0

# 28 câu hỏi Part 1 đã trích xuất từ đề thi
QUESTIONS = [
    {"topic": "Family", "question": "Please tell me about your family?"},
    {"topic": "Personal Introduction", "question": "Please tell me about yourself?"},
    {"topic": "Hometown & Places", "question": "Tell me about your hometown / the place that you live? / A famous place in your country?"},
    {"topic": "Travel in Country", "question": "Tell me the best way to travel about around your country?"},
    {"topic": "Friend & Family Member", "question": "Tell me about your friend / a member in your family"},
    {"topic": "Weather & Seasons", "question": "What is the weather like today? / What is your favorite season?"},
    {"topic": "Good Memories", "question": "Please tell me about one of your good memories"},
    {"topic": "Activities with Friends", "question": "What do you like doing with your friends?"},
    {"topic": "Free Time Activities", "question": "What do you like doing in your free time?"},
    {"topic": "Past Activities", "question": "What did you do last night / on the weekend?"},
    {"topic": "First School", "question": "Please tell me about your first school?"},
    {"topic": "Current Room", "question": "Describe the room you are in?"},
    {"topic": "Journey Today", "question": "Describe your journey here today?"},
    {"topic": "Clothing & Outfit", "question": "What are you wearing today?"},
    {"topic": "Feeling Tired", "question": "When do you feel tired?"},
    {"topic": "Vietnamese Meal", "question": "Describe a typical Vietnamese meal?"},
    {"topic": "Typical Day", "question": "Describe your typical day?"},
    {"topic": "Free Time Hobbies", "question": "What do you like to do in your free time?"},
    {"topic": "Favorite Places", "question": "Describe your favorite places"},
    {"topic": "Conversation with Mother", "question": "Tell me about the last time you talked with your mother"},
    {"topic": "Sports in Country", "question": "People like sport in your country"},
    {"topic": "New House", "question": "What are you looking for in your new house?"},
    {"topic": "Learning English", "question": "Why are you learning English?"},
    {"topic": "Work & Profession", "question": "Describe your job"},
    {"topic": "Food & Cuisine", "question": "What is the food like in your country?"},
    {"topic": "Stress & Pressure", "question": "When do you feel stressed?"},
    {"topic": "Travel Interests", "question": "Tell me why you are interested in travel?"},
    {"topic": "Favorite Books", "question": "Favorite book in your country?"}
]

# Prompt chấm CEFR chuẩn Aptis
APTIS_SYSTEM_PROMPT = """
Bạn là giám khảo kỳ thi Aptis Speaking (British Council).
Nhiệm vụ: Đánh giá câu trả lời Speaking Part 1 (thời lượng chuẩn 30 giây).

Tiêu chí:
1. Grammar: Chỉ rõ các lỗi ngữ pháp đã mắc phải và cách sửa cụ thể.
2. Vocabulary: Đánh giá độ phù hợp, gợi ý từ thay thế band cao hơn.
3. Fluency: Đánh giá độ trôi chảy, tốc độ nói, khoảng dừng ngập ngừng.
4. Pronunciation: Nhận xét phát âm từ, âm cuối (ending sounds), trọng âm.

Trả về DUY NHẤT định dạng JSON theo đúng schema sau:
{
  "transcript": "Lời thoại thí sinh đã nói",
  "cefr_band": "A1 | A2 | B1 | B2 | C1",
  "criteria": {
    "grammar": {
      "score": "A2/B1/B2...",
      "comment": "Nhận xét chi tiết ngữ pháp",
      "corrections": ["Lỗi -> Sửa"]
    },
    "vocabulary": {
      "score": "A2/B1/B2...",
      "comment": "Nhận xét chi tiết từ vựng",
      "better_words": ["Từ cũ -> Từ nâng cao"]
    },
    "fluency": {
      "score": "A2/B1/B2...",
      "comment": "Nhận xét độ lưu loát"
    },
    "pronunciation": {
      "score": "A2/B1/B2...",
      "comment": "Nhận xét phát âm"
    }
  },
  "general_feedback": "Lời khuyên tổng quan ngắn gọn",
  "model_answer": "Câu trả lời mẫu B2/C1 cho 30s (khoảng 45-60 từ)"
}
"""

def evaluate_audio(audio_bytes: bytes, question_text: str):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
        
    try:
        audio_file = client.files.upload(file=temp_audio_path)
        
        # Dùng model flash-lite với hạn mức 500 RPD
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[
                audio_file,
                f"Question: {question_text}\nHãy phân tích file ghi âm và chấm điểm theo tiêu chí Aptis."
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

# --- Giao diện học viên ---
st.title("🎙️ Luyện thi Speaking Aptis Part 1")
st.caption("Chấm điểm tự động theo tiêu chuẩn British Council CEFR")

# Thanh bên chỉ để chọn câu hỏi
with st.sidebar:
    st.header("📚 Chọn câu hỏi")
    q_titles = [f"Câu {i+1}: {q['topic']}" for i, q in enumerate(QUESTIONS)]
    selected_idx = st.selectbox("Danh sách 28 câu hỏi:", range(len(QUESTIONS)), format_func=lambda x: q_titles[x])
    st.session_state.current_q_idx = selected_idx
    
    st.markdown("---")
    st.markdown("""
    **Hướng dẫn làm bài:**
    1. Đọc câu hỏi ở bảng bên phải.
    2. Bấm vào biểu tượng **Micro** để ghi âm.
    3. Nói câu trả lời trong khoảng **30 giây**.
    4. Bấm lại micro để dừng, sau đó bấm **🚀 Chấm điểm ngay**.
    """)

current_q = QUESTIONS[st.session_state.current_q_idx]
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader(f"📌 Chủ đề: {current_q['topic']}")
    st.info(f"**Question:** {current_q['question']}")
    
    st.markdown("### ⏱️ Thu âm câu trả lời (30 giây)")
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e83e8c",
        neutral_color="#6aa36f",
        icon_size="3x",
        pause_threshold=30.0
    )
    
    if audio_bytes:
        st.success("✅ Đã ghi âm xong!")
        st.audio(audio_bytes, format="audio/wav")
        
        btn_eval = st.button("🚀 Chấm điểm ngay với AI", type="primary", use_container_width=True)
        if btn_eval:
            if GEMINI_API_KEY == "AIzaSy..." or not GEMINI_API_KEY:
                st.error("⚠️ Bạn chưa dán GEMINI_API_KEY vào đầu file app.py!")
            else:
                with st.spinner("AI đang lắng nghe và chấm điểm..."):
                    try:
                        result = evaluate_audio(audio_bytes, current_q['question'])
                        st.session_state.last_result = result
                    except Exception as e:
                        st.error(f"Đã có lỗi xảy ra: {str(e)}")

with col_right:
    st.subheader("📊 Kết quả chấm điểm")
    if "last_result" in st.session_state:
        res = st.session_state.last_result
        
        band = res.get("cefr_band", "N/A")
        st.metric(label="Ước tính trình độ CEFR", value=f"{band}")
        
        with st.expander("📝 Đoạn văn đã nói (Transcript)", expanded=True):
            st.write(res.get("transcript", ""))
            
        criteria = res.get("criteria", {})
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**🔤 Ngữ pháp ({criteria.get('grammar', {}).get('score', '')})**")
            st.write(criteria.get('grammar', {}).get('comment', ''))
            corrections = criteria.get('grammar', {}).get('corrections', [])
            if corrections:
                st.caption("Lỗi cần sửa:")
                for item in corrections:
                    st.markdown(f"- `{item}`")
                    
            st.markdown(f"**🗣️ Độ trôi chảy ({criteria.get('fluency', {}).get('score', '')})**")
            st.write(criteria.get('fluency', {}).get('comment', ''))
            
        with c2:
            st.markdown(f"**📖 Từ vựng ({criteria.get('vocabulary', {}).get('score', '')})**")
            st.write(criteria.get('vocabulary', {}).get('comment', ''))
            better_words = criteria.get('vocabulary', {}).get('better_words', [])
            if better_words:
                st.caption("Từ vựng nâng cao nên dùng:")
                for w in better_words:
                    st.markdown(f"- `{w}`")

            st.markdown(f"**🔊 Phát âm ({criteria.get('pronunciation', {}).get('score', '')})**")
            st.write(criteria.get('pronunciation', {}).get('comment', ''))
            
        st.markdown("---")
        st.markdown(f"**💡 Nhận xét tổng quan:** {res.get('general_feedback', '')}")
        with st.expander("🌟 Câu trả lời mẫu chuẩn Band B2/C1"):
            st.write(res.get("model_answer", ""))
    else:
        st.info("Hãy bấm micro để ghi âm và bấm nút chấm điểm để xem kết quả tại đây.")