import json
from ollama import chat
from pathlib import Path
from backend.config import USER_ID, MODEL_NAME

from backend.long_term_memory import (
    save_memory,
    get_all_memories,
    update_memory,
)

PROMPT_PATH = (
    Path(__file__).parent / "prompts" / "memory_extraction.txt"
)


def load_memory_prompt(
    existing_memories_json: str,
    user_message: str,
):
    template = PROMPT_PATH.read_text(encoding="utf-8")

    return template.format(
        existing_memories_json=existing_memories_json,
        user_message=user_message,
    )


def extract_and_save_memories(user_message: str):
    """
    Extract explicit facts from a user message
    and save them to long-term memory.
    """

    existing_memories = get_all_memories(user_id=USER_ID)
    existing_memories_json = json.dumps(existing_memories,indent=2)

    prompt = load_memory_prompt(
        existing_memories_json=existing_memories_json,
        user_message=user_message,
    )

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
        actions = result.get("actions", [])
        saved = []

        existing_ids = {
            memory["id"] for memory in existing_memories
        }

        allowed_categories = {
            "profession",
            "skill",
            "interest",
            "learning_goal",
            "preference",
            "project",
            "general",
        }

        for item in actions:
            if not isinstance(item, dict):
                continue

            action = item.get("action")
            text = item.get("text", "")
            category = item.get("category", "general")
            memory_id = item.get("memory_id")

            if not isinstance(text, str) or not text.strip():
                continue

            if not isinstance(category, str):
                category = "general"

            text = text.strip()
            category = category.strip().lower()

            if category not in allowed_categories:
                category = "general"

            if action == "add":
                save_memory(
                    text=text,
                    user_id=USER_ID,
                    category=category,
                )
                saved.append(text)

            elif action == "update" and memory_id in existing_ids:
                updated = update_memory(
                    memory_id=memory_id,
                    text=text,
                    user_id=USER_ID,
                    category=category,
                )

                if updated:
                    saved.append(text)

        return saved

    except (json.JSONDecodeError, TypeError, AttributeError):
        print("Memory extraction returned invalid JSON.")
        return []

    except Exception as error:
        print(f"Memory extraction failed: {error}")
        return []
