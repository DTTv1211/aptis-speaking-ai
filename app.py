import streamlit as st
import json
import tempfile
import os
import httpx
from audio_recorder_streamlit import audio_recorder
from google import genai
from google.genai import types

# ==============================================================================
# CẤU HÌNH API KEY (Tự động nhận diện từ Secrets hoặc nhập trên web)
# ==============================================================================
DEFAULT_KEY = ""
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", DEFAULT_KEY))

st.set_page_config(
    page_title="Aptis Speaking AI Coach - Part 1 & Part 2",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .question-box {
        background-color: #EFF6FF;
        border-left: 5px solid #2563EB;
        padding: 14px;
        border-radius: 8px;
        font-size: 1.15rem;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DỮ LIỆU ĐỀ THI: PART 1 & PART 2
# ==============================================================================
PART1_QUESTIONS = [
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

PART2_DATA = [
  {
    "id": 1,
    "image": "https://aptiskey.com/images/speaking/part2/1.png",
    "questions": [
      "Describe the picture?",
      "Why do people like eating out with friends?",
      "Please talk about the last time you ate with friends?"
    ]
  },
  {
    "id": 2,
    "image": "https://aptiskey.com/images/speaking/part2/2.png",
    "questions": [
      "Describe the picture?",
      "Tell me the last time you traveled in a car?",
      "How can people overcome the time of a long journey?"
    ]
  },
  {
    "id": 3,
    "image": "https://aptiskey.com/images/speaking/part2/3.png",
    "questions": [
      "Describe the picture?",
      "How often do you watch films or programmers at home? Why?",
      "Which is better for learning, watching video or reading? Why?"
    ]
  },
  {
    "id": 4,
    "image": "https://aptiskey.com/images/speaking/part2/4.png",
    "questions": [
      "Describe the picture?",
      "Do you often watch TV?",
      "Why is free time important?"
    ]
  },
  {
    "id": 5,
    "image": "https://aptiskey.com/images/speaking/part2/5.png",
    "questions": [
      "Describe the picture?",
      "What do you usually read?",
      "Why is reading important for children?"
    ]
  },
  {
    "id": 6,
    "image": "https://aptiskey.com/images/speaking/part2/6.png",
    "questions": [
      "Describe the picture?",
      "When was the last time you visited a new place?",
      "Why do people like to go to new places?"
    ]
  },
  {
    "id": 7,
    "image": "https://aptiskey.com/images/speaking/part2/7.png",
    "questions": [
      "Describe the picture?",
      "Describe the last time you did some physical work.",
      "Do you think machines will do all our hard work in the future? Why?"
    ]
  },
  {
    "id": 8,
    "image": "https://aptiskey.com/images/speaking/part2/8.png",
    "questions": [
      "Describe the picture?",
      "Tell us about the time you give a presentation. How did you feel?",
      "Why are people scared of public speaking?"
    ]
  },
  {
    "id": 9,
    "image": "https://aptiskey.com/images/speaking/part2/9.png",
    "questions": [
      "Describe the picture?",
      "Tell us the last time you went to the sea?",
      "Why do some people dislike going to the sea?"
    ]
  },
  {
    "id": 10,
    "image": "https://aptiskey.com/images/speaking/part2/10.png",
    "questions": [
      "Describe the picture?",
      "Tell me about the last time you used public transport",
      "How can we increase the number of people using public transport?"
    ]
  },
  {
    "id": 11,
    "image": "https://aptiskey.com/images/speaking/part2/11.png",
    "questions": [
      "Describe the picture?",
      "Tell me about a time you laughed a lot.",
      "Do you think people from different countries laugh at different things?"
    ]
  },
  {
    "id": 12,
    "image": "https://aptiskey.com/images/speaking/part2/12.png",
    "questions": [
      "Describe the picture?",
      "How do people learn to cook in your culture",
      "Why is it important for people to learn how to cook for themselves?"
    ]
  },
  {
    "id": 13,
    "image": "https://aptiskey.com/images/speaking/part2/13.png",
    "questions": [
      "Describe the picture?",
      "In your country, do parents care about their children?",
      "Why do parents care about their children?"
    ]
  },
  {
    "id": 14,
    "image": "https://aptiskey.com/images/speaking/part2/14.png",
    "questions": [
      "Describe the picture?",
      "How do children go to school in your country?",
      "Is it common to live far from school in your country? Why?"
    ]
  },
  {
    "id": 15,
    "image": "https://aptiskey.com/images/speaking/part2/15.png",
    "questions": [
      "Describe the picture?",
      "Do you like dancing? Why? Why not?",
      "On what occasions do people usually dance in your country?"
    ]
  },
  {
    "id": 16,
    "image": "https://aptiskey.com/images/speaking/part2/16.png",
    "questions": [
      "Describe the picture?",
      "Tell me about a game you played when you were a child.",
      "How have the children's games changed in the last 50 years?"
    ]
  },
  {
    "id": 17,
    "image": "https://aptiskey.com/images/speaking/part2/17.png",
    "questions": [
      "Describe the picture?",
      "How do most people in your country learn about world news?",
      "How has the reporting of news changed in the last fifty years?"
    ]
  },
  {
    "id": 18,
    "image": "https://aptiskey.com/images/speaking/part2/18.png",
    "questions": [
      "Describe the picture?",
      "Do you like to climb mountains?",
      "Do you think outdoor activities are important?"
    ]
  },
  {
    "id": 19,
    "image": "https://aptiskey.com/images/speaking/part2/19.png",
    "questions": [
      "Describe the picture?",
      "Why is it important to play with children?",
      "How should parents spend time together with their children?"
    ]
  },
  {
    "id": 20,
    "image": "https://aptiskey.com/images/speaking/part2/20.png",
    "questions": [
      "Describe the picture?",
      "Tell me about an animal that you like?",
      "How important are animals in our lives?"
    ]
  },
  {
    "id": 21,
    "image": "https://aptiskey.com/images/speaking/part2/21.png",
    "questions": [
      "Describe the picture?",
      "What are the benefits of outdoor activities?",
      "Why do many people like outdoor activities?"
    ]
  },
  {
    "id": 22,
    "image": "https://aptiskey.com/images/speaking/part2/22.png",
    "questions": [
      "Describe the picture?",
      "In your country, do parents care about their children?",
      "Why do parents care about their children?"
    ]
  },
  {
    "id": 23,
    "image": "https://aptiskey.com/images/speaking/part2/23.png",
    "questions": [
      "Describe the picture?",
      "Tell me the time you shopped in a local store?",
      "Nowadays, why do people like shopping online?"
    ]
  },
  {
    "id": 24,
    "image": "https://aptiskey.com/images/speaking/part2/24.png",
    "questions": [
      "Describe the picture?",
      "Do you prefer reading newspapers or watching news?",
      "Why do people need to watch the news?"
    ]
  },
  {
    "id": 25,
    "image": "https://aptiskey.com/images/speaking/part2/25.png",
    "questions": [
      "Describe the picture?",
      "What do you think about living in a crowded city?",
      "Why do many people hate crowded places?"
    ]
  },
  {
    "id": 26,
    "image": "https://aptiskey.com/images/speaking/part2/26.png",
    "questions": [
      "Describe the picture?",
      "When was the last time you went on vacation with someone else?",
      "What are the benefits of hanging out with other people?"
    ]
  },
  {
    "id": 27,
    "image": "https://aptiskey.com/images/speaking/part2/27.png",
    "questions": [
      "Describe the picture?",
      "Tell me about a time you received or gave gifts?",
      "On what occasions in your country do people give gifts?"
    ]
  },
  {
    "id": 28,
    "image": "https://aptiskey.com/images/speaking/part2/28.png",
    "questions": [
      "Describe the picture?",
      "Have you ever written a hand letter?",
      "Do you plan to write handwritten letters in the future?"
    ]
  },
  {
    "id": 29,
    "image": "https://aptiskey.com/images/speaking/part2/29.png",
    "questions": [
      "Describe the picture?",
      "What are the benefits of viewing artworks?",
      "Why do people like to go to art exhibitions?"
    ]
  },
  {
    "id": 30,
    "image": "https://aptiskey.com/images/speaking/part2/30.png",
    "questions": [
      "Describe the picture?",
      "Tell me the last time you went shopping?",
      "What is missing here?"
    ]
  }
]

APTIS_SYSTEM_PROMPT = """
Bạn là một giám khảo chấm thi kỳ thi Aptis Speaking (British Council).
Nhiệm vụ: Lắng nghe trực tiếp file ghi âm của thí sinh trả lời câu hỏi và đánh giá chi tiết theo thang điểm CEFR (A1, A2, B1, B2, C1, C2).

Yêu cầu tiêu chí chấm:
1. transcript: Chép lại chính xác lời nói của thí sinh từ file ghi âm.
2. cefr_band: Bậc điểm tổng thể (A1 | A2 | B1 | B2 | C1).
3. criteria:
   - grammar: Nhận xét lỗi ngữ pháp và danh sách câu sai -> câu sửa đúng.
   - vocabulary: Nhận xét từ vựng và gợi ý từ thay thế nâng cao hơn (better_words).
   - fluency: Nhận xét độ lưu loát, tốc độ nói và độ ngập ngừng.
   - pronunciation: Nhận xét phát âm, trọng âm, ending sounds.
4. general_feedback: Nhận xét động viên, chỉ dẫn ngắn gọn cách cải thiện.
5. model_answer: Bài mẫu chuẩn band B2/C1 cho thời lượng câu hỏi (tự nhiên, đủ ý).

BẮT BUỘC trả về DUY NHẤT một chuỗi JSON hợp lệ:
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

def evaluate_audio(audio_bytes: bytes, question_text: str, api_key: str, image_url: str = None):
    client = genai.Client(api_key=api_key)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
        
    try:
        audio_file = client.files.upload(file=temp_audio_path)
        contents = [audio_file]
        
        if image_url:
            try:
                resp = httpx.get(image_url, timeout=10.0)
                if resp.status_code == 200:
                    contents.append(types.Part.from_bytes(data=resp.content, mime_type="image/png"))
            except Exception:
                pass

        contents.append(f"Câu hỏi: {question_text}\nHãy nghe bài nói (và quan sát ảnh nếu có) để chấm điểm CEFR chuẩn Aptis.")

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=APTIS_SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

# ==============================================================================
# GIAO DIỆN HỌC VIÊN
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/microphone.png", width=95)
    st.title("Aptis Speaking Coach")
    
    selected_part = st.radio("Chọn phần thi:", ["Part 1: Personal Info", "Part 2: Describe Picture"], index=1)
    
    st.markdown("---")
    if not GEMINI_API_KEY:
        input_key = st.text_input("🔑 Nhập Gemini API Key:", type="password")
        if input_key:
            GEMINI_API_KEY = input_key
            
    if selected_part == "Part 1: Personal Info":
        p1_titles = [f"Câu {q['id']}: {q['topic']}" for q in PART1_QUESTIONS]
        selected_idx = st.selectbox("Chọn câu hỏi (28 câu):", range(len(PART1_QUESTIONS)), format_func=lambda x: p1_titles[x])
    else:
        p2_titles = [f"Đề {item['id']}: {item['questions'][1] if len(item['questions'])>1 else 'Picture ' + str(item['id'])}" for item in PART2_DATA]
        selected_idx = st.selectbox("Chọn đề Part 2 (30 đề):", range(len(PART2_DATA)), format_func=lambda x: p2_titles[x])
        
    st.markdown("---")
    st.markdown("""
    **💡 Hướng dẫn:**
    1. Quan sát ảnh và đọc câu hỏi.
    2. Bấm vào biểu tượng **Micro** 🎙️ để trả lời (~45s cho Part 2, ~30s cho Part 1).
    3. Bấm lại micro để dừng, rồi bấm **🚀 Chấm điểm ngay**.
    """)

col_left, col_right = st.columns([1.1, 1], gap="large")

with col_left:
    if selected_part == "Part 1: Personal Info":
        curr_q = PART1_QUESTIONS[selected_idx]
        st.markdown(f'<div class="main-title">🎙️ Aptis Part 1: {curr_q["topic"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="question-box">❓ {curr_q["question"]}</div>', unsafe_allow_html=True)
        active_question = curr_q["question"]
        active_img = None
        target_time = 30
    else:
        curr_p2 = PART2_DATA[selected_idx]
        st.markdown(f'<div class="main-title">🖼️ Aptis Part 2: Đề {curr_p2["id"]}</div>', unsafe_allow_html=True)
        
        st.image(curr_p2["image"], use_container_width=True)
        
        sub_idx = st.radio(
            "Chọn câu hỏi phụ cần luyện tập (45 giây/câu):",
            [f"Câu {i+1}: {q}" for i, q in enumerate(curr_p2["questions"])],
            horizontal=False
        )
        selected_sub_num = int(sub_idx.split(":")[0].replace("Câu ", "")) - 1
        active_question = curr_p2["questions"][selected_sub_num]
        active_img = curr_p2["image"]
        target_time = 45

        st.markdown(f'<div class="question-box">❓ {active_question}</div>', unsafe_allow_html=True)

    st.markdown(f"#### ⏱️ Thu âm câu trả lời (Chuẩn ~{target_time} giây)")
    audio_bytes = audio_recorder(
        text="",
        recording_color="#EF4444",
        neutral_color="#3B82F6",
        icon_size="3x",
        pause_threshold=float(target_time)
    )

    if audio_bytes:
        st.success("✅ Đã ghi âm xong! Bạn có thể nghe lại bên dưới:")
        st.audio(audio_bytes, format="audio/wav")
        
        btn_eval = st.button("🚀 Chấm điểm ngay với AI", type="primary", use_container_width=True)
        if btn_eval:
            if not GEMINI_API_KEY:
                st.error("⚠️ Vui lòng cấu hình GEMINI_API_KEY!")
            else:
                with st.spinner("Giám khảo AI đang quan sát ảnh, lắng nghe và chấm điểm..."):
                    try:
                        result = evaluate_audio(audio_bytes, active_question, GEMINI_API_KEY, active_img)
                        st.session_state["current_feedback"] = result
                    except Exception as e:
                        st.error(f"Đã có lỗi: {str(e)}")

with col_right:
    st.markdown("### 📊 Kết quả đánh giá chi tiết")
    if "current_feedback" in st.session_state:
        res = st.session_state["current_feedback"]
        
        band = res.get("cefr_band", "B1")
        st.metric(label="🏆 Bậc CEFR Ước tính", value=f"Band {band}")
        
        with st.expander("📝 Lời thoại thí sinh (Transcript)", expanded=True):
            st.write(res.get("transcript", ""))
            
        crit = res.get("criteria", {})
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**🔤 Ngữ pháp ({crit.get('grammar', {}).get('score', '')})**")
            st.write(crit.get('grammar', {}).get('comment', ''))
            for err in crit.get('grammar', {}).get('corrections', []):
                st.markdown(f"- `{err}`")
                
            st.markdown(f"**🗣️ Độ trôi chảy ({crit.get('fluency', {}).get('score', '')})**")
            st.write(crit.get('fluency', {}).get('comment', ''))
            
        with c2:
            st.markdown(f"**📖 Từ vựng ({crit.get('vocabulary', {}).get('score', '')})**")
            st.write(crit.get('vocabulary', {}).get('comment', ''))
            for w in crit.get('vocabulary', {}).get('better_words', []):
                st.markdown(f"- `{w}`")

            st.markdown(f"**🔊 Phát âm ({crit.get('pronunciation', {}).get('score', '')})**")
            st.write(crit.get('pronunciation', {}).get('comment', ''))

        st.markdown("---")
        st.info(f"💡 **Lời khuyên của giám khảo:** {res.get('general_feedback', '')}")
        with st.expander("🌟 Câu trả lời mẫu Band B2/C1", expanded=False):
            st.write(res.get("model_answer", ""))
    else:
        st.info("👈 Chưa có bài chấm. Hãy bấm vào Micro ở cột bên trái để trả lời và nhấn nút chấm điểm!")
