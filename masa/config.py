import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.getenv("MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "3"))
MAX_AGENT_INTERNAL = int(os.getenv("MAX_AGENT_INTERNAL", "10"))

if not API_KEY:
    raise ValueError(
        "API_KEY is not set. "
        "Get a free Groq API key at: https://console.groq.com/keys"
    )
