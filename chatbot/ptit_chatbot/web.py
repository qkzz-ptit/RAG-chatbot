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
        :root { --ptit-navy: #102a43; --ptit-blue: #1769aa; --ptit-red: #c73e4d; }
        .stApp { background: linear-gradient(180deg, #f5f8fc 0%, #ffffff 38rem); }
        [data-testid="stHeader"] { background: rgba(255,255,255,.82); }
        [data-testid="stMainBlockContainer"] { max-width: 860px; padding-top: 2rem; padding-bottom: 7rem; }
        [data-testid="stChatMessage"] { border-radius: 18px; padding: .7rem 1rem; }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { line-height: 1.7; }
        [data-testid="stChatInput"] { border-radius: 18px; box-shadow: 0 8px 30px rgba(16,42,67,.10); }
        [data-testid="stSidebar"] { background: #f2f6fb; }
        .ptit-eyebrow { color: var(--ptit-blue); font-size: .78rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
        .ptit-subtitle { color: #526579; font-size: 1.03rem; line-height: 1.65; max-width: 650px; }
        @media (max-width: 640px) {
          [data-testid="stMainBlockContainer"] { padding: 1.15rem .85rem 6rem; }
          [data-testid="stChatMessage"] { padding: .45rem .72rem; border-radius: 15px; }
          h1 { font-size: 1.75rem !important; line-height: 1.2 !important; }
          .ptit-subtitle { font-size: .94rem; }
          [data-testid="stChatInput"] textarea { font-size: 16px !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.markdown("### 🎓 Trợ lý PTIT")
        st.caption("Tra cứu trực tiếp cổng PTIT, kết hợp tài liệu của Học viện.")
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
    st.title("Xin chào! Mình có thể giúp gì?")
    st.markdown(
        '<div class="ptit-subtitle">Hỏi về tuyển sinh, điểm chuẩn, học phí, ngành học và các thông tin mới trên website PTIT. Chatbot cũng hiểu các viết tắt phổ biến.</div>',
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
        st.markdown("**Bạn có thể bắt đầu với một câu hỏi**")
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
