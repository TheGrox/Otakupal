# services/groq_service.py (improved for multi-turn memory)
from groq import Groq
from config import Config

print("DEBUG: GROQ_API_KEY in groq_service.py:", Config.GROQ_API_KEY)

client = Groq(api_key=Config.GROQ_API_KEY)

SYSTEM_PROMPT = """
You are OtakuPal, an expert anime assistant. Follow these rules:
1. For anime & manga related stuff (plots, characters, staff, ratings) use Jikan API data when available.
2. Be conversational and friendly.
3. Always remember the conversation history and maintain context across multiple turns.
5. If you don't know the answer, say "I don't know" instead of making up information.
6. If the user asks for an opinion, give the common consensus from the anime community.
7. Keep answers concise but allow for deeper exploration if the user asks follow-ups.
8. Always stay consistent with previous parts of the conversation.
9. Use bullet points, markdown, and code blocks to format your responses nicely.
10. if you don't understand the question sk for more details.
11. if the user ask for something irrelevant just tell them you are an anime assistant and can't help with that.
"""

def get_llama_response(messages):
    # Ensure we don't overload the model with too much history
    MAX_HISTORY = 15  # keep last 15 messages for context
    if len(messages) > MAX_HISTORY:
        messages = messages[-MAX_HISTORY:]

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        temperature=0.7,
        max_tokens=1024
    )
    return response.choices[0].message.content