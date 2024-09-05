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
text_adventure_game_default = [
            {
                "role": "user",
                "content": "You are a text adventure game guide who will play a text adventure game with the user. You will guide the user through the game, and the user will say what they want to do in the game. You will then respond to the user's actions and provide action options to continue the game. When the user says 'Let's go!, or something similar, you will start the game. If the user want to play a game they provide, you will start the game based on the user's request. You will only generate text that is related to the game, and you will not generate actions for the user. You will use any language the user initially uses. The following is an example."
            },
            {
                "role": "assistant",
                "content": "Ok."
            },
            {
                "role": "user",
                "content": "Example:{A description of the surroundings and the environment, please be creative! Prompt thee user with action options:\n- Option 1\n- Option 2\n- Option 3}"
            },
            {
                "role": "assistant",
                "content": "Let's start the text adventure game!"
            }
        ]
story_writer_default = [
            {
                "role": "user",
                "content": "You are a story writer who will write a story based on the user's prompt. You will write a story based on the user's prompt, and the user will provide the prompt for the story. You will then write the story based on the user's prompt and provide the story to the user. You will only generate text that is related to the story, and you will not generate actions for the user. You will use any language the user initially uses. Character names can be freely decided by the user, even user ids."                
            },
            {
                "role": "assistant",
                "content": "Let's start writing a story!"
            }
        ]
code_writer_default = [
            {
                "role": "user",
                "content": "You are a code writer who will write code based on the user's prompt. You will write code based on the user's prompt, and the user will provide the prompt for the code. You will then write the code based on the user's prompt and provide the code to the user. You will only generate text that is related to the code. You will use any language the user initially uses."                
            },
            {
                "role": "assistant",
                "content": "What code would you like me to write?"
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

if "autosave" not in st.session_state:
    st.session_state.autosave = False

if "autosave_path" not in st.session_state:
    st.session_state.autosave_path = "C:\\Users\\jimye\\Downloads\\conversations.json"

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "Text Chat"

if "messages_text_adventure_game" not in st.session_state:
    st.session_state.messages_text_adventure_game = text_adventure_game_default.copy()

if "messages_story_writer" not in st.session_state:
    st.session_state.messages_story_writer = story_writer_default.copy()

if "messages_code_writer" not in st.session_state:
    st.session_state.messages_code_writer = code_writer_default.copy()

# Set page config
st.set_page_config(page_title="Text Chat Bot", page_icon="🤖", layout="wide", menu_items={"Report a bug": "mailto:ljsh1111031@ljsh.hcc.edu.tw"})

model_name = st.empty()

#Create columns
left_column, right_column = st.columns([4, 1])

# Sidebar
sidebar = st.sidebar
# Sidebar - Title
sidebar.subheader("Text Chat Bot")
sidebar.markdown("Version: 1.5")
sidebar.markdown("Developed by: JimmyN0912")
sidebar.markdown("---")

# Sidebar - Text-Gen Stats
sidebar.markdown("### Text-Gen Stats")
sidebar.markdown(f"Prompt Tokens: {st.session_state.usage_info.get('prompt_tokens', 'N/A')}")
sidebar.markdown(f"Completion Tokens: {st.session_state.usage_info.get('completion_tokens', 'N/A')}")
if st.session_state.usage_info.get('completion_tokens', 'N/A') != 'N/A' and st.session_state.usage_info.get('elapsed_time', 'N/A') != 'N/A':
    sidebar.markdown(f"Generation Speed: {round(st.session_state.usage_info.get('completion_tokens', 'N/A') / st.session_state.usage_info.get('elapsed_time'), 2)} tokens/s")
sidebar.markdown(f"Total Tokens: {st.session_state.usage_info.get('total_tokens', 'N/A')}")
sidebar.markdown(f"Elapsed Time: {st.session_state.usage_info.get('elapsed_time', 'N/A')} s")
sidebar.markdown("---")

# Sidebar - Chat Mode Options
sidebar.markdown("### Chat Modes")
st.session_state.chat_mode = sidebar.selectbox("Select Chat Mode", ["Text Chat", "Text Adventure Game", "Story Writer", "Code Writer"])
    
# Chat Container
with left_column:
    container = st.container(height=900, border=True)
    with container:
        if st.session_state.chat_mode == "Text Chat":
            # Display chat messages from history on app rerun
            st.chat_message("assistant").markdown("Hello! How can I help you today?")
            for message in st.session_state.messages[2:]:
                st.chat_message(message["role"]).markdown(message["content"])
        elif st.session_state.chat_mode == "Text Adventure Game":
            # Display chat messages from history on app rerun
            st.chat_message("assistant").markdown("Let's start the text adventure game!")
            for message in st.session_state.messages_text_adventure_game[4:]:
                st.chat_message(message["role"]).markdown(message["content"])
        elif st.session_state.chat_mode == "Story Writer":
            # Display chat messages from history on app rerun
            st.chat_message("assistant").markdown("Let's start writing a story!")
            for message in st.session_state.messages_story_writer[2:]:
                st.chat_message(message["role"]).markdown(message["content"])
        elif st.session_state.chat_mode == "Code Writer":
            # Display chat messages from history on app rerun
            st.chat_message("assistant").markdown("What code would you like me to write?")
            for message in st.session_state.messages_code_writer[2:]:
                st.chat_message(message["role"]).markdown(message["content"])

    def check_request_status(request_id):
        response = requests.get(f"{status_url}/{request_id}")
        if response.status_code == 200:
            return response.json()['status']
        return 'unknown'

    # Function to get response from the API via relay server
    def get_text_to_text(mode):
        request_id = str(uuid.uuid4())
        if mode == "text_chat":
            message = st.session_state.messages
        elif mode == "text_adventure_game":
            message = st.session_state.messages_text_adventure_game
        elif mode == "story_writer":
            message = st.session_state.messages_story_writer
        elif mode == "code_writer":
            message = st.session_state.messages_code_writer
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
                if mode == "text_chat":
                    st.session_state.messages.append({'role': 'assistant', 'content': assistant_message})
                elif mode == "text_adventure_game":
                    st.session_state.messages_text_adventure_game.append({'role': 'assistant', 'content': assistant_message})
                elif mode == "story_writer":
                    st.session_state.messages_story_writer.append({'role': 'assistant', 'content': assistant_message})
                elif mode == "code_writer":
                    st.session_state.messages_code_writer.append({'role': 'assistant', 'content': assistant_message})
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
            if st.session_state.chat_mode == "Text Chat":
                # Append user message to session state
                st.session_state.messages.append({'role': 'user', 'content': prompt})
                input_container.empty()
                # Get response from the API and display it
                response = get_text_to_text("text_chat")
            elif st.session_state.chat_mode == "Text Adventure Game":
                # Append user message to session state
                st.session_state.messages_text_adventure_game.append({'role': 'user', 'content': prompt})
                input_container.empty()
                # Get response from the API and display it
                response = get_text_to_text("text_adventure_game")
            elif st.session_state.chat_mode == "Story Writer":
                # Append user message to session state
                st.session_state.messages_story_writer.append({'role': 'user', 'content': prompt})
                input_container.empty()
                # Get response from the API and display it
                response = get_text_to_text("story_writer")
            elif st.session_state.chat_mode == "Code Writer":
                # Append user message to session state
                st.session_state.messages_code_writer.append({'role': 'user', 'content': prompt})
                input_container.empty()
                # Get response from the API and display it
                response = get_text_to_text("code_writer")

            if response:
                st.chat_message("assistant").markdown(response)
                if st.session_state.autosave:
                    if st.session_state.chat_mode == "Text Chat":
                        with open(st.session_state.autosave_path, 'w') as f:
                            json.dump(st.session_state.messages, f, indent=4)
                    elif st.session_state.chat_mode == "Text Adventure Game":
                        with open(st.session_state.autosave_path, 'w') as f:
                            json.dump(st.session_state.messages_text_adventure_game, f, indent=4)
                    elif st.session_state.chat_mode == "Story Writer":
                        with open(st.session_state.autosave_path, 'w') as f:
                            json.dump(st.session_state.messages_story_writer, f, indent=4)
                    elif st.session_state.chat_mode == "Code Writer":
                        with open(st.session_state.autosave_path, 'w') as f:
                            json.dump(st.session_state.messages_code_writer, f, indent=4)
                st.rerun()

def get_model_info():
    response = requests.get(model_info_url, headers=headers)
    if response.status_code == 200:
        model_name = response.json()['model_name']
        return model_name
    return {}

model_name.info(f"Current Model: {get_model_info()}", icon="ℹ️")

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
    with st.expander("Settings", expanded=True):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.5, 0.05)
        st.session_state.max_tokens = st.number_input("Max Tokens", 1, 1024, 512, 1)
        st.session_state.autosave = st.checkbox("Autosave Conversations", value=False)
        st.session_state.autosave_path = st.text_input("Autosave Path", value="S:\\chat_histories\\conversations.json")
    with st.expander("Model Options", expanded=False):
        st.session_state.model_name = st.selectbox("Model Name", {"Meta-Llama-3-8B-Instruct.Q4_K_M.gguf", "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf", "Mistral-7B-Instruct-v0.2-Quantised.gguf"})
        st.session_state.n_gpu_layers = st.slider("n-gpu-layers", 0, 33, 33, 1)
        st.session_state.n_ctx = st.number_input("n_ctx", 1024, 65536, 65536 ,1)
        if st.button("Load Model"):
            load_model_args = {"n_gpu_layers": st.session_state.n_gpu_layers, "n_ctx": st.session_state.n_ctx}
            with st.spinner("Loading model..."):
                load_status = load_model(st.session_state.model_name, load_model_args)
            st.toast(load_status, icon="✅")
            time.sleep(4)
            st.rerun()
        if st.button("Unload Model"):
            with st.spinner("Unloading model..."):
                unload_status = unload_model()
            st.toast(unload_status, icon="✅")
            time.sleep(4)
            st.rerun()
    with st.expander("Conversation Options", expanded=False):
        if st.button("Reset Conversations"):
            if st.session_state.chat_mode == "Text Chat":
                st.session_state.messages = text_chat_default.copy()
                st.session_state.usage_info = {}
                st.rerun()
            elif st.session_state.chat_mode == "Text Adventure Game":
                st.session_state.messages_text_adventure_game = text_adventure_game_default.copy()
                st.session_state.usage_info = {}
                st.rerun()
            elif st.session_state.chat_mode == "Story Writer":
                st.session_state.messages_story_writer = story_writer_default.copy()
                st.session_state.usage_info = {}
                st.rerun()
            elif st.session_state.chat_mode == "Code Writer":
                st.session_state.messages_code_writer = code_writer_default.copy()
                st.session_state.usage_info = {}
                st.rerun()
        if st.button("Remove previous message"):
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()
        # Export Conversations
        def export_conversations():
            if st.session_state.chat_mode == "Text Chat":
                export_data = json.dumps(st.session_state.messages)
            elif st.session_state.chat_mode == "Text Adventure Game":
                export_data = json.dumps(st.session_state.messages_text_adventure_game)
            elif st.session_state.chat_mode == "Story Writer":
                export_data = json.dumps(st.session_state.messages_story_writer)
            elif st.session_state.chat_mode == "Code Writer":
                export_data = json.dumps(st.session_state.messages_code_writer)
            return export_data
        st.download_button(
            label="Export Conversations",
            data=export_conversations(),
            file_name="conversations.json",
            mime="application/json"
        )
        # Import Conversations
        def import_conversations(uploaded_file):
            json_file = json.load(uploaded_file)
            if st.session_state.chat_mode == "Text Chat":
                st.session_state.messages = json_file
            elif st.session_state.chat_mode == "Text Adventure Game":
                st.session_state.messages_text_adventure_game = json_file
            elif st.session_state.chat_mode == "Story Writer":
                st.session_state.messages_story_writer = json_file
            elif st.session_state.chat_mode == "Code Writer":
                st.session_state.messages_code_writer = json_file
        def update_key():
            st.session_state.uploader_key += 1    
        uploaded_file = st.file_uploader(
            label="Import Conversations",
            type="json",
            key=st.session_state.uploader_key)
        if uploaded_file:
            import_conversations(uploaded_file)
            update_key()
            st.rerun()