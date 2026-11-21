
import tiktoken

# A configurable budget for conversation messages.
MAX_CONTEXT_TOKENS = 500

SYSTEM_PROMPT = """
You are RecallAI, a helpful conversational assistant.
Answer clearly and concisely.
Use the conversation history to understand the user's context.
"""

# Initialize a tokenizer.
try:
    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:
    tokenizer = None


def count_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string."""

    if tokenizer is None:
        # Rough fallback estimate.
        return max(1, len(text) // 4)

    return len(tokenizer.encode(text))


def build_context(history: list[dict]) -> dict:
    """
    Build a context containing the system prompt
    and the most recent messages within the token budget.
    """

    system_tokens = count_tokens(SYSTEM_PROMPT)

    remaining_budget = MAX_CONTEXT_TOKENS - system_tokens

    selected_messages = []
    used_tokens = 0

    # Work backwards, starting with the newest message.
    for message in reversed(history):

        message_tokens = (
            count_tokens(message["content"]) + 4
        )

        if used_tokens + message_tokens > remaining_budget:
            break

        selected_messages.append(message)
        used_tokens += message_tokens

    # Restore chronological order.
    selected_messages.reverse()

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    messages.extend(selected_messages)

    return {
        "messages": messages,
        "token_count": system_tokens + used_tokens,
        "message_count": len(selected_messages),
    }
