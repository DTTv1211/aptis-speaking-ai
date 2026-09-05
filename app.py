import os
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from question_bank import PART1_DATA, PART2_DATA, PART3_DATA, PART4_DATA, part4_questions

load_dotenv()

st.set_page_config(
    page_title="Aptis AI Speaking Practice",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


class AptisFeedback(BaseModel):
    transcript: str = Field(description="Transcript of the candidate response")
    cefr_level: str = Field(description="Estimated CEFR level: A1, A2, B1, B2, or C")
    grammar_score: int = Field(ge=1, le=5, description="Grammar score from 1 to 5")
    vocabulary_score: int = Field(ge=1, le=5, description="Vocabulary score from 1 to 5")
    fluency_score: int = Field(ge=1, le=5, description="Fluency and rhythm score from 1 to 5")
    task_fulfillment_score: int = Field(ge=1, le=5, description="Task fulfillment score from 1 to 5")
    pronunciation_feedback: str = Field(description="Concise pronunciation and intonation feedback")
    detailed_feedback: str = Field(description="Key strengths and the most important language errors to fix")
    better_version: str = Field(description="A stronger B2/C-style sample answer based on the same ideas")
    formula_feedback: str = Field(description="How well the candidate followed the recommended speaking formula")


PART_LABELS = {
    "Part 1": "Part 1: Personal Information (30s/câu)",
    "Part 2": "Part 2: Describe, Opinion & Experience (45s/câu)",
    "Part 3": "Part 3: Compare two pictures (45s/câu)",
    "Part 4": "Part 4: Extended response (1 phút chuẩn bị + 2 phút nói)",
}

FORMULAS = {
    "Part 1": "Answer directly → add 1 detail → add 1 reason/example.",
    "Part 2": "Overall → Details (foreground/background) → Atmosphere → Personal link.",
    "Part 3": "Similarity → Differences (whereas/while) → Preference + 2 reasons.",
    "Part 4": "Past event → Problem → Action → Result → Feeling/Lesson → Broader social view.",
}

QUESTION_SOURCES = {
    "Part 1": PART1_DATA,
    "Part 2": PART2_DATA,
    "Part 3": PART3_DATA,
    "Part 4": PART4_DATA,
}


def get_secret(name: str) -> Optional[str]:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    value = os.getenv(name)
    return value if value else None


def evaluate_submission(
    api_key: str,
    part_name: str,
    questions: list[str],
    formula: str,
    audio_bytes: Optional[bytes] = None,
    audio_mime: str = "audio/wav",
    text_input: Optional[str] = None,
) -> AptisFeedback:
    if not api_key:
        raise ValueError("Thiếu GEMINI_API_KEY.")

    client = genai.Client(api_key=api_key)
    questions_str = "\n".join(f"- {q}" for q in questions)

    prompt = f"""
You are an AI practice evaluator for Aptis ESOL Speaking. This is training feedback, not an official British Council score.

PART: {part_name}
QUESTIONS:
{questions_str}

RECOMMENDED RESPONSE FORMULA:
{formula}

Evaluate the candidate's response using a CEFR-oriented practice rubric.
Requirements:
1. Transcribe the audio accurately when audio is provided. If text is provided, preserve it as the transcript.
2. Estimate CEFR as A1, A2, B1, B2, or C.
3. Give integer scores from 1 to 5 for grammar, vocabulary, fluency, and task fulfillment.
4. For pronunciation feedback, be concise and specific. If only text was provided, explicitly say pronunciation cannot be judged reliably from text.
5. In detailed_feedback, identify only the 3 highest-impact fixes. Do not overwhelm the learner.
6. In better_version, produce a natural B2/C-style answer that directly answers all questions and can be memorised as a speaking model.
7. In formula_feedback, say which steps of the recommended formula were present or missing.
8. Respond in Vietnamese except for the transcript and better_version, which should remain in English.
""".strip()

    contents = [prompt]
    if audio_bytes:
        contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))
    elif text_input and text_input.strip():
        contents.append(f"Candidate response:\n{text_input.strip()}")
    else:
        raise ValueError("Cần cung cấp bản ghi âm hoặc transcript.")

    model_name = get_secret("GEMINI_MODEL") or "gemini-2.5-flash"
    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AptisFeedback,
            temperature=0.2,
        ),
    )

    if response.parsed is None:
        raise RuntimeError("AI không trả về structured output hợp lệ. Hãy thử lại.")
    return response.parsed


def normalize_exam(part_key: str, item: dict) -> dict:
    """Adapt each synchronized source item to the compact UI shape."""
    if part_key == "Part 1":
        return {
            "title": item.get("topic", "Personal Information"),
            "instructions": "Trả lời tự nhiên, khoảng 30 giây.",
            "questions": [item["question"]],
            "images": [],
        }
    if part_key == "Part 2":
        return {
            "title": f"Đề Part 2 #{item['id']}",
            "instructions": "Mỗi câu khoảng 45 giây. Mô tả ảnh rồi mở rộng ý.",
            "questions": item["questions"],
            "images": [item["image"]],
        }
    if part_key == "Part 3":
        return {
            "title": f"Đề Part 3 #{item['id']}",
            "instructions": "So sánh hai hình, trả lời lần lượt 3 câu hỏi.",
            "questions": item["questions"],
            "images": item["images"],
        }
    return {
        "title": f"Đề Part 4 #{item['id']}",
        "instructions": "1 phút chuẩn bị, 2 phút nói liền mạch cả 3 ý.",
        "questions": part4_questions(item["question"]),
        "images": [item["image"]] if item.get("image") else [],
    }


def render_images(images: list[str]) -> None:
    if not images:
        return
    if len(images) == 1:
        try:
            st.image(images[0], caption="Ảnh đề bài", width="stretch")
        except Exception:
            st.warning("Không tải được ảnh đề bài. Bạn vẫn có thể trả lời theo câu hỏi.")
        return
    cols = st.columns(len(images))
    for idx, (col, image) in enumerate(zip(cols, images), start=1):
        with col:
            try:
                st.image(image, caption=f"Hình {idx}", width="stretch")
            except Exception:
                st.warning(f"Không tải được hình {idx}.")


st.markdown(
    """
<style>
.block-container {padding-top: 1.8rem; padding-bottom: 3rem;}
[data-testid="stMetricValue"] {font-size: 1.65rem;}
.formula-box {padding: 0.9rem 1rem; border-radius: 0.75rem; background: #f8fafc; border: 1px solid #e2e8f0;}
.small-note {font-size: 0.9rem; opacity: 0.8;}
</style>
""",
    unsafe_allow_html=True,
)

if "session_api_key" not in st.session_state:
    st.session_state.session_api_key = ""

with st.sidebar:
    st.header("⚙️ Phòng luyện Aptis")
    part_key = st.selectbox("Chọn phần", list(PART_LABELS.keys()), format_func=lambda x: PART_LABELS[x])
    source_items = QUESTION_SOURCES[part_key]
    selected_index = st.selectbox(
        "Chọn đề",
        range(len(source_items)),
        format_func=lambda index: f"Đề {source_items[index]['id']}",
        key=f"question_index_{part_key}",
    )

    st.divider()
    st.subheader("🔑 Gemini")
    configured_key = get_secret("GEMINI_API_KEY")
    if configured_key:
        st.success("Đã nhận GEMINI_API_KEY từ Secrets/Environment.")
    else:
        st.session_state.session_api_key = st.text_input(
            "Gemini API Key cho phiên này",
            type="password",
            value=st.session_state.session_api_key,
            help="Key chỉ được giữ trong session Streamlit hiện tại; không ghi vào repo.",
        )
        st.caption("Khi deploy, nên đặt GEMINI_API_KEY trong Streamlit Secrets.")

    st.divider()
    show_formula = st.toggle("Hiện formula gợi ý", value=True)
    st.caption("AI feedback là công cụ luyện tập, không phải kết quả Aptis chính thức.")

api_key = configured_key or st.session_state.session_api_key
exam = normalize_exam(part_key, source_items[selected_index])
formula = FORMULAS[part_key]

st.title("🎯 Aptis Speaking AI Practice")
st.caption("Luyện phản xạ theo formula → thu âm/nhập transcript → nhận feedback CEFR-oriented ngay.")

left, right = st.columns([1.35, 1])
with left:
    st.subheader(exam["title"])
    st.write(exam["instructions"])
    render_images(exam["images"])

    st.markdown("#### ❓ Questions")
    for i, question in enumerate(exam["questions"], start=1):
        st.markdown(f"**{i}. {question}**")

with right:
    st.subheader("🧠 Formula phản xạ")
    if show_formula:
        st.markdown(f'<div class="formula-box"><b>{part_key}</b><br>{formula}</div>', unsafe_allow_html=True)
    else:
        st.info("Formula đang được ẩn để mô phỏng phòng thi.")

    if part_key == "Part 4":
        st.warning("Phòng thi: 1 phút chuẩn bị → 2 phút nói liền mạch. Hãy trả lời cả 3 ý trong một bài.")
    elif part_key in {"Part 2", "Part 3"}:
        st.info("Mục tiêu: khoảng 45 giây cho mỗi câu.")
    else:
        st.info("Mục tiêu: khoảng 30 giây cho mỗi câu.")

st.divider()
input_mode = st.radio(
    "Phương thức làm bài",
    ["🎙️ Thu âm trực tiếp", "⌨️ Nhập transcript"],
    horizontal=True,
)

recorded_audio = None
text_response = ""
if input_mode == "🎙️ Thu âm trực tiếp":
    recorded_audio = st.audio_input("Ghi âm bài nói")
    st.caption("Nói một lượt như phòng thi, sau đó bấm Chấm bài.")
else:
    text_response = st.text_area(
        "Transcript",
        height=190,
        placeholder="Overall, this picture shows...",
    )

submitted = st.button("🚀 Chấm bài ngay", type="primary", use_container_width=True)

if submitted:
    if not api_key:
        st.error("Chưa có GEMINI_API_KEY. Nhập key ở sidebar hoặc cấu hình Streamlit Secrets.")
    elif input_mode == "🎙️ Thu âm trực tiếp" and recorded_audio is None:
        st.warning("Hãy ghi âm trước khi chấm bài.")
    elif input_mode == "⌨️ Nhập transcript" and not text_response.strip():
        st.warning("Hãy nhập transcript trước khi chấm bài.")
    else:
        with st.spinner("AI đang chấm bài..."):
            try:
                if recorded_audio is not None and input_mode == "🎙️ Thu âm trực tiếp":
                    audio_bytes = recorded_audio.getvalue()
                    mime_type = getattr(recorded_audio, "type", None) or "audio/wav"
                    result = evaluate_submission(
                        api_key=api_key,
                        part_name=PART_LABELS[part_key],
                        questions=exam["questions"],
                        formula=formula,
                        audio_bytes=audio_bytes,
                        audio_mime=mime_type,
                    )
                else:
                    result = evaluate_submission(
                        api_key=api_key,
                        part_name=PART_LABELS[part_key],
                        questions=exam["questions"],
                        formula=formula,
                        text_input=text_response,
                    )

                st.success(f"Estimated CEFR: {result.cefr_level}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Grammar", f"{result.grammar_score}/5")
                c2.metric("Vocabulary", f"{result.vocabulary_score}/5")
                c3.metric("Fluency", f"{result.fluency_score}/5")
                c4.metric("Task", f"{result.task_fulfillment_score}/5")

                with st.expander("📄 Transcript", expanded=True):
                    st.write(result.transcript)

                fb1, fb2 = st.columns(2)
                with fb1:
                    st.subheader("🗣️ Pronunciation / Intonation")
                    st.info(result.pronunciation_feedback)
                    st.subheader("🧩 Formula")
                    st.info(result.formula_feedback)
                with fb2:
                    st.subheader("🎯 3 lỗi cần sửa nhất")
                    st.warning(result.detailed_feedback)

                st.subheader("🌟 Better version — B2/C model")
                st.success(result.better_version)
            except Exception as exc:
                st.error(f"Chấm bài thất bại: {exc}")
                st.caption("Kiểm tra API key, model name, quota và kết nối mạng của Streamlit Cloud.")

st.divider()
st.markdown(
    '<p class="small-note">Practice tool only. CEFR level and scores are AI estimates and are not official British Council Aptis results.</p>',
    unsafe_allow_html=True,
)
