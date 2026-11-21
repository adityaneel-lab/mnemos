
from backend.memory import build_context, count_tokens

history = [
    {"role": "user", "content": "My name is Alex."},
    {"role": "assistant", "content": "Nice to meet you, Alex!"},
    {"role": "user", "content": "I am learning Python."},
    {"role": "assistant", "content": "That's great!"},
    {"role": "user", "content": "I want to build AI projects."},
    {"role": "assistant", "content": "Let's build one together."},
    {"role": "user", "content": "What am I learning?"},
]

context = build_context(history)

print("Messages sent to LLM:")
for message in context["messages"]:
    print(message["role"], ":", message["content"])

print("\nToken estimate:", context["token_count"])
print("Messages included:", context["message_count"])
print("Messages in database:", len(history))
