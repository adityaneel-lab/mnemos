
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="RecallAI",
    page_icon="🧠",
)

st.title("🧠 RecallAI")
st.caption("Day 2 — Persistent Conversation History")

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
