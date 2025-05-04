import streamlit as st
import time
from os import getenv
from dotenv import load_dotenv
from openai import OpenAI

# Initialize environment
load_dotenv()

# Available Gemini models with their OpenAI-compatible names
models = {
    "Gemini 2.5 Pro Experimental": "gemini-2.5-pro-exp-03-25",
    "Gemini 2.5 Flash Preview 04-17": "gemini-2.5-flash-preview-04-17",
    "Gemini 2.0 Flash": "gemini-2.0-flash",
    "Gemini 2.0 Flash-Lite": "gemini-2.0-flash-lite", 
    "Gemini 1.5 Flash": "gemini-1.5-flash", 
    "Gemini 1.5 Flash-8B": "gemini-1.5-flash-8b", 
    "Gemini 1.5 Pro": "gemini-1.5-pro"
}

def get_response_stream(message, progress_bar):
    """Get response from Google Gemini API using OpenAI compatibility layer"""
    try:
        # Initialize OpenAI client with Google Gemini base URL
        client = OpenAI(
            api_key=getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        model_name = models[st.session_state.gemini_model]
        progress_bar.progress(0.2, "Sending request to Gemini API...")
        
        # Format messages for OpenAI format
        formatted_messages = []
        for msg in message:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Get response from Gemini API through OpenAI compatibility layer
        start_time = time.time()
        
        progress_bar.progress(0.5, "Processing request...")
        
        # For streaming with OpenAI client
        assistant_message = ""
        response_placeholder = st.empty()
        
        # Make the streaming request
        stream = client.chat.completions.create(
            model=model_name,
            messages=formatted_messages,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                assistant_message += content
                response_placeholder.markdown(assistant_message + "▌")
                # Calculate a progress percentage that stays within bounds
                progress_value = min(0.9, 0.5 + (len(assistant_message) / 2000))
                progress_bar.progress(progress_value, "Receiving response...")
        
        response_placeholder.empty()
        elapsed_time = time.time() - start_time
        
        progress_bar.progress(0.9, "Response received, processing...")
        model_display_name = f"Google {model_name}"
        
        # Set usage info
        st.session_state.usage_info = {
            'prompt_tokens': "N/A (streaming)",
            'completion_tokens': "N/A (streaming)",
            'total_tokens': "N/A (streaming)",
            'elapsed_time': f"{elapsed_time:.2f} seconds"
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
        # Initialize OpenAI client with Google Gemini base URL
        client = OpenAI(
            api_key=getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        model_name = models[st.session_state.gemini_model]
        progress_bar.progress(0.2, "Sending request to Gemini API...")
        
        # Format messages for OpenAI format
        formatted_messages = []
        for msg in message:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Get response from Gemini API through OpenAI compatibility layer
        start_time = time.time()
        
        progress_bar.progress(0.5, "Processing request...")
        
        # Make the non-streaming request
        response = client.chat.completions.create(
            model=model_name,
            messages=formatted_messages,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            stream=False  # Set to False for non-streaming
        )
        
        # Extract the response content
        assistant_message = response.choices[0].message.content
        
        elapsed_time = time.time() - start_time
        
        progress_bar.progress(0.9, "Response received, processing...")
        model_display_name = f"Google {model_name}"
        
        # Set usage info (with token counts if available in the response)
        usage_info = {
            'elapsed_time': f"{elapsed_time:.2f} seconds"
        }
        
        # Add token usage if available in the response
        if hasattr(response, 'usage'):
            usage_info['prompt_tokens'] = response.usage.prompt_tokens
            usage_info['completion_tokens'] = response.usage.completion_tokens
            usage_info['total_tokens'] = response.usage.total_tokens
        else:
            usage_info['prompt_tokens'] = "N/A"
            usage_info['completion_tokens'] = "N/A"
            usage_info['total_tokens'] = "N/A"
            
        st.session_state.usage_info = usage_info
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