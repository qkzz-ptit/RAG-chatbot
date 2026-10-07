# PTIT AI Chatbot

Trợ lý hỏi đáp PTIT bằng tiếng Việt. Ứng dụng tìm bằng chứng trong PDF và cẩm nang Markdown, rồi dùng Gemini để tạo câu trả lời có căn cứ. Đây là RAG (tra cứu tài liệu lúc trả lời), không phải huấn luyện lại mô hình Gemini.

## Cấu trúc

```text
.
├── README.md
├── .gitignore
├── app.py
├── main.py
├── requirements.txt
├── .env.example
├── .streamlit/config.toml
├── scripts/
│   └── run_web.bat
├── data/
│   ├── documents/       # PDF gốc của Học viện
│   └── knowledge/       # Cẩm nang Markdown được nạp vào chỉ mục
└── ptit_chatbot/
    ├── config.py        # Đường dẫn dự án và .env
    ├── rag.py           # Nạp tài liệu, FAISS, Gemini và nguồn trích dẫn
    ├── web_search.py    # Tra cứu thời gian thực trên website PTIT
    ├── query.py         # Mở rộng viết tắt và chuẩn hóa câu hỏi
    ├── web.py           # Giao diện chat thích ứng cho máy tính/điện thoại
    └── cli.py           # Giao diện terminal
```

## Cài đặt và chạy

Tạo môi trường Python và cài các thư viện đã ghim phiên bản:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Điền `GOOGLE_API_KEY` vào `.env`. Mô hình mặc định là `gemini-3.5-flash-lite`; nếu quá tải, ứng dụng lần lượt thử `gemini-3.7-flash` và `gemini-3.8-flash`. Có thể đặt `PTIT_CHAT_MODEL` và danh sách dự phòng `PTIT_CHAT_MODEL_FALLBACKS` trong `.env`.

- Web: `streamlit run app.py` hoặc chạy `scripts\run_web.bat` trên Windows
- Terminal: `python main.py`
