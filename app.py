import uuid
import streamlit as st
from google.oauth2 import service_account
from google.cloud import dialogflow_v2 as dialogflow

st.set_page_config(page_title="Dialogflow x Streamlit", page_icon="🤖")

# --- Credentials from Streamlit Secrets ---
credentials = service_account.Credentials.from_service_account_info(
    dict(st.secrets["google_service_account"])
)
PROJECT_ID = st.secrets["dialogflow"]["project_id"]
LANGUAGE_CODE = st.secrets["dialogflow"].get("language_code", "en")

sessions_client = dialogflow.SessionsClient(credentials=credentials)

# Keep one Dialogflow session per browser tab
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("🤖 Dialogflow + Streamlit")
st.caption("Type a message below to talk to your Dialogflow ES agent.")

def detect_intent(text: str) -> str:
    session = sessions_client.session_path(PROJECT_ID, st.session_state.session_id)
    text_input = dialogflow.TextInput(text=text, language_code=LANGUAGE_CODE)
    query_input = dialogflow.QueryInput(text=text_input)
    response = sessions_client.detect_intent(
        request=dialogflow.DetectIntentRequest(session=session, query_input=query_input)
    )
    return (response.query_result.fulfillment_text or "").strip() or "_(No text response)_"

# Simple chat UI
if "history" not in st.session_state:
    st.session_state.history = [{"role": "assistant", "text": "Hi! How can I help?"}]

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["text"])

user_text = st.chat_input("Type your message…")
if user_text:
    st.session_state.history.append({"role": "user", "text": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    bot_text = detect_intent(user_text)
    st.session_state.history.append({"role": "assistant", "text": bot_text})
    with st.chat_message("assistant"):
        st.markdown(bot_text)
