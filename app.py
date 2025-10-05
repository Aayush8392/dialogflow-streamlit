import uuid
import streamlit as st
from google.oauth2 import service_account
from google.cloud import dialogflow_v2 as dialogflow

st.set_page_config(page_title="Dialogflow x Streamlit", page_icon="🤖")

# --- Credentials from Streamlit Secrets ---
if "google_service_account" not in st.secrets:
    st.error("Secrets missing. Add [google_service_account] and [dialogflow] in Settings → Secrets.")
    st.stop()

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
st.caption("Type a message or click a suggestion below.")

def extract_chips(query_result):
    """Return a list of suggestion labels from fulfillmentMessages."""
    chips = []

    # 1) Classic Quick Replies
    try:
        for m in query_result.fulfillment_messages:
            if hasattr(m, "quick_replies") and m.quick_replies.quick_replies:
                chips.extend(list(m.quick_replies.quick_replies))
    except Exception:
        pass

    # 2) Dialogflow ES richContent payload (Messenger-style)
    try:
        for m in query_result.fulfillment_messages:
            if hasattr(m, "payload") and m.payload:
                # Convert Struct -> dict safely
                d = {k: m.payload.fields[k].ToPython() for k in m.payload.fields}
                rich = d.get("richContent")
                # richContent is a list of rows (lists of widgets)
                if isinstance(rich, list):
                    for row in rich:
                        if isinstance(row, list):
                            for w in row:
                                t = w.get("type")
                                if t in {"chips", "suggestion"}:
                                    for opt in w.get("options", []):
                                        label = opt.get("text") or opt.get("title")
                                        if label:
                                            chips.append(label)
                                # Some people use "button" with a "text"
                                if t == "button" and w.get("text"):
                                    chips.append(w["text"])
    except Exception:
        pass

    # De-dup & trim
    seen, out = set(), []
    for c in chips:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:8]

def detect_intent(text: str):
    session = sessions_client.session_path(PROJECT_ID, st.session_state.session_id)
    text_input = dialogflow.TextInput(text=text, language_code=LANGUAGE_CODE)
    query_input = dialogflow.QueryInput(text=text_input)
    resp = sessions_client.detect_intent(
        request=dialogflow.DetectIntentRequest(session=session, query_input=query_input)
    )
    qr = resp.query_result
    bot_text = (qr.fulfillment_text or "").strip() or "_(No text response)_"
    chips = extract_chips(qr)
    return bot_text, chips

# --- Chat state ---
if "history" not in st.session_state:
    st.session_state.history = [{"role": "assistant", "text": "Hi! How can I help?", "chips": []}]
if "pending_send" not in st.session_state:
    st.session_state.pending_send = None

# Render history
for idx, m in enumerate(st.session_state.history):
    with st.chat_message(m["role"]):
        st.markdown(m["text"])
        if m["role"] == "assistant" and m.get("chips"):
            cols = st.columns(len(m["chips"]))
            for i, c in enumerate(m["chips"]):
                if cols[i].button(c, key=f"chip-{idx}-{i}"):
                    st.session_state.pending_send = c
                    st.rerun()

# Input (also fires when a chip was clicked)
user_text = st.chat_input("Type your message…")
if user_text is None and st.session_state.pending_send:
    user_text = st.session_state.pending_send
    st.session_state.pending_send = None

if user_text:
    st.session_state.history.append({"role": "user", "text": user_text, "chips": []})
    with st.chat_message("user"):
        st.markdown(user_text)

    bot_text, chips = detect_intent(user_text)
    st.session_state.history.append({"role": "assistant", "text": bot_text, "chips": chips})
    with st.chat_message("assistant"):
        st.markdown(bot_text)
        if chips:
            cols = st.columns(len(chips))
            for i, c in enumerate(chips):
                if cols[i].button(c, key=f"chip-bottom-{i}"):
                    st.session_state.pending_send = c
                    st.rerun()
