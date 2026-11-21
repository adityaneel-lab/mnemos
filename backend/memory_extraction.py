
import json
from ollama import chat

from backend.long_term_memory import save_memory

MODEL_NAME = "qwen3.5:0.8b"


def extract_and_save_memories(
    user_message: str,
    user_id: str = "default",
):
    """
    Extract explicit facts from a user message
    and save them to long-term memory.
    """

    prompt = f"""
Extract useful facts explicitly stated by the user.

Only remember stable information that may help in
future conversations, such as:
- Name
- Profession
- Skills
- Interests
- Learning goals
- Preferences
- Ongoing projects

Do not invent facts or make assumptions.
Do not extract temporary or irrelevant details.
Do not extract sensitive personal information.

Return valid JSON in exactly this structure:

{{
  "memories": [
    {{
      "text": "The user is learning Python",
      "category": "learning_goal"
    }}
  ]
}}

If there are no useful facts, return:
{{"memories": []}}

User message:
{user_message}
"""

    try:
        response = chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format="json",
            think=False,
            options={
                "temperature": 0
            }
        )

        raw_response = response.message.content

        result = json.loads(raw_response)

        memories = result.get("memories", [])

        saved = []

        for memory in memories:
            text = memory.get("text", "").strip()
            category = memory.get("category", "general")

            if text:
                save_memory(
                    text=text,
                    user_id=user_id,
                    category=category,
                )
                saved.append(text)

        return saved

    except (json.JSONDecodeError, TypeError, AttributeError):
        print("Memory extraction returned invalid JSON.")
        return []

    except Exception as error:
        print(f"Memory extraction failed: {error}")
        return []
