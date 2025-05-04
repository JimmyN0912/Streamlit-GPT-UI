import streamlit as st
import time
from os import getenv
from dotenv import load_dotenv
from openai import OpenAI

# Initialize environment
load_dotenv()

# Available Gemini models
models = {
    "Gemini 2.5 Pro Experimental": "gemini-2.5-pro-exp-03-25",
    "Gemini 2.5 Flash Preview 04-17": "gemini-2.5-flash-preview-04-17",
    "Gemini 2.0 Flash": "gemini-2.0-flash",
    "Gemini 2.0 Flash-Lite": "gemini-2.0-flash-lite", 
    "Gemini 1.5 Flash": "gemini-1.5-flash", 
    "Gemini 1.5 Flash-8B": "gemini-1.5-flash-8b", 
    "Gemini 1.5 Pro": "gemini-1.5-pro"
}

# Initialize OpenAI client with Google Gemini base URL
client = OpenAI(
    api_key=getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def get_response_stream(message, progress_bar):
    """Get response from Google Gemini API"""
    try:
        model_name = models[st.session_state.gemini_model]

        progress_bar.progress(50, "Sending request to Gemini API...")
        
        messages = [{"role": msg['role'], "content": msg['content']} for msg in message]
        
        # For streaming with OpenAI client
        assistant_message = ""
        response_placeholder = st.empty()
        
        # Make the streaming request
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                assistant_message += content
                response_placeholder.markdown(assistant_message + "▌")
        
        response_placeholder.empty()
        
        progress_bar.progress(90, "Response received, processing...")
        model_display_name = f"Google {model_name}"
        
        # Set usage info
        st.session_state.usage_info = {
            'prompt_tokens': "N/A (streaming)",
            'completion_tokens': "N/A (streaming)",
            'total_tokens': "N/A (streaming)"
        }
        
        st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': model_display_name})

        progress_bar.progress(1.0, "Response processed successfully.")
        time.sleep(1)
        progress_bar.empty()        
        return assistant_message

    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        print(f"Error with Gemini API: {str(e)}")
        progress_bar.empty()
        return None

def get_response(message, progress_bar):
    """Get response from Google Gemini API using OpenAI compatibility layer (non-streaming)"""
    try:
        model_name = models[st.session_state.gemini_model]
        messages = [{"role": msg['role'], "content": msg['content']} for msg in message]
        
        progress_bar.progress(50, "Sending request to Gemini API...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            stream=False
        )

        assistant_message = response.choices[0].message.content
        
        progress_bar.progress(90, "Response received, processing...")
        model_display_name = f"Google {model_name}"
        
        st.session_state.usage_info = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': model_display_name})

        progress_bar.progress(100, "Response processed successfully.")
        time.sleep(1)
        progress_bar.empty()        
        return assistant_message

    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        print(f"Error with Gemini API: {str(e)}")
        progress_bar.empty()
        return None