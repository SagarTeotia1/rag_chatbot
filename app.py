"""
CLI chat interface for Dosh Mukti RAG chatbot.

Usage:
  python app.py

Commands during chat:
  /quit or /exit  - exit
  /sources        - show source pages for last query
  /clear          - clear chat history
  /help           - show commands
"""
import io
import os
import sys
from pathlib import Path

# Force UTF-8 on Windows console
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    ctypes.windll.kernel32.SetConsoleCP(65001)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from config import GROQ_API_KEY, CHROMA_DIR, COLLECTION_NAME
from src.chat.chatbot import ask, get_source_pages
from src.ingestion.embedder import get_chroma_collection


def check_ready() -> bool:
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set. Add it to .env file.")
        return False
    try:
        col = get_chroma_collection()
        count = col.count()
        if count == 0:
            print("ERROR: Knowledge base is empty. Run `python ingest.py` first.")
            return False
        print(f"Knowledge base ready: {count} chunks loaded.")
        return True
    except Exception as e:
        print(f"ERROR: Could not connect to ChromaDB: {e}")
        print("Run `python ingest.py` first.")
        return False


BANNER = """
=================================================
   Dosh Mukti Book - AI Chatbot (RAG)
   Dosh Mukti Pustak - AI Sahayak
=================================================
  /sources - show source pages
  /clear   - clear chat history
  /quit    - exit
=================================================
"""


def main():
    print(BANNER)

    if not check_ready():
        sys.exit(1)

    chat_history: list[dict] = []
    last_question: str | None = None

    print("\nAsk your questions (Hindi or English):\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            print("Goodbye!")
            break

        if user_input.lower() == "/clear":
            chat_history.clear()
            last_question = None
            print("[Chat history cleared]\n")
            continue

        if user_input.lower() == "/help":
            print("/sources, /clear, /quit\n")
            continue

        if user_input.lower() == "/sources":
            if last_question:
                pages = get_source_pages(last_question)
                print(f"Source pages: {pages}\n")
            else:
                print("No previous question.\n")
            continue

        last_question = user_input
        print("\nAssistant: ", flush=True)

        response = ask(user_input, chat_history=chat_history, stream=False)

        print(response)
        print()

        # Also save to file in case terminal can't render Hindi
        with open("last_response.txt", "w", encoding="utf-8") as f:
            f.write(f"Q: {user_input}\n\nA: {response}\n")

        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
