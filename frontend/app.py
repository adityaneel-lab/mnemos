
import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(
    page_title="Real Memory Chatbot",
    page_icon="🧠"
)

st.title("🧠 Real Memory Chatbot")
st.caption("Day 1 - Basic conversational AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask me anything...")

if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Model is generating response..."):

            try:
                start = time.time()

                response = requests.post(
                    API_URL,
                    json={
                        "messages": st.session_state.messages
                    },
                    timeout=600
                )

                response.raise_for_status()

                reply = response.json()["reply"]

                st.markdown(reply)

                st.caption(
                    f"Response time: {time.time() - start:.2f}s"
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply
                })

            except requests.exceptions.Timeout:
                st.error("Request timed out. Check Ollama and FastAPI.")

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to FastAPI.")

            except requests.exceptions.RequestException as e:
                st.error(f"API error: {e}")
