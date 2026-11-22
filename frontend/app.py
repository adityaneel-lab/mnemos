
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="RecallAI",
    page_icon="🧠",
)

st.title("🧠 RecallAI")
st.caption("Context-aware AI with real memory")


def edit_memory_form(memory):
    memory_id = memory["id"]

    with st.form(key=f"edit_form_{memory_id}"):
        new_text = st.text_area(
            "Memory",
            value=memory["text"],
        )

        new_category = st.text_input(
            "Category",
            value=memory.get("category", "general"),
        )

        submitted = st.form_submit_button("Save changes")

        if submitted:
            if not new_text.strip():
                st.error("Memory cannot be empty.")
                return

            try:
                response = requests.put(
                    f"{API_URL}/memories/{memory_id}",
                    json={
                        "text": new_text,
                        "category": new_category,
                    },
                    timeout=10,
                )
                response.raise_for_status()

                st.success("Memory updated!")
                st.session_state.edit_memory_id = None
                st.rerun()

            except requests.RequestException as e:
                st.error(f"Update failed: {e}")


# Fetch saved conversations
try:
    response = requests.get(
        f"{API_URL}/conversations",
        timeout=10,
    )
    response.raise_for_status()
    conversations = response.json()
except requests.RequestException as e:
    st.error(f"Cannot connect to backend: {e}")
    st.stop()

# Initialize selected conversation
conversation_ids = [c["id"] for c in conversations]

if (
    "selected_conversation_id" not in st.session_state
    or st.session_state.selected_conversation_id not in conversation_ids
):
    st.session_state.selected_conversation_id = (
        conversation_ids[0] if conversation_ids else None
    )

# Sidebar
with st.sidebar:
    st.header("Your conversations")

    if st.button("➕ New conversation", use_container_width=True):
        try:
            response = requests.post(
                f"{API_URL}/conversations",
                timeout=10,
            )
            response.raise_for_status()

            new_id = response.json()["id"]
            st.session_state.selected_conversation_id = new_id
            st.rerun()

        except requests.RequestException as e:
            st.error(f"Could not create conversation: {e}")

    if conversations:
        selected_id = st.selectbox(
            "Choose a conversation",
            options=conversation_ids,
            index=conversation_ids.index(
                st.session_state.selected_conversation_id
            ),
            format_func=lambda cid: next(
                c["title"] for c in conversations
                if c["id"] == cid
            ),
        )

        st.session_state.selected_conversation_id = selected_id

        st.divider()

        st.header("🧠 Your memories")

        if st.button("🔄 Refresh memories", use_container_width=True):
            st.rerun()

        try:
            memory_response = requests.get(
                f"{API_URL}/memories",
                timeout=10,
            )
            memory_response.raise_for_status()
            memories = memory_response.json()

            if memories:
                st.caption(f"{len(memories)} saved memories")

                ####
                # Group memories by category
                grouped_memories = {}

                for memory in memories:
                    category = memory.get("category", "general")
                    grouped_memories.setdefault(category, []).append(memory)

                categories = ["All"] + sorted(grouped_memories.keys())

                selected_category = st.selectbox(
                    "Filter by category",
                    categories,
                )

                # Display each category
                for category, category_memories in grouped_memories.items():
                    if selected_category != "All" and category != selected_category:
                        continue

                    with st.expander(
                        f"{category.replace('_', ' ').title()} "
                        f"({len(category_memories)})",
                        expanded=True,
                    ):
                        for memory in category_memories:
                            with st.container(border=True):
                                st.write(memory["text"])

                                # Keep your existing Edit functionality here
                                if st.button("✏️ Edit", key=f"edit_{memory['id']}"):
                                    st.session_state.edit_memory_id = memory["id"]
                                    st.rerun()

                                if st.session_state.get("edit_memory_id") == memory["id"]:
                                    edit_memory_form(memory)

                                if st.button("🗑️ Delete", key=f"delete_memory_{memory['id']}",use_container_width=True):
                                    try:
                                        delete_response = requests.delete(
                                            f"{API_URL}/memories/{memory['id']}",
                                            timeout=10,
                                        )
                                        delete_response.raise_for_status()
                                        st.success("Memory deleted!")
                                        st.rerun()

                                    except requests.RequestException as e:
                                        st.error(f"Could not delete memory: {e}")

            else:
                st.info("No saved memories yet.")

        except requests.RequestException as e:
            st.error(f"Could not load memories: {e}")


# Create the first conversation if none exists
if st.session_state.selected_conversation_id is None:
    try:
        response = requests.post(
            f"{API_URL}/conversations",
            timeout=10,
        )
        response.raise_for_status()
        st.session_state.selected_conversation_id = (
            response.json()["id"]
        )
        st.rerun()
    except requests.RequestException as e:
        st.error(f"Could not create conversation: {e}")
        st.stop()

conversation_id = st.session_state.selected_conversation_id

# Load messages from SQLite through FastAPI
try:
    response = requests.get(
        f"{API_URL}/conversations/{conversation_id}/messages",
        timeout=10,
    )
    response.raise_for_status()
    messages = response.json()
except requests.RequestException as e:
    st.error(f"Could not load conversation: {e}")
    st.stop()

# Display saved history
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask me anything...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "conversation_id": conversation_id,
                        "message": prompt,
                    },
                    timeout=600,
                )
                response.raise_for_status()

                reply = response.json()["reply"]
                st.markdown(reply)

            except requests.RequestException as e:
                st.error(f"Chat request failed: {e}")

    # Refresh to load the saved messages and updated title
    st.rerun()
