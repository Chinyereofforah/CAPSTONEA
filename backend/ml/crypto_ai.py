import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)


def ask_crypto_ai(question: str):

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional DeFi risk analyst. "
                    "You analyze wallets, liquidity, DEX activity, and rug-pull signals. "
                    "You do not hallucinate numbers."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content