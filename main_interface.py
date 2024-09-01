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

# Set page config
st.set_page_config(page_title="Text Chat Bot", page_icon="🤖", layout="wide", menu_items={"Report a bug": "mailto:ljsh1111031@ljsh.hcc.edu.tw"})

#Create columns
left_column, right_column = st.columns([4, 1])

# Sidebar
sidebar = st.sidebar
# Sidebar CSS
st.markdown("""
    <style>
    .sidebar-text {
        font-family: 'DFKai-SB', sans-serif;
        font-size: 18px;
    }
    .sidebar-title {
        font-family: 'DFKai-SB', sans-serif;
        font-size: 22px;
        font-weight: bold;
    }
    .sidebar-subheader {
        font-family: 'DFKai-SB', sans-serif;
        font-size: 20px;
        font-weight: bold;
    }
    .sidebar-info {
        font-family: 'Arial', sans-serif;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)
# Sidebar - Title
sidebar.markdown("<div class='sidebar-title'>Text Chat Bot</div>", unsafe_allow_html=True)
sidebar.markdown("<div class='sidebar-info'>Version: 1.1</div>", unsafe_allow_html=True)
sidebar.markdown("<div class='sidebar-info'>Developed by: JimmyN0912</div>", unsafe_allow_html=True)
sidebar.markdown("---")
# Sidebar - Description
sidebar.markdown("<div class='sidebar-subheader'>關於本頁面：</div>", unsafe_allow_html=True)
sidebar.markdown("<div class='sidebar-text'>這是我的一個小技術展示的頁面，你可以用文字與AI對話。要使用此功能，請在下面的輸入框中輸入文字。</div>", unsafe_allow_html=True)
sidebar.markdown("<div class='sidebar-subheader'>使用注意事項：</div>", unsafe_allow_html=True)
sidebar.markdown("<div class='sidebar-text'>1. 可用中英文與AI對話，但中文對話效果可能不是太好。</div>", unsafe_allow_html=True)
sidebar.markdown("<div class='sidebar-text'>2. 請按提交按鈕提交文字，AI將生成回應。</div>", unsafe_allow_html=True)
sidebar.markdown("<div class='sidebar-text'>3. 請按重製按鈕重置對話，重新開始。</div>", unsafe_allow_html=True)
sidebar.info("AI生成內容僅供展示，生成內容可能不準確，僅供參考。", icon="🚨")
sidebar.markdown("---")
# Sidebar - Export/Import Conversations
sidebar.markdown("<div class='sidebar-subheader'>對話匯出/匯入：</div>", unsafe_allow_html=True)
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
    
# Chat Container
with left_column:
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
            'request_id': request_id
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


# Right column
with right_column:
    st.markdown("---")
    st.markdown("### Text-Gen Stats 生成相關數據：")
    st.markdown(f"Prompt Tokens: {st.session_state.usage_info.get('prompt_tokens', 'N/A')}")
    st.markdown(f"Completion Tokens: {st.session_state.usage_info.get('completion_tokens', 'N/A')}")
    st.markdown(f"Total Tokens: {st.session_state.usage_info.get('total_tokens', 'N/A')}")
    st.markdown(f"Elapsed Time: {st.session_state.usage_info.get('elapsed_time', 'N/A')} seconds")
    st.markdown("---")

# Reset button
with st.sidebar:
    if st.button("Reset 重置"):
        st.session_state.messages = text_chat_default.copy()
        st.session_state.usage_info = {}
        st.rerun()