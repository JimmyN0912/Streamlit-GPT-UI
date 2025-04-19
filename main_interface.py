import streamlit as st
import json
import datetime

# Import our modules
from utils.constants import (TEXT_CHAT_DEFAULT, TEXT_ADVENTURE_GAME_DEFAULT, STORY_WRITER_DEFAULT, CODE_WRITER_DEFAULT)
from utils.pdf_utils import pdf_to_text
from utils.chat_utils import update_key, get_text_to_text, export_conversations, import_conversations
from api import gemini, cloudflare, cohere, openrouter, groq

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = TEXT_CHAT_DEFAULT.copy()

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

if "autosave" not in st.session_state:
    st.session_state.autosave = False

if "autosave_path" not in st.session_state:
    st.session_state.autosave_path = "F:\\chats\\conversations.json"

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "Text Chat"

if "messages_text_adventure_game" not in st.session_state:
    st.session_state.messages_text_adventure_game = TEXT_ADVENTURE_GAME_DEFAULT.copy()

if "messages_story_writer" not in st.session_state:
    st.session_state.messages_story_writer = STORY_WRITER_DEFAULT.copy()

if "messages_code_writer" not in st.session_state:
    st.session_state.messages_code_writer = CODE_WRITER_DEFAULT.copy()

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "model_provider" not in st.session_state:
    st.session_state.model_provider = "Local Model"

if "gemini_model" not in st.session_state:
    st.session_state.gemini_model = "gemini-1.5-pro"

if "cloudflare_model" not in st.session_state:
    st.session_state.cloudflare_model = "Llama 4 Scout 17B 16E Instruct"

if "cohere_model" not in st.session_state:
    st.session_state.cohere_model = "Command R+"

if "openrouter_model" not in st.session_state:
    st.session_state.openrouter_model = "NVDA Llama 3.1 Nemotron Ultra 253B V1"

if "groq_model" not in st.session_state:
    st.session_state.groq_model = "Llama 4 Maverick 17B 128E Instruct"

# Set page config
st.set_page_config(page_title="Text Chat Bot", page_icon="🤖", layout="wide", menu_items={"Report a bug": "mailto:ljsh1111031@ljsh.hcc.edu.tw"})
if st.session_state.model_provider == "Local Model":
    st.badge("Current AI Model: Local model")
elif st.session_state.model_provider == "Google Gemini":
    st.badge(f"Current AI Model: {st.session_state.gemini_model}")
elif st.session_state.model_provider == "Cloudflare Workers AI":
    st.badge(f"Current AI Model: {st.session_state.cloudflare_model}")
elif st.session_state.model_provider == "Cohere":
    st.badge(f"Current AI Model: {st.session_state.cohere_model}")
elif st.session_state.model_provider == "OpenRouter":
    st.badge(f"Current AI Model: {st.session_state.openrouter_model}")
elif st.session_state.model_provider == "Groq":
    st.badge(f"Current AI Model: {st.session_state.groq_model}")

progress_bar = st.empty()

# Sidebar
sidebar = st.sidebar
with sidebar:
    st.markdown("## Chat Settings")
    st.session_state.model_provider = st.selectbox(
        label="Model Provider",
        help="Select the AI model provider to use for generating responses.",
        options=["Local Model", "Google Gemini", "Cloudflare Workers AI", "Cohere", "OpenRouter", "Groq"],
    )
    if st.session_state.model_provider == "Google Gemini":
        st.session_state.gemini_model = st.selectbox(
            label="Gemini Model",
            help="Select which Gemini model to use.",
            options=gemini.models.keys()
        )
    elif st.session_state.model_provider == "Cloudflare Workers AI":
        st.session_state.cloudflare_model = st.selectbox(
            label="Cloudflare Workers AI Model",
            help="Select which Cloudflare Workers AI model to use.",
            options=cloudflare.models.keys()
        )
    elif st.session_state.model_provider == "Cohere":
        st.session_state.cohere_model = st.selectbox(
            label="Cohere Model",
            help="Select which Cohere model to use.",
            options=cohere.models.keys()
        )
    elif st.session_state.model_provider == "OpenRouter":
        st.session_state.openrouter_model = st.selectbox(
            label="OpenRouter Model",
            help="Select which OpenRouter model to use.",
            options=openrouter.models.keys()
        )
    elif st.session_state.model_provider == "Groq":
        st.session_state.groq_model = st.selectbox(
            label="Groq Model",
            help="Select which Groq model to use.",
            options=groq.models.keys()
        )
    st.session_state.autosave = st.toggle(
        label="Autosave Conversations",
        help="Automatically save the conversation history after each message.", 
        value=False)
    st.session_state.autosave_path = st.text_input(
        label="Autosave Path",
        help="The file path for autosaving the conversation history.", 
        value=st.session_state.autosave_path,
        disabled=not st.session_state.autosave)
    
    st.sidebar.markdown("## Generation Parameters")
    st.session_state.temperature = st.slider(
        label="Temperature", 
        help="Lower values generate more confident responses, while higher values generate more diverse and random responses.",
        min_value=0.0, 
        max_value=1.0, 
        value=0.7, 
        step=0.05)
    st.session_state.max_tokens = st.slider(
        label="Max Tokens",
        help="The maximum number of tokens to generate in the response.", 
        min_value=256, 
        max_value=4096, 
        value=1024, 
        step=256)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        if st.button(
            label="❌",
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
    with col2:
        def edit_message():
            st.session_state.edit_mode = True
        # Edit last message
        st.button(
            label="✏️",
            help="Edit the last user message in the conversation history.",
            on_click=edit_message)
    with col3:
        if st.button(
            label="🔄️",
            help="Resubmit the previous message to get a new response."):
            if st.session_state.chat_mode == "Text Chat":
                st.session_state.messages = st.session_state.messages[:-1]
                response = get_text_to_text("text_chat", progress_bar)
            elif st.session_state.chat_mode == "Text Adventure Game":
                st.session_state.messages_text_adventure_game = st.session_state.messages_text_adventure_game[:-1]
                response = get_text_to_text("text_adventure_game", progress_bar)
            elif st.session_state.chat_mode == "Story Writer":
                st.session_state.messages_story_writer = st.session_state.messages_story_writer[:-1]
                response = get_text_to_text("story_writer", )
            elif st.session_state.chat_mode == "Code Writer":
                st.session_state.messages_code_writer = st.session_state.messages_code_writer[:-1]
                response = get_text_to_text("code_writer", progress_bar)
            st.rerun()
    with col4:
        if st.button(
        label="🗑️",
        help="Start a new conversation."):
            if st.session_state.chat_mode == "Text Chat":
                st.session_state.messages = TEXT_CHAT_DEFAULT.copy()
                st.session_state.usage_info = {}
            elif st.session_state.chat_mode == "Text Adventure Game":
                st.session_state.messages_text_adventure_game = TEXT_ADVENTURE_GAME_DEFAULT.copy()
                st.session_state.usage_info = {}
            elif st.session_state.chat_mode == "Story Writer":
                st.session_state.messages_story_writer = STORY_WRITER_DEFAULT.copy()
                st.session_state.usage_info = {}
            elif st.session_state.chat_mode == "Code Writer":
                st.session_state.messages_code_writer = CODE_WRITER_DEFAULT.copy()
                st.session_state.usage_info = {}
            st.rerun()
    with col5:
        st.download_button(
            label="💾",
            help="Export the current conversations to a JSON file.",
            data=export_conversations(),
            file_name="conversations.json",
            mime="application/json"
        )
    with st.expander("Usage Info", expanded=False):
        st.markdown(f"Prompt Tokens: {st.session_state.usage_info.get('prompt_tokens', 'N/A')}")
        st.markdown(f"Completion Tokens: {st.session_state.usage_info.get('completion_tokens', 'N/A')}")
        st.markdown(f"Total Tokens: {st.session_state.usage_info.get('total_tokens', 'N/A')}")
                
    uploaded_file = st.file_uploader(
        label="Import Conversations",
        help="Import previous conversations from a JSON file to continue the chat.",
        type="json",
        key=st.session_state.chat_uploader_key,
        accept_multiple_files=False)
    if uploaded_file:
        import_conversations(uploaded_file)
        update_key("chat")
        st.rerun()
    sidebar.markdown("## Chat Options")
    st.session_state.chat_mode = sidebar.selectbox(
        label="Select Chat Mode",
        help="Select the chat mode to use. Different chat modes serve different purposes and generate different types of responses.", 
        options=["Text Chat", "Text Adventure Game", "Story Writer", "Code Writer"])
    
    upload_pdf = st.file_uploader(
    label = "Upload a PDF file", 
    help="Upload a PDF file to the chat. Only text content will be extracted from the PDF file.",
    type=["pdf"],
    accept_multiple_files=False,
    key=st.session_state.pdf_uploader_key)
    if upload_pdf:
        text = pdf_to_text(upload_pdf)
        if st.session_state.chat_mode == "Text Chat":
            st.session_state.messages.append({'role': 'user', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
        elif st.session_state.chat_mode == "Text Adventure Game":
            st.session_state.messages.append({'role': 'system', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
        elif st.session_state.chat_mode == "Story Writer":
            st.session_state.messages.append({'role': 'system', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
        elif st.session_state.chat_mode == "Code Writer":
            st.session_state.messages.append({'role': 'system', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
        update_key("pdf")
        st.rerun()

# Main Interface
if st.session_state.chat_mode == "Text Chat":
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
                if message["type"] == "PDF":
                    st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
                elif message["role"] != "system":
                    st.chat_message(message["role"]).markdown(message["content"])
                    if message["role"] == "assistant" and "model" in message:
                        st.caption(f"Generated by: {message['model']}")
        else:
            if message["type"] == "PDF":
                st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
            elif message["role"] != "system":
                st.chat_message(message["role"]).markdown(message["content"])
                if message["role"] == "assistant" and "model" in message:
                    st.caption(f"Generated by: {message['model']}") 
               
elif st.session_state.chat_mode == "Text Adventure Game":
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
                if message["type"] == "PDF":
                    st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
                elif message["role"] != "system":
                    st.chat_message(message["role"]).markdown(message["content"])
                    # Display model name if available for assistant messages
                    if message["role"] == "assistant" and "model" in message:
                        st.caption(f"Generated by: {message['model']}")
        else:
            if message["type"] == "PDF":
                st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
            if message["role"] != "system":
                st.chat_message(message["role"]).markdown(message["content"])
                # Display model name if available for assistant messages
                if message["role"] == "assistant" and "model" in message:
                    st.caption(f"Generated by: {message['model']}")
    
elif st.session_state.chat_mode == "Story Writer":
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
                if message["type"] == "PDF":
                    st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
                elif message["role"] != "system":
                    st.chat_message(message["role"]).markdown(message["content"])
                    # Display model name if available for assistant messages
                    if message["role"] == "assistant" and "model" in message:
                        st.caption(f"Generated by: {message['model']}")
        else:
            if message["type"] == "PDF":
                st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
            if message["role"] != "system":
                st.chat_message(message["role"]).markdown(message["content"])
                # Display model name if available for assistant messages
                if message["role"] == "assistant" and "model" in message:
                    st.caption(f"Generated by: {message['model']}")

elif st.session_state.chat_mode == "Code Writer":
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
                if message["type"] == "PDF":
                    st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
                elif message["role"] != "system":
                    st.chat_message(message["role"]).markdown(message["content"])
                    # Display model name if available for assistant messages
                    if message["role"] == "assistant" and "model" in message:
                        st.caption(f"Generated by: {message['model']}")
        else:
            if message["type"] == "PDF":
                st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
            if message["role"] != "system":
                st.chat_message(message["role"]).markdown(message["content"])
                # Display model name if available for assistant messages
                if message["role"] == "assistant" and "model" in message:
                    st.caption(f"Generated by: {message['model']}")

# Accept user input
input_container = st.empty()
prompt = input_container.chat_input("Enter your message here...",key=32768)
if prompt:
    st.chat_message("user").markdown(prompt)
    progress_bar = st.empty()
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if st.session_state.chat_mode == "Text Chat":
        st.session_state.messages.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
        st.session_state.messages.append({'role': 'user', 'type': 'message', 'content': prompt})
        input_container.empty()
        response = get_text_to_text("text_chat", progress_bar)
    elif st.session_state.chat_mode == "Text Adventure Game":
        st.session_state.messages_text_adventure_game.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
        st.session_state.messages_text_adventure_game.append({'role': 'user', 'type': 'message', 'content': prompt})
        input_container.empty()
        response = get_text_to_text("text_adventure_game", progress_bar)
    elif st.session_state.chat_mode == "Story Writer":
        st.session_state.messages_story_writer.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
        st.session_state.messages_story_writer.append({'role': 'user', 'type': 'message', 'content': prompt})
        input_container.empty()
        response = get_text_to_text("story_writer", progress_bar)
    elif st.session_state.chat_mode == "Code Writer":
        st.session_state.messages_code_writer.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
        st.session_state.messages_code_writer.append({'role': 'user', 'type': 'message', 'content': prompt})
        input_container.empty()
        response = get_text_to_text("code_writer", progress_bar)
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