import streamlit as st
import time
from google.genai import types
from os import getenv
from dotenv import load_dotenv
import requests

# Initialize Gemini Client
load_dotenv()

base_url = "https://generativelanguage.googleapis.com/v1beta/models/"

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

def get_response(message, mode, progress_bar):
    """Get response from Google Gemini API"""
    try:
        # Initialize Gemini client
        model = models[st.session_state.gemini_model]
        url = base_url + model + ":generateContent" + "?key=" + getenv("GEMINI_API_KEY")

        progress_bar.progress(20, "Sending request to Gemini API...")
        
        # Format messages for Gemini
        gemini_messages = []
        for msg in message:
            if msg['role'] == 'system':
                # Include system messages as user messages prefixed with "[System]"
                gemini_messages.append(
                    {
                        "role": "user",
                        "parts": {
                            "text": "[System] " + msg['content']
                        }
                    }
                )
            elif msg['role'] == 'user':
                gemini_messages.append(
                    {
                        "role": "user",
                        "parts": {
                            "text": msg['content']
                        }
                    }
                )
            elif msg['role'] == 'assistant':
                gemini_messages.append(
                    {
                        "role": "model",
                        "parts": {
                            "text": msg['content']
                        }
                    }
                )

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data={
                "contents": gemini_messages,
                "generateContentConfig": {
                    "temperature": st.session_state.temperature,
                    "maxOutputTokens": st.session_state.max_tokens,
                    "responseMimeType": "text/plain",
                    "thinkingConfig": {
                        "thinkingBudget": 1024
                    }
                }
            }
        )


        print(response.text)
        progress_bar.progress(90, "Response received, processing...")
        assistant_message = response.text
        model_name = f"Google {model}"
        
        # Set usage info (Gemini doesn't provide token counts the same way)
        st.session_state.usage_info = {
            'prompt_tokens': response.usage_metadata.prompt_token_count,
            'completion_tokens': response.usage_metadata.candidates_token_count,
            'total_tokens': response.usage_metadata.total_token_count,
            'elapsed_time': ''
        }
        
        # Add the response to the appropriate message list
        if mode == "text_chat":
            st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': model_name})
        elif mode == "text_adventure_game":
            st.session_state.messages_text_adventure_game.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': model_name})
        elif mode == "story_writer":
            st.session_state.messages_story_writer.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': model_name})
        elif mode == "code_writer":
            st.session_state.messages_code_writer.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': model_name})

        progress_bar.progress(100, "Response processed successfully.")
        time.sleep(1)
        progress_bar.empty()        
        return assistant_message

    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        progress_bar.empty()
        return None
