import streamlit as st
import requests
from os import getenv
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()

# Set up API Credentials
API_KEY = getenv("GROQ_API_KEY")
ACCOUNT_ID = getenv("CLOUDFLARE_ACCOUNT_ID")
GATEWAY_ID = getenv("CLOUDLFARE_AI_GATEWAY_GATEWAY_ID")
base_url = f"https://gateway.ai.cloudflare.com/v1/{ACCOUNT_ID}/{GATEWAY_ID}/groq/chat/completions"

# Available Groq models
models = {
    "Llama 4 Maverick 17B 128E Instruct": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "Llama 4 Scout 17B 16E Instruct": "meta-llama/llama-4-scout-17b-16e-instruct",
    "Gemma 2 9B Instruct": "gemma2-9b-it",
    "Llama 3.3 70B Versatile": "llama-3.3-70b-versatile",
    "Llama 3.1 8B Instant": "llama-3.1-8b-instant",
    "Llama 3 70B 8192": "llama3-70b-8192",
    "Llama 3 8B 8192": "llama3-8b-8192",
    "Deepseek R1 Distill Llama 70B": "deepseek-r1-distill-llama-70b",
    "Mistral Saba 24B": "mistral-saba-24b",
    "Qwen QWQ 32B": "qwen-qwq-32b"
}

def get_response(message, progress_bar, message_placeholder=None):
    """Get response from Cloudflare Workers AI API"""

    if "enable_streaming" in st.session_state and st.session_state.enable_streaming:
        return get_response_streaming(message, progress_bar, message_placeholder)

    model = models[st.session_state.groq_model]

    messages = [{"role": msg['role'], "content": msg['content']} for msg in message]

    progress_bar.progress(50, "Sending request to Groq API...")

    response = requests.post(
        url=base_url,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "messages": messages,
            "max_tokens": st.session_state.max_tokens,
            "temperature": st.session_state.temperature,
            "model": model
        }
    )
    
    progress_bar.progress(90, "Response received, processing...")

    if response.status_code == 200:
        response_data = response.json()

        assistant_message = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
        st.session_state.usage_info = {
            'prompt_tokens': response_data['usage']['prompt_tokens'],
            'completion_tokens': response_data['usage']['completion_tokens'],
            'total_tokens': response_data['usage']['total_tokens']
        }
        
        st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': "Groq " + st.session_state.groq_model})
        
        progress_bar.progress(100, "Response processed successfully.")
        time.sleep(1)
        progress_bar.empty()

        return assistant_message
    else:
        st.error(f"Error from Groq API: {response.status_code} - {response.text}")
        progress_bar.empty()
        return None
    
def get_response_streaming(message, progress_bar, message_placeholder):
    """Get streaming response from Groq API"""
    model = models[st.session_state.groq_model]

    messages = [{"role": msg['role'], "content": msg['content']} for msg in message]

    progress_bar.progress(50, "Sending request to Groq API...")

    response = requests.post(
        url=base_url,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "messages": messages,
            "max_tokens": st.session_state.max_tokens,
            "temperature": st.session_state.temperature,
            "model": model,
            "stream": True
        },
        stream=True
    )
    
    progress_bar.progress(90, "Response received, processing...")

    if response.status_code == 200:
        assistant_message = ""
        for chunk in response.iter_lines():
            if chunk:
                chunk_data = chunk.decode('utf-8')
                if 'data: ' in chunk_data:
                    data = chunk_data.split('data: ')[1]
                    if data == '[DONE]':
                        break
                    else:
                        try:
                            json_data = json.loads(data)
                            content = json_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            if content:
                                assistant_message += content
                                message_placeholder.markdown(assistant_message + "▌")
                        except json.JSONDecodeError:
                            pass

        st.session_state.usage_info = {
            'prompt_tokens': "",
            'completion_tokens': "",
            'total_tokens': ""
        }
        
        st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': "Groq " + st.session_state.groq_model})
        
        progress_bar.progress(100, "Response processed successfully.")
        time.sleep(1)
        progress_bar.empty()

        return assistant_message
    else:
        st.error(f"Error from Groq API: {response.status_code} - {response.text}")
        progress_bar.empty()
        return None