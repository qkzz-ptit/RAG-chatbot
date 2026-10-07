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

## Bổ sung kiến thức PTIT

Thêm file `.md` tiếng Việt vào `data/knowledge/` hoặc PDF vào `data/documents/`. Ghi rõ mốc năm cho học phí, tuyển sinh, chỉ tiêu và điểm; ưu tiên văn bản/link chính thức của PTIT. Khởi động lại ứng dụng sau khi thêm/sửa tài liệu để tạo lại chỉ mục FAISS và embeddings. Các đoạn tài liệu được gửi lên Google Embeddings theo nhóm tối đa 8 đoạn; việc hỏi đáp cũng gửi câu hỏi và các đoạn trích liên quan đến Google Gemini. Thay đổi nội dung kho hoặc đặt câu hỏi có thể phát sinh lượt gọi Google API.

PDF `PTIT_diem_chuan_PTIT_day_du_2010_2026.pdf` đã được thêm vào kho. Bộ nạp đọc nội dung PDF khi khởi tạo chỉ mục; bảng này là dữ liệu tham khảo tổng hợp, cần đối chiếu nguồn tuyển sinh chính thức khi cần xác nhận.

Thông tin hiện có được tổng hợp trong `data/knowledge/ptit_reference_2026.md`. Đối chiếu cổng PTIT trước khi dùng các thông tin có thể thay đổi như hạn tuyển sinh, điểm chuẩn và học phí.

Mỗi câu hỏi được tra cứu trên `tuyensinh.ptit.edu.vn` và `ptit.edu.vn` qua tìm kiếm WordPress công khai, chỉ lấy một số ít trang khớp và lưu kết quả 10 phút để tránh gọi lặp. Khi REST API tìm kiếm không khả dụng, ứng dụng thử tìm kiếm nội bộ của website. Nếu website không phản hồi, chatbot vẫn dùng kho PDF/Markdown. Câu hỏi được mở rộng các viết tắt PTIT phổ biến (ví dụ `CNTT`, `ATTT`, `HP`, `HB`, `PTXT`, `ĐH`, `ĐGNL`) trước khi tra cứu; câu hỏi gốc vẫn được giữ để Gemini trả lời đúng ý.

`.env`, `.venv`, cache Python và cấu hình IDE là tệp/thư mục cục bộ, không cần đưa vào bản phát hành.
