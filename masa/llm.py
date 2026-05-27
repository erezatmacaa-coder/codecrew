from openai import OpenAI
from . import config

client = OpenAI(
    api_key=config.API_KEY,
    base_url=config.BASE_URL,
)

def chat(messages, tools=None):
    kwargs = {
        "model": config.MODEL,
        "messages": messages,
        "max_tokens": config.MAX_TOKENS,
    }
    if tools:
        kwargs["tools"] = tools
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message
