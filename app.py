import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="Hunger Bot", page_icon="🍽️")

st.title("🍽️ Hunger Bot – SDG 2 Assistant")
st.markdown("Chat directly with your Dialogflow agent below. All cards, chips, and buttons are supported automatically.")

messenger = """
<script src="https://www.gstatic.com/dialogflow-console/fast/messenger/bootstrap.js?v=1"></script>
<df-messenger
  intent="WELCOME"
  chat-title="HUNGER-BOT"
  agent-id="cdfaaaa5-8dad-4665-883e-bc87fd05b98b"
  language-code="en"
></df-messenger>

<style>
  df-messenger {
    z-index: 999;
    position: fixed;
    bottom: 24px;
    right: 24px;
  }
</style>
"""

html(messenger, height=700)
