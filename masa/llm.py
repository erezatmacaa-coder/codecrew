import time
from openai import OpenAI, RateLimitError
from . import config

client = OpenAI(
    api_key=config.API_KEY,
    base_url=config.BASE_URL,
)


def chat(messages, tools=None, retries=3):
    kwargs = {
        "model": config.MODEL,
        "messages": messages,
        "max_tokens": config.MAX_TOKENS,
    }
    if tools:
        kwargs["tools"] = tools

    last_error = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except RateLimitError as e:
            last_error = e
            wait = min(2 ** attempt * 2, 30)
            print(f"[Rate limit, {wait}s bekleniyor...]")
            time.sleep(wait)
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                wait = 1
                time.sleep(wait)
            else:
                raise last_error

    raise last_error
