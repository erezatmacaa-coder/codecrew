import os, sys
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.getenv("MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "1"))
MAX_AGENT_INTERNAL = int(os.getenv("MAX_AGENT_INTERNAL", "10"))

# Fix Windows Turkish locale encoding
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

if not API_KEY:
    raise ValueError(
        "API_KEY is not set. "
        "Get a free key at: https://console.groq.com/keys"
    )
