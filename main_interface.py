import streamlit as st
import requests
import time
import uuid
import json
import PyPDF2
import datetime

# Variables
headers = {"Content-Type": "application/json"}
relay_url = 'http://localhost:5000/relay'
response_url = 'http://localhost:5000/response'
queue_size_url = 'http://localhost:5000/queue_size'
status_url = 'http://localhost:5000/status'
text_chat_default = [
    {
        'role': 'system',
        'type': 'message',
        'content': "You are a text chat assistant who will generate responses based on the user's messages. You can engage in all kinds of conversations with the user. You can also provide information, answer questions, and more.",
    },
    {
        'role': 'assistant',
        'type': 'message',
        'content': "Hello! How can I help you today?",
    }
]
text_adventure_game_default = [
            {
                "role": "user",
                'type': 'message',
                "content": "You are a text adventure game guide who will play a text adventure game with the user. You will guide the user through the game, and the user will say what they want to do in the game. You will then respond to the user's actions and provide action options to continue the game. When the user says 'Let's go!, or something similar, you will start the game. If the user want to play a game they provide, you will start the game based on the user's request. You will only generate text that is related to the game, and you will not generate actions for the user. You will use any language the user initially uses. The following is an example."
            },
            {
                "role": "assistant",
                'type': 'message',
                "content": "Ok."
            },
            {
                "role": "user",
                'type': 'message',
                "content": "Example:{A description of the surroundings and the environment, please be creative! Prompt thee user with action options:\n- Option 1\n- Option 2\n- Option 3}"
            },
            {
                "role": "assistant",
                'type': 'message',
                "content": "Let's start the text adventure game!"
            }
        ]
story_writer_default = [
            {
                "role": "user",
                'type': 'message',
                "content": "You are a story writer who will write a story based on the user's prompt. You will write a story based on the user's prompt, and the user will provide the prompt for the story. You will then write the story based on the user's prompt and provide the story to the user. You will only generate text that is related to the story, and you will not generate actions for the user. You will use any language the user initially uses. Character names can be freely decided by the user, even user ids."                
            },
            {
                "role": "assistant",
                'type': 'message',
                "content": "Let's start writing a story!"
            }
        ]
code_writer_default = [
            {
                "role": "user",
                'type': 'message',
                "content": "You are a code writer who will write code based on the user's prompt. You will write code based on the user's prompt, and the user will provide the prompt for the code. You will then write the code based on the user's prompt and provide the code to the user. You will only generate text that is related to the code. You will use any language the user initially uses."                
            },
            {
                "role": "assistant",
                'type': 'message',
                "content": "What code would you like me to write?"
            }
        ]

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = text_chat_default.copy()

if "chat_uploader_key" not in st.session_state:
    st.session_state.chat_uploader_key = 0

if "pdf_uploader_key" not in st.session_state:
    st.session_state.pdf_uploader_key = 131072

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

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

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
        'text': [{'role': msg['role'], 'content': msg['content']} for msg in message],
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

    def check_request_status(request_id):
        response = requests.get(f"{status_url}/{request_id}")
        if response.status_code == 200:
            return response.json()['status']
        return 'unknown'
    
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
                st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message})
            elif mode == "text_adventure_game":
                st.session_state.messages_text_adventure_game.append({'role': 'assistant', 'type': 'message', 'content': assistant_message})
            elif mode == "story_writer":
                st.session_state.messages_story_writer.append({'role': 'assistant', 'type': 'message', 'content': assistant_message})
            elif mode == "code_writer":
                st.session_state.messages_code_writer.append({'role': 'assistant', 'type': 'message', 'content': assistant_message})
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

def update_key(module):
    if module == "chat":
        st.session_state.chat_uploader_key += 1
    if module == "pdf":
        st.session_state.pdf_uploader_key += 1

# Function to convert PDF to text using PyPDF2
def pdf_to_text(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text()
    return text

# Set page config
st.set_page_config(page_title="Text Chat Bot", page_icon="🤖", layout="wide", menu_items={"Report a bug": "mailto:ljsh1111031@ljsh.hcc.edu.tw"})

model_name = st.empty()

# Sidebar
sidebar = st.sidebar

# Sidebar - Text-Gen Stats
with sidebar.expander("Text-Gen Stats", expanded=True):
    st.markdown(f"Prompt Tokens: {st.session_state.usage_info.get('prompt_tokens', 'N/A')}")
    st.markdown(f"Completion Tokens: {st.session_state.usage_info.get('completion_tokens', 'N/A')}")
    if st.session_state.usage_info.get('completion_tokens', 'N/A') != 'N/A' and st.session_state.usage_info.get('elapsed_time', 'N/A') != 'N/A':
        st.markdown(f"Generation Speed: {round(st.session_state.usage_info.get('completion_tokens', 'N/A') / st.session_state.usage_info.get('elapsed_time'), 2)} tokens/s")
    st.markdown(f"Total Tokens: {st.session_state.usage_info.get('total_tokens', 'N/A')}")
    st.markdown(f"Elapsed Time: {st.session_state.usage_info.get('elapsed_time', 'N/A')} s")

with sidebar.expander("Settings", expanded=False):
        st.session_state.temperature = st.slider(
            label="Temperature", 
            help="Lower values generate more confident responses, while higher values generate more diverse and random responses.",
            min_value=0.0, 
            max_value=1.0, 
            value=0.7, 
            step=0.05)
        st.session_state.max_tokens = st.number_input(
            label="Max Tokens",
            help="The maximum number of tokens to generate in the response.", 
            min_value=1, 
            max_value=2048, 
            value=1024, 
            step=1)
        st.session_state.autosave = st.checkbox(
            label="Autosave Conversations",
            help="Automatically save the conversation history after each message.", 
            value=False,
            disabled=True)
        st.session_state.autosave_path = st.text_input(
            label="Autosave Path",
            help="The file path for autosaving the conversation history.", 
            value="S:\\chat_histories\\conversations.json",
            disabled=not st.session_state.autosave)

with sidebar.expander("Conversation Options", expanded=True):
        if st.button(
            label="Reset Conversations",
            help="Start a new conversation."):
            if st.session_state.chat_mode == "Text Chat":
                st.session_state.messages = text_chat_default.copy()
                st.session_state.usage_info = {}
            elif st.session_state.chat_mode == "Text Adventure Game":
                st.session_state.messages_text_adventure_game = text_adventure_game_default.copy()
                st.session_state.usage_info = {}
            elif st.session_state.chat_mode == "Story Writer":
                st.session_state.messages_story_writer = story_writer_default.copy()
                st.session_state.usage_info = {}
            elif st.session_state.chat_mode == "Code Writer":
                st.session_state.messages_code_writer = code_writer_default.copy()
                st.session_state.usage_info = {}
            st.rerun()
        if st.button(
            label="Remove previous message",
            help="Remove the previous user message and assistant response."):
            if st.session_state.chat_mode == "Text Chat":
                st.session_state.messages = st.session_state.messages[:-2]
            elif st.session_state.chat_mode == "Text Adventure Game":
                st.session_state.messages_text_adventure_game = st.session_state.messages_text_adventure_game[:-2]
            elif st.session_state.chat_mode == "Story Writer":
                st.session_state.messages_story_writer = st.session_state.messages_story_writer[:-2]
            elif st.session_state.chat_mode == "Code Writer":
                st.session_state.messages_code_writer = st.session_state.messages_code_writer[:-2]
            st.rerun()
        if st.button(
            label="Rerun previous message",
            help="Resubmit the previous message to get a new response."):
            if st.session_state.chat_mode == "Text Chat":
                st.session_state.messages = st.session_state.messages[:-1]
                response = get_text_to_text("text_chat")
            elif st.session_state.chat_mode == "Text Adventure Game":
                st.session_state.messages_text_adventure_game = st.session_state.messages_text_adventure_game[:-1]
                response = get_text_to_text("text_adventure_game")
            elif st.session_state.chat_mode == "Story Writer":
                st.session_state.messages_story_writer = st.session_state.messages_story_writer[:-1]
                response = get_text_to_text("story_writer")
            elif st.session_state.chat_mode == "Code Writer":
                st.session_state.messages_code_writer = st.session_state.messages_code_writer[:-1]
                response = get_text_to_text("code_writer")
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
            help="Export the current conversations to a JSON file.",
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
        uploaded_file = st.file_uploader(
            label="Import Conversations",
            help="Import previous conversations from a JSON file to continue the chat.",
            type="json",
            key=st.session_state.chat_uploader_key)
        if uploaded_file:
            import_conversations(uploaded_file)
            update_key("chat")
            st.rerun()
        
        def edit_message():
            st.session_state.edit_mode = True

        # Edit last message
        st.button(
            label="Edit last message",
            help="Edit the last user message in the conversation history.",
            on_click=edit_message)
        

# Sidebar - Chat Mode Options
sidebar.markdown("### Chat Modes")
st.session_state.chat_mode = sidebar.selectbox(
    label="Select Chat Mode",
    help="Select the chat mode to use. Different chat modes serve different purposes and generate different types of responses.", 
    options=["Text Chat", "Text Adventure Game", "Story Writer", "Code Writer"])
sidebar.markdown("---")

# Main Interface
if st.session_state.chat_mode == "Text Chat":
    # Display chat messages from history on app rerun
    st.chat_message("assistant").markdown("Hello! How can I help you today?")
    total_messages = len(st.session_state.messages)
    for index, message in enumerate(st.session_state.messages[2:]):
        if index == total_messages - 4:
            if st.session_state.edit_mode == True:
                editor = st.empty()
                new_message = editor.text_input("Edit last message", value=message["content"])
                if new_message is not message["content"]:
                    editor.empty()
                    st.session_state.messages[-2]["content"] = new_message
                    del st.session_state.messages[-1]
                    st.session_state.edit_mode = False
                    st.chat_message("user").markdown(new_message)
                    get_text_to_text("text_chat")
                    st.rerun()
            else:
                if message["role"] == "system" and message["type"] == "PDF":
                    st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
                elif message["role"] != "system":
                    st.chat_message(message["role"]).markdown(message["content"])
        else:
            if message["role"] == "system" and message["type"] == "PDF":
                st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
            elif message["role"] != "system":
                st.chat_message(message["role"]).markdown(message["content"])
elif st.session_state.chat_mode == "Text Adventure Game":
    # Display chat messages from history on app rerun
    st.chat_message("assistant").markdown("Let's start the text adventure game!")
    total_messages = len(st.session_state.messages_text_adventure_game)
    for index, message in enumerate(st.session_state.messages_text_adventure_game[4:]):
        if index == total_messages - 6:
            if st.session_state.edit_mode == True:
                editor = st.empty()
                new_message = editor.text_input("Edit last message", value=message["content"])
                if new_message is not message["content"]:
                    editor.empty()
                    st.session_state.messages_text_adventure_game[-2]["content"] = new_message
                    del st.session_state.messages_text_adventure_game[-1]
                    st.session_state.edit_mode = False
                    st.chat_message("user").markdown(new_message)
                    get_text_to_text("text_adventure_game")
                    st.rerun()
            else:
                if message["role"] == "system" and message["type"] == "PDF":
                    st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
                elif message["role"] != "system":
                    st.chat_message(message["role"]).markdown(message["content"])
        else:
            if message["role"] == "system" and message["type"] == "PDF":
                st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
            if message["role"] != "system":
                st.chat_message(message["role"]).markdown(message["content"])
elif st.session_state.chat_mode == "Story Writer":
    # Display chat messages from history on app rerun
    st.chat_message("assistant").markdown("Let's start writing a story!")
    total_messages = len(st.session_state.messages_story_writer)
    for index, message in enumerate(st.session_state.messages_story_writer[2:]):
        if index == total_messages - 4:
            if st.session_state.edit_mode == True:
                editor = st.empty()
                new_message = editor.text_input("Edit last message", value=message["content"])
                if new_message is not message["content"]:
                    editor.empty()
                    st.session_state.messages_story_writer[-2]["content"] = new_message
                    del st.session_state.messages_story_writer[-1]
                    st.session_state.edit_mode = False
                    st.chat_message("user").markdown(new_message)
                    get_text_to_text("story_writer")
                    st.rerun()
            else:
                if message["role"] == "system" and message["type"] == "PDF":
                    st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
                elif message["role"] != "system":
                    st.chat_message(message["role"]).markdown(message["content"])
        else:
            if message["role"] == "system" and message["type"] == "PDF":
                st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
            if message["role"] != "system":
                st.chat_message(message["role"]).markdown(message["content"])
elif st.session_state.chat_mode == "Code Writer":
    # Display chat messages from history on app rerun
    st.chat_message("assistant").markdown("What code would you like me to write?")
    total_messages = len(st.session_state.messages_code_writer)
    for index, message in enumerate(st.session_state.messages_code_writer[2:]):
        if index == total_messages - 4:
            if st.session_state.edit_mode == True:
                editor = st.empty()
                new_message = editor.text_input("Edit last message", value=message["content"])
                if new_message is not message["content"]:
                    editor.empty()
                    st.session_state.messages_code_writer[-2]["content"] = new_message
                    del st.session_state.messages_code_writer[-1]
                    st.session_state.edit_mode = False
                    st.chat_message("user").markdown(new_message)
                    get_text_to_text("code_writer")
                    st.rerun()
            else:
                if message["role"] == "system" and message["type"] == "PDF":
                    st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
                elif message["role"] != "system":
                    st.chat_message(message["role"]).markdown(message["content"])
        else:
            if message["role"] == "system" and message["type"] == "PDF":
                st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
            if message["role"] != "system":
                st.chat_message(message["role"]).markdown(message["content"])

# Accept user input
input_container = st.empty()
prompt = input_container.chat_input("Enter your message here...",key=32768)
if prompt:
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if st.session_state.chat_mode == "Text Chat":
        # Append user message to session state
        st.session_state.messages.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
        st.session_state.messages.append({'role': 'user', 'type': 'message', 'content': prompt})
        input_container.empty()
        # Get response from the API and display it
        response = get_text_to_text("text_chat")
    elif st.session_state.chat_mode == "Text Adventure Game":
        # Append user message to session state
        st.session_state.messages_text_adventure_game.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
        st.session_state.messages_text_adventure_game.append({'role': 'user', 'type': 'message', 'content': prompt})
        input_container.empty()
        # Get response from the API and display it
        response = get_text_to_text("text_adventure_game")
    elif st.session_state.chat_mode == "Story Writer":
        # Append user message to session state
        st.session_state.messages_story_writer.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
        st.session_state.messages_story_writer.append({'role': 'user', 'type': 'message', 'content': prompt})
        input_container.empty()
        # Get response from the API and display it
        response = get_text_to_text("story_writer")
    elif st.session_state.chat_mode == "Code Writer":
        # Append user message to session state
        st.session_state.messages_code_writer.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
        st.session_state.messages_code_writer.append({'role': 'user', 'type': 'message', 'content': prompt})
        input_container.empty()
        # Get response from the API and display it
        response = get_text_to_text("code_writer")
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

upload_pdf = sidebar.file_uploader(
    label = "Upload a PDF file", 
    help="Upload a PDF file to the chat. Only text content will be extracted from the PDF file.",
    type=["pdf"],
    accept_multiple_files=False,
    key=st.session_state.pdf_uploader_key)
if upload_pdf:
    text = pdf_to_text(upload_pdf)
    if st.session_state.chat_mode == "Text Chat":
        st.session_state.messages.append({'role': 'system', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
    elif st.session_state.chat_mode == "Text Adventure Game":
        st.session_state.messages.append({'role': 'system', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
    elif st.session_state.chat_mode == "Story Writer":
        st.session_state.messages.append({'role': 'system', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
    elif st.session_state.chat_mode == "Code Writer":
        st.session_state.messages.append({'role': 'system', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
    update_key("pdf")
    st.rerun()