import requests
import streamlit as st
import time
import uuid

# URL endpoints
relay_url = 'http://localhost:5000/relay'
response_url = 'http://localhost:5000/response'
queue_size_url = 'http://localhost:5000/queue_size'
status_url = 'http://localhost:5000/status'

def get_response(message, mode, progress_bar, start_time):
    """Get response from local model via relay server"""
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
            model_name = "Local Model" # For local model, hardcode the name
            st.session_state.usage_info = {
                'prompt_tokens': response_data['prompt_tokens'],
                'completion_tokens': response_data['completion_tokens'],
                'total_tokens': response_data['total_tokens'],
                'elapsed_time': round(end_time - start_time, 2)
            }
            
            # Add the response to the appropriate message list with model name
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
