import streamlit as st
import cohere
from os import getenv
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Set up API credentials
ACCOUNT_ID = getenv("CLOUDFLARE_ACCOUNT_ID")
GATEWAY_ID = getenv("CLOUDLFARE_AI_GATEWAY_GATEWAY_ID")
base_url=f"https://gateway.ai.cloudflare.com/v1/{ACCOUNT_ID}/{GATEWAY_ID}/cohere"

# Set up Cohere API client
co = cohere.ClientV2(
    api_key=getenv("COHERE_API_KEY"),
    base_url=base_url
)

# Available Cohere models
models = {
    "Command A": "command-a-03-2025",
    "Command R 7B": "command-r7b-12-2024",
    "Command R+": "command-r-plus",
    "Command R": "command-r",
    "Command": "command",
    "Command Nightly": "command-nightly",
    "Command Light": "command-light",
    "Command Light Nightly": "command-light-nightly"
}

def get_response(message, progress_bar):
    """Get response from Cohere API"""
    model = models[st.session_state.cohere_model]

    messages = [{"role": msg['role'], "content": msg['content']} for msg in message]
    
    if st.session_state.max_tokens > 4096:
        st.warning("Cohere models' max tokens are 4096. Setting to 4096.")
        st.session_state.max_tokens = 4096

    progress_bar.progress(50, "Sending request to Cohere...")

    response = co.chat(
        model=model,
        messages=messages,
        max_tokens=st.session_state.max_tokens,
        temperature=st.session_state.temperature
    )
    
    progress_bar.progress(90, "Response received, processing...")
    
    assistant_message = response.message.content[0].text
    st.session_state.usage_info = {
            'prompt_tokens': response.usage.tokens.input_tokens,
            'completion_tokens': response.usage.tokens.output_tokens,
            'total_tokens': response.usage.tokens.input_tokens + response.usage.tokens.output_tokens
        }
    
    st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': "Cohere " + st.session_state.cohere_model})
    
    progress_bar.progress(100, "Response processed successfully.")
    time.sleep(1)
    progress_bar.empty()

    return assistant_message