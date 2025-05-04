import requests
import streamlit as st
import time
import uuid
import os
import re
import json
from utils.check_model import get_current_model_name

# Check if running in Docker (environment variable can be set in docker-compose.yml)
IN_DOCKER = os.environ.get('IN_DOCKER', 'false').lower() == 'true'

# Choose URL endpoints based on environment
if IN_DOCKER:
    # Docker environment - use service name
    relay_url = 'http://relay-server:5000/relay'
    response_url = 'http://relay-server:5000/response'
    queue_size_url = 'http://relay-server:5000/queue_size'
    status_url = 'http://relay-server:5000/status'
    stream_url = 'http://relay-server:5000/stream'
else:
    # Local environment - use localhost
    relay_url = 'http://localhost:5000/relay'
    response_url = 'http://localhost:5000/response'
    queue_size_url = 'http://localhost:5000/queue_size'
    status_url = 'http://localhost:5000/status'
    stream_url = 'http://localhost:5000/stream'

def extract_thinking(text):
    """Extract thinking content from response text"""
    thinking_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL)
    match = thinking_pattern.search(text)
    
    if match:
        thinking_content = match.group(1).strip()
        # Remove the thinking part from the original text
        clean_text = thinking_pattern.sub('', text).strip()
        return clean_text, thinking_content
    
    # If no thinking tags found, return original text and None
    return text, None

def get_streaming_response(message, progress_bar, start_time, message_placeholder):
    """Get streamed response from local model via relay server"""
    request_id = str(uuid.uuid4())
    
    data = {
        'text': [{'role': msg['role'], 'content': msg['content']} for msg in message],
        'request_id': request_id,
        'max_tokens': st.session_state.max_tokens,
        'temperature': st.session_state.temperature,
        'stream': True
    }
    
    progress_bar.progress(20, "Sending streaming request...")
    
    # Create a placeholder for the streaming text
    full_response = ""
    
    try:
        response = requests.post(stream_url, json=data, stream=True)
        
        # Update the placeholder with empty text to start
        message_placeholder.markdown("")
        
        # Process the streaming response line by line
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data:'):
                    chunk_data = line[5:].strip()
                    if chunk_data == "[DONE]":
                        break
                        
                    try:
                        json_obj = json.loads(chunk_data)
                        if 'choices' in json_obj and len(json_obj['choices']) > 0:
                            if 'delta' in json_obj['choices'][0] and 'content' in json_obj['choices'][0]['delta']:
                                chunk = json_obj['choices'][0]['delta']['content']
                                full_response += chunk
                                # Update the display with the accumulated response
                                message_placeholder.markdown(full_response)
                    except json.JSONDecodeError:
                        # Skip malformed JSON
                        continue
        
        # Process finished
        end_time = time.time()
        
        # Extract thinking content if present
        clean_message, thinking_content = extract_thinking(full_response)
        
        # Get token counts from the final response
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        
        # Try to get the final token counts if available
        try:
            resp = requests.get(f"{response_url}/{request_id}")
            if resp.status_code == 200:
                response_data = resp.json()
                prompt_tokens = response_data.get('prompt_tokens', 0)
                completion_tokens = response_data.get('completion_tokens', 0)
                total_tokens = response_data.get('total_tokens', 0)
        except Exception:
            # If we can't get token counts, just continue
            pass
        
        model_name = "Local " + get_current_model_name()
        st.session_state.usage_info = {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'elapsed_time': round(end_time - start_time, 2)
        }
        
        if thinking_content:
            st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': clean_message, 'reasoning': thinking_content, 'model': model_name})
        else:
            st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': clean_message, 'model': model_name})
        
        # Clear the placeholder
        message_placeholder.empty()
        progress_bar.empty()
        return clean_message
        
    except Exception as e:
        st.error(f"Error with streaming: {str(e)}")
        progress_bar.empty()
        return None

def get_response(message, progress_bar, start_time, message_placeholder=None):
    """Get response from local model via relay server"""
    # If streaming is enabled in session state, use streaming response
    if "enable_streaming" in st.session_state and st.session_state.enable_streaming:
        return get_streaming_response(message, progress_bar, start_time, message_placeholder)
    
    # Original non-streaming implementation
    request_id = str(uuid.uuid4())
    
    data = {
        'text': [{'role': msg['role'], 'content': msg['content']} for msg in message],
        'request_id': request_id,
        'max_tokens': st.session_state.max_tokens,
        'temperature': st.session_state.temperature
    }
    
    progress_bar.progress(20, "Sending request to the relay server...")
    
    response = requests.post(relay_url, json=data)
    response_data = response.json()
    queue_position = response_data['position']
    
    # Update the progress bar
    progress_bar.progress(30, f"Request sent, waiting in queue... (Position: {queue_position})")

    def check_request_status(request_id):
        response = requests.get(f"{status_url}/{request_id}")
        if response.status_code == 200:
            return response.json()['status']
        return 'unknown'
    
    # Poll the relay server for the response
    while True:
        status = check_request_status(request_id)
        if status == 'completed':
            progress_bar.progress(90, "Response received, processing...")
            end_time = time.time()
            response = requests.get(f"{response_url}/{request_id}")
            response_data = response.json()
            if 'error' in response_data:
                st.error(f"Error: {response_data['error']}")
                progress_bar.empty()
                return None
            
            assistant_message = response_data['assistant_message']
            
            # Extract thinking content if present
            clean_message, thinking_content = extract_thinking(assistant_message)
            
            model_name = "Local " + get_current_model_name()
            st.session_state.usage_info = {
                'prompt_tokens': response_data['prompt_tokens'],
                'completion_tokens': response_data['completion_tokens'],
                'total_tokens': response_data['total_tokens'],
                'elapsed_time': round(end_time - start_time, 2)
            }
            if thinking_content:
                st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': clean_message, 'reasoning': thinking_content, 'model': model_name})
            else:
                st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': clean_message, 'model': model_name})
            
            progress_bar.progress(100, "Response processed successfully.")
            time.sleep(1)
            progress_bar.empty()
            return clean_message
        elif status == 'queued':
            # Update the progress bar
            queue_size_response = requests.get(queue_size_url)
            queue_size = queue_size_response.json()['queue_size']
            progress_bar.progress(35, f"Waiting in queue... (Position: {queue_position} / Queue Size: {queue_size})")
            time.sleep(0.5)
        elif status == 'processing':
            progress_bar.progress(50, "Request is being processed...")
            time.sleep(0.5)
        else:
            st.error("Error retrieving response")
            progress_bar.empty()
            break
