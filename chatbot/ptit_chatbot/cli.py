from . import config as _config
from .rag import answer_question


def main() -> None:
    print("\nCHATBOT PTIT SẴN SÀNG")
    try:
        
        from .rag import build_rag_chain

        rag_chain = build_rag_chain()
    except Exception as error:
        print(f"Không thể khởi động chatbot: {error}")
        return

    while True:
        question = input("\nCâu hỏi (nhập 'q' để thoát): ").strip()
        if question.lower() == "q":
            break
        if not question:
            continue

        print("Đang suy nghĩ...")
        try:
            result = answer_question(question, chain=rag_chain)
            print(result["answer"])
            if result["sources"]:
                print("\nNguồn: " + "; ".join(
                    f"{source['name']}" + (f", trang {source['page']}" if source["page"] else "")
                    for source in result["sources"]
                ))
        except Exception as error:
            print(f"Không thể trả lời câu hỏi: {error}")


if __name__ == "__main__":
    main()
