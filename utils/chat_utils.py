import streamlit as st
import json
import time
from api import local_model, gemini, cloudflare, cohere, openrouter, groq

def update_key(module):
    """Update uploader keys to reset the file upload widget"""
    if module == "chat":
        st.session_state.chat_uploader_key += 1
    if module == "pdf":
        st.session_state.pdf_uploader_key += 1

def get_text_to_text(progress_bar=None, message_placeholder=None):
    """Get response from the selected model API"""

    message = st.session_state.messages

    if message_placeholder:
        if st.session_state.model_provider == "Local Model":
            return local_model.get_response(message, progress_bar, message_placeholder)
        elif st.session_state.model_provider == "Google Gemini":
            return gemini.get_response(message, progress_bar)
        elif st.session_state.model_provider == "Cloudflare Workers AI":
            return cloudflare.get_response(message, progress_bar, message_placeholder)
        elif st.session_state.model_provider == "Cohere":
            return cohere.get_response(message, progress_bar)
        elif st.session_state.model_provider == "OpenRouter":
            return openrouter.get_response(message, progress_bar)
        elif st.session_state.model_provider == "Groq":
            return groq.get_response(message, progress_bar)
        else:
            st.error(f"Unknown model provider: {st.session_state.model_provider}")
            return None
    else:
        # Choose model provider based on session state
        if st.session_state.model_provider == "Local Model":
            return local_model.get_response(message, progress_bar)
        elif st.session_state.model_provider == "Google Gemini":
            return gemini.get_response(message, progress_bar)
        elif st.session_state.model_provider == "Cloudflare Workers AI":
            return cloudflare.get_response(message, progress_bar)
        elif st.session_state.model_provider == "Cohere":
            return cohere.get_response(message, progress_bar)
        elif st.session_state.model_provider == "OpenRouter":
            return openrouter.get_response(message, progress_bar)
        elif st.session_state.model_provider == "Groq":
            return groq.get_response(message, progress_bar)
        else:
            st.error(f"Unknown model provider: {st.session_state.model_provider}")
            return None

def export_conversations():
    """Export conversation history to JSON"""
    export_data = json.dumps(st.session_state.messages)
    return export_data

def import_conversations(uploaded_file):
    """Import conversation history from JSON"""
    json_file = json.load(uploaded_file)
    st.session_state.messages = json_file
