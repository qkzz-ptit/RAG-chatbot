"""Responsive Streamlit chat interface for PTIT."""

import streamlit as st

from . import config as _config
from .rag import answer_question, build_rag_chain


def explain_error(error: Exception) -> str:
    """Turn provider failures into a useful, non-technical chat message."""
    detail = str(error).lower()
    if "503" in detail or "unavailable" in detail or "high demand" in detail:
        return (
            "Các mô hình AI đang quá tải tạm thời. Mình đã thử mô hình dự phòng "
            "nhưng chưa nhận được phản hồi; bạn thử gửi lại sau ít phút nhé."
        )
    if "429" in detail or "resource_exhausted" in detail or "quota" in detail:
        return (
            "Dịch vụ AI đã chạm giới hạn lượt gọi hiện tại. Vui lòng thử lại sau "
            "hoặc kiểm tra hạn mức API của ứng dụng."
        )
    if "504" in detail or "deadline_exceeded" in detail or "timed out" in detail:
        return "Yêu cầu mất quá nhiều thời gian. Bạn thử gửi lại sau ít phút nhé."
    return "Mình chưa xử lý được yêu cầu này. Bạn thử lại sau ít phút nhé."


@st.cache_resource(show_spinner=False)
def get_rag_chain():
    """Build the expensive retrieval resources once per Streamlit process."""
    return build_rag_chain()


def show_sources(sources):
    with st.expander("Tài liệu đã tra cứu", icon=":material/menu_book:"):
        for source in sources:
            label = source["name"]
            if source.get("page"):
                label += f" · trang {source['page']}"
            if source.get("url"):
                st.markdown(f"- [{label}]({source['url']})")
            else:
                st.caption(label)


def run() -> None:
    """Render the full page. Call this on every Streamlit script rerun."""
    st.set_page_config(
        page_title="PTIT AI | Trợ lý thông tin",
        page_icon="🎓",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
        :root {
          --ptit-bg: var(--st-background-color);
          --ptit-surface: var(--st-secondary-background-color);
          --ptit-text: var(--st-text-color);
          --ptit-primary: var(--st-primary-color);
          --ptit-border: var(--st-border-color);
        }
        .stApp, [data-testid="stAppViewContainer"] {
          background: var(--ptit-bg);
          color: var(--ptit-text);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] {
          max-width: 940px;
          padding-top: clamp(1.5rem, 5vh, 3.5rem);
          padding-bottom: 7rem;
        }
        h1, h2, h3, [data-testid="stHeading"] {
          color: var(--ptit-text) !important;
          opacity: 1 !important;
        }
        [data-testid="stMarkdownContainer"] { color: var(--ptit-text); }
        [data-testid="stChatMessage"] {
          border: 1px solid var(--ptit-border);
          border-radius: 16px;
          padding: .85rem 1rem;
          background: var(--ptit-surface);
        }
        [data-testid="stChatMessage"][aria-label="user"] {
          background: color-mix(in srgb, var(--ptit-primary) 9%, var(--ptit-bg));
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
          line-height: 1.7;
        }
        [data-testid="stChatInput"] {
          background: var(--ptit-surface) !important;
          border: 1px solid var(--ptit-border) !important;
          border-radius: 16px !important;
          box-shadow: 0 8px 28px color-mix(in srgb, var(--ptit-text) 9%, transparent);
        }
        [data-testid="stChatInput"] textarea {
          color: var(--ptit-text) !important;
          background: transparent !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
          color: var(--ptit-text) !important;
          opacity: .62;
        }
        [data-testid="stSidebar"] {
          background: var(--ptit-surface);
          border-right: 1px solid var(--ptit-border);
        }
        .ptit-eyebrow {
          color: var(--ptit-primary);
          font-size: .76rem;
          font-weight: 700;
          letter-spacing: .1em;
          text-transform: uppercase;
        }
        .ptit-subtitle {
          color: var(--ptit-text);
          opacity: .78;
          font-size: 1.04rem;
          line-height: 1.7;
          max-width: 680px;
        }
        .stButton > button {
          min-height: 3.25rem;
          justify-content: flex-start;
          text-align: left;
          white-space: normal;
          color: var(--ptit-text);
          background: var(--ptit-surface);
          border: 1px solid var(--ptit-border);
          border-radius: 12px;
          transition: border-color .15s ease, color .15s ease, transform .15s ease;
        }
        .stButton > button:hover {
          color: var(--ptit-primary);
          border-color: var(--ptit-primary);
          transform: translateY(-1px);
        }
        .stButton > button:focus-visible {
          outline: 2px solid var(--ptit-primary);
          outline-offset: 2px;
        }
        [data-testid="stExpander"] {
          border-color: var(--ptit-border);
          border-radius: 12px;
        }
        @media (max-width: 640px) {
          [data-testid="stMainBlockContainer"] { padding: 1.3rem .9rem 6rem; }
          [data-testid="stHorizontalBlock"] { flex-direction: column; gap: .55rem; }
          [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
            flex: 1 1 100%;
            width: 100% !important;
          }
          [data-testid="stChatMessage"] { padding: .65rem .75rem; border-radius: 14px; }
          h1 { font-size: 1.8rem !important; line-height: 1.22 !important; }
          .ptit-subtitle { font-size: .96rem; }
          .stButton > button { min-height: 3rem; }
          [data-testid="stChatInput"] textarea { font-size: 16px !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.markdown("### PTIT · Tra cứu")
        st.caption("Thông tin tuyển sinh, đào tạo và dịch vụ sinh viên.")
        st.markdown("---")
        st.markdown("**Tra cứu chính thức**")
        st.link_button("Cổng PTIT", "https://ptit.edu.vn", width="stretch")
        st.link_button("Thông tin tuyển sinh", "https://tuyensinh.ptit.edu.vn", width="stretch")
        st.link_button("Cổng đào tạo", "https://daotao.ptit.edu.vn", width="stretch")
        st.caption("Thông tin tuyển sinh và học phí có thể thay đổi theo từng năm.")
        if st.button("Xóa cuộc trò chuyện", icon=":material/delete:", width="stretch"):
            st.session_state.messages = []
            st.rerun()

    st.markdown(
        '<div class="ptit-eyebrow">Học viện Công nghệ Bưu chính Viễn thông</div>',
        unsafe_allow_html=True,
    )
    st.title("Tra cứu thông tin PTIT")
    st.markdown(
        '<div class="ptit-subtitle">Tuyển sinh, điểm chuẩn, ngành đào tạo, học phí và thông tin mới nhất từ các cổng chính thức của Học viện.</div>',
        unsafe_allow_html=True,
    )

    suggestions = [
        "PTIT có những cơ sở đào tạo nào?",
        "Các ngành công nghệ nổi bật của PTIT là gì?",
        "Học phí PTIT năm học 2026–2027 khoảng bao nhiêu?",
        "Năm 2026 PTIT có những phương thức xét tuyển nào?",
    ]

    selected_prompt = None
    if not st.session_state.messages:
        st.markdown("**Gợi ý tra cứu**")
        columns = st.columns(2, gap="small")
        for index, suggestion in enumerate(suggestions):
            with columns[index % 2]:
                if st.button(suggestion, key=f"suggestion_{index}", width="stretch"):
                    selected_prompt = suggestion

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                show_sources(message["sources"])

    question = st.chat_input("Nhập câu hỏi về PTIT...") or selected_prompt
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Đang tra cứu website chính thức và tài liệu PTIT..."):
            try:
                rag_chain = get_rag_chain()
                result = answer_question(question, chain=rag_chain)
                st.markdown(result["answer"])
                if result["sources"]:
                    show_sources(result["sources"])
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["sources"],
                    }
                )
            except Exception as error:
                error_message = explain_error(error)
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message, "sources": []}
                )
