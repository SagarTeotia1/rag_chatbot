"""RAG chatbot: retrieve context + generate answer via Groq."""
import sys
from pathlib import Path

from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import GROQ_API_KEY, CHAT_MODEL
from src.retrieval.retriever import retrieve

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


SYSTEM_PROMPT = """You are Pandit Shri Rameshwar Das Ji — a wise, warm, and experienced Vedic astrologer who has spent decades studying Jyotish Shastra and dosh remedies.

Your character:
- Speak like a caring, loving pandit — not a robot
- Use warm Hindi phrases like "beta", "putri", "chinta mat karo", "Ishwar ki kripa hai"
- If someone greets ("kese ho", "namaste", "hello", "hi") — respond warmly as Pandit Ji, briefly, then invite them to share their problem
- Show genuine compassion — the person is struggling

Answer rules:
- ONLY give remedies that appear in the retrieved passages provided
- Do NOT fabricate mantras, rituals, or yantras not present in the passages
- Never say "book says" or "according to context" or mention page numbers
- Always answer in Hindi (even if asked in English or Hinglish)
- For greetings: respond warmly in 1-2 lines only, invite them to share their problem. DO NOT give any remedies.
- For remedy/astrology questions: 1 warm empathy line → numbered remedies (heading + how to do) → 1 closing blessing
- If no relevant passages found for a remedy question: "Beta, is vishay mein mujhe aur jaankari chahiye. Thoda aur detail mein batao apni samasya."
- NEVER show or mention page numbers"""


def _translate_to_hindi(text: str) -> str:
    """Translate Romanized Hindi / English query to Hindi for better retrieval."""
    client = _get_client()
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Translate the following query to Hindi (Devanagari script). Output ONLY the Hindi translation, nothing else.",
            },
            {"role": "user", "content": text},
        ],
        temperature=0,
        max_tokens=100,
    )
    return resp.choices[0].message.content or text


def build_context_string(hits: list[dict]) -> str:
    if not hits:
        return ""
    parts = []
    for hit in hits:
        parts.append(f"[Page {hit['page']}]\n{hit['text']}")
    return "\n\n---\n\n".join(parts)


GREETINGS = {
    "hello", "hi", "hey", "namaste", "namaskar", "pranam",
    "kese ho", "kaise ho", "kaisa ho", "keso ho", "kesho ho",
    "how are you", "aap kese hain", "aap kaisa hai",
    "good morning", "good evening", "good night", "hii", "helo",
}

def _is_greeting(text: str) -> bool:
    cleaned = text.strip().lower().rstrip("?!.")
    return cleaned in GREETINGS or len(cleaned.split()) <= 4 and any(
        g in cleaned for g in ["kese", "kaise", "hello", "hi ", "namaste", "namaskar"]
    )


def ask(
    question: str,
    chat_history: list[dict] | None = None,
    top_k: int = 8,
    stream: bool = False,
) -> str:
    """
    Full RAG pipeline: detect greeting → skip retrieval OR translate → retrieve → answer.
    """
    client = _get_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if chat_history:
        messages.extend(chat_history[-6:])

    # Greeting: skip retrieval entirely, just respond as Pandit Ji
    if _is_greeting(question):
        messages.append({"role": "user", "content": question})
        resp = client.chat.completions.create(
            model=CHAT_MODEL, messages=messages, temperature=0.8, max_tokens=120,
        )
        return resp.choices[0].message.content or ""

    # Translate to Hindi for better semantic match with Devanagari corpus
    hindi_query = _translate_to_hindi(question)

    # Retrieve with both original + Hindi query, merge results
    hits_orig = retrieve(question, top_k=top_k // 2)
    hits_hindi = retrieve(hindi_query, top_k=top_k)

    # Deduplicate by chunk_id approximation (use text as key)
    seen = set()
    all_hits = []
    for h in hits_hindi + hits_orig:
        key = h["text"][:80]
        if key not in seen:
            seen.add(key)
            all_hits.append(h)

    context = build_context_string(all_hits[:top_k])

    if context:
        user_message = f"""Relevant passages from the Dosh Mukti book:
{context}

User question: {question}

Give practical remedies ONLY from the above passages. Format as numbered list with clear headings. Present as expert guidance, not as quotes."""
    else:
        user_message = f"User question: {question}\n\nNo relevant passages found. Respond accordingly."

    messages.append({"role": "user", "content": user_message})

    if stream:
        response_text = ""
        stream_resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )
        for chunk in stream_resp:
            delta = chunk.choices[0].delta.content or ""
            print(delta, end="", flush=True)
            response_text += delta
        print()
        return response_text
    else:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""


def get_source_pages(question: str, top_k: int = 5) -> list[int]:
    hits = retrieve(question, top_k=top_k)
    return sorted({h["page"] for h in hits})
