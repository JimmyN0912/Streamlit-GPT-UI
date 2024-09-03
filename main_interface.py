import streamlit as st
import requests
import time
import uuid
import json
import base64

# Variables
headers = {"Content-Type": "application/json"}
ttt_url = "http://192.168.0.175:5000/v1/chat/completions"
relay_url = 'http://localhost:5000/relay'
response_url = 'http://localhost:5000/response'
queue_size_url = 'http://localhost:5000/queue_size'
status_url = 'http://localhost:5000/status'
model_info_url = "http://192.168.0.175:5000/v1/internal/model/info"
model_list_url = "http://192.168.0.175:5000/v1/internal/model/list"
model_load_url = "http://192.168.0.175:5000/v1/internal/model/load"
model_unload_url = "http://192.168.0.175:5000/v1/internal/model/unload"
text_chat_default = [
    {
        'role': 'user',
        'content': "You are a text chat assistant who will generate responses based on the user's messages. You can engage in all kinds of conversations with the user. You can also provide information, answer questions, and more. You will respond in English or Chinese.",
    },
    {
        'role': 'assistant',
        'content': "Hello! How can I help you today?",
    }
]

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = text_chat_default.copy()

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "usage_info" not in st.session_state:
    st.session_state.usage_info = {}

if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 512

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.5

if "model_name" not in st.session_state:
    st.session_state.model_name = "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"

if "n_gpu_layers" not in st.session_state:
    st.session_state.n_gpu_layers = 33

if "n_ctx" not in st.session_state:
    st.session_state.n_ctx = 65536

# Set page config
st.set_page_config(page_title="Text Chat Bot", page_icon="🤖", layout="wide", menu_items={"Report a bug": "mailto:ljsh1111031@ljsh.hcc.edu.tw"})

#Create columns
left_column, right_column = st.columns([4, 1])

# Sidebar
sidebar = st.sidebar
# Sidebar - Title
sidebar.markdown("# Text Chat Bot")
sidebar.markdown("## Version: 1.3")
sidebar.markdown("## Developed by: JimmyN0912")
sidebar.markdown("---")
# Sidebar - Export/Import Conversations
sidebar.markdown("# Conversation Options：")
def export_conversations():
    export_data = json.dumps(st.session_state.messages)
    return export_data

st.sidebar.download_button(
    label="Export Conversations",
    data=export_conversations(),
    file_name="conversations.json",
    mime="application/json"
)

def import_conversations(uploaded_file):
    json_file = json.load(uploaded_file)
    st.session_state.messages = json_file

def update_key():
    st.session_state.uploader_key += 1
    
# Import Conversations
uploaded_file = st.sidebar.file_uploader(
    label="Import Conversations",
    type="json",
    key=st.session_state.uploader_key)

if uploaded_file:
    import_conversations(uploaded_file)
    update_key()
    st.rerun()

# Reset button
with st.sidebar:
    if st.button("Reset Conversations"):
        st.session_state.messages = text_chat_default.copy()
        st.session_state.usage_info = {}
        st.rerun()
    if st.button("Remove previous message"):
        st.session_state.messages = st.session_state.messages[:-2]
        st.rerun()

# Sidebar - Text-Gen Stats
sidebar.markdown("---")
sidebar.markdown("### Text-Gen Stats")
sidebar.markdown(f"Prompt Tokens: {st.session_state.usage_info.get('prompt_tokens', 'N/A')}")
sidebar.markdown(f"Completion Tokens: {st.session_state.usage_info.get('completion_tokens', 'N/A')}")
sidebar.markdown(f"Total Tokens: {st.session_state.usage_info.get('total_tokens', 'N/A')}")
sidebar.markdown(f"Elapsed Time: {st.session_state.usage_info.get('elapsed_time', 'N/A')} seconds")
sidebar.markdown("---")
    
# Chat Container
with left_column:
    container = st.container(height=950, border=True)
    with container:
        # Display chat messages from history on app rerun
        st.chat_message("assistant").markdown("Hello! How can I help you today?")
        for message in st.session_state.messages[2:]:
            st.chat_message(message["role"]).markdown(message["content"])

    def check_request_status(request_id):
        response = requests.get(f"{status_url}/{request_id}")
        if response.status_code == 200:
            return response.json()['status']
        return 'unknown'

    # Function to get response from the API via relay server
    def get_text_to_text():
        request_id = str(uuid.uuid4())
        message = st.session_state.messages
        data = {
            'text': message,
            'request_id': request_id,
            'max_tokens': st.session_state.max_tokens,
            'temperature': st.session_state.temperature
        }
        # Initialize the progress bar
        progress_bar = st.progress(0, "Sending request to the relay server...")
        start_time = time.time()

        response = requests.post(relay_url, json=data)

        response_data = response.json()
        queue_position = response_data['position']
        
        # Update the progress bar
        progress_bar.progress(20, f"Request sent, waiting in queue... (Position: {queue_position})")
        
        # Poll the relay server for the response
        while True:
            status = check_request_status(request_id)
            if status == 'completed':
                progress_bar.progress(95, "Response received, processing...")
                end_time = time.time()
                response = requests.get(f"{response_url}/{request_id}")
                response_data = response.json()
                if 'error' in response_data:
                    st.error(f"Error: {response_data['error']}")
                    return None
                assistant_message = response_data['assistant_message']
                st.session_state.usage_info = {
                    'prompt_tokens': response_data['prompt_tokens'],
                    'completion_tokens': response_data['completion_tokens'],
                    'total_tokens': response_data['total_tokens'],
                    'elapsed_time': round(end_time - start_time, 2)
                }
                st.session_state.messages.append({'role': 'assistant', 'content': assistant_message})
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
                break

    # Accept user input
    input_container = st.empty()
    prompt = input_container.chat_input("Enter your message here...",key=32768)
    if prompt:
        with container:
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Append user message to session state
            st.session_state.messages.append({'role': 'user', 'content': prompt})
            input_container.empty()
            # Get response from the API and display it
            response = get_text_to_text()
            if response:
                st.chat_message("assistant").markdown(response)
                st.rerun()

def get_model_info():
    response = requests.get(model_info_url, headers=headers)
    if response.status_code == 200:
        model_name = response.json()['model_name']
        return model_name
    return {}

def load_model(model_name, load_model_args):
    payload = {"model_name": model_name, "args": load_model_args}
    response = requests.post(model_load_url, json=payload, headers=headers)
    if response.status_code == 200:
        return "Model loaded successfully"
    return "Model loading failed"
    
def unload_model():
    response = requests.post(model_unload_url, headers=headers)
    if response.status_code == 200:
        return "Model unloaded successfully"
    return "Model unloading failed"

# Right column
with right_column:
    st.markdown("### Settings")
    st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.5, 0.05)
    st.session_state.max_tokens = st.number_input("Max Tokens", 1, 1024, 512, 1)
    st.markdown("---")
    st.markdown("### Model Info")
    model_info = get_model_info()
    st.markdown(f"Model Name:\n\n{model_info}")
    if st.button("Refresh Model Info"):
        st.rerun()
    st.markdown("---")
    st.markdown("### Model Loading")
    st.session_state.model_name = st.selectbox("Model Name", {"Meta-Llama-3-8B-Instruct.Q4_K_M.gguf", "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf", "Mistral-7B-Instruct-v0.2-Quantised.gguf"})
    st.session_state.n_gpu_layers = st.slider("n-gpu-layers", 0, 33, 33, 1)
    st.session_state.n_ctx = st.number_input("n_ctx", 1024, 65536, 65536 ,1)
    if st.button("Load Model"):
        load_model_args = {"n_gpu_layers": st.session_state.n_gpu_layers, "n_ctx": st.session_state.n_ctx}
        with st.spinner("Loading model..."):
            load_status = load_model(st.session_state.model_name, load_model_args)
            st.toast(load_status, icon="✅")
    if st.button("Unload Model"):
        with st.spinner("Unloading model..."):
            unload_status = unload_model()
            st.toast(unload_status, icon="✅")