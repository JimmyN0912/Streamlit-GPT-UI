import streamlit as st
import json
import datetime
import os

# Import our modules
from utils.constants import (TEXT_CHAT_DEFAULT)
from utils.pdf_utils import pdf_to_text
from utils.chat_utils import update_key, get_text_to_text, export_conversations, import_conversations
from utils import check_model
from api import gemini, cloudflare, cohere, openrouter, groq

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = TEXT_CHAT_DEFAULT.copy()

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""

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

if "enable_streaming" not in st.session_state:
    st.session_state.enable_streaming = True

if "docker_mode" not in st.session_state:
    st.session_state.docker_mode = os.environ.get("IN_DOCKER") == "true"

if "autosave_path" not in st.session_state:
    # Default path that works well on Windows
    st.session_state.autosave_path = "F:\\chats\\conversations.json"

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "model_provider" not in st.session_state:
    st.session_state.model_provider = "Local Model"

if "local_model" not in st.session_state:
    st.session_state.local_model = None

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
    st.session_state.local_model = check_model.get_current_model_name()
    if st.session_state.local_model == None:
        st.badge("Local Model is not running. Please check the model server.")
    else:
        st.badge(f"Current AI Model: {st.session_state.local_model}")
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
        options=["Local Model", "Google Gemini", "Cloudflare Workers AI", "Cohere", "OpenRouter", "Groq"]
    )
    
    # Add system prompt input
    system_prompt = st.text_area(
        label="System Prompt",
        help="Set a system prompt that will be included at the beginning of each conversation. Leave empty for no system prompt.",
        value=st.session_state.system_prompt,
        placeholder="Example: You are a helpful assistant who specializes in programming...",
        height=100
    )
    # Update session state if the prompt has changed
    if system_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = system_prompt
    
    # Add streaming toggle (only for Local Model)
    if st.session_state.model_provider == "Local Model":
        st.session_state.enable_streaming = st.toggle(
            label="Enable Streaming",
            help="Enable streaming responses that appear word by word instead of all at once.",
            value=st.session_state.enable_streaming
        )
    else:
        # Reset streaming to false when not using Local Model
        st.session_state.enable_streaming = False
    
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
    
    # Different autosave UI based on Docker or local mode
    if st.session_state.docker_mode:
        st.info("Running in Docker mode. History will be saved in the container and available for download.")
        if st.session_state.autosave:
            st.download_button(
                label="📥 Download Current Autosave",
                help="Download the current autosaved conversation to your local machine",
                data=export_conversations(),
                file_name="conversations.json",
                mime="application/json"
            )
    else:
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
        min_value=1024, 
        max_value=16384, 
        value=8192, 
        step=256)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        if st.button(
            label="❌",
            help="Remove the previous user message and assistant response."):
            st.session_state.messages = st.session_state.messages[:-2]
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
            st.session_state.messages = st.session_state.messages[:-1]
            response = get_text_to_text("text_chat", progress_bar)
            st.rerun()
    with col4:
        if st.button(
        label="🗑️",
        help="Start a new conversation."):
            st.session_state.messages = TEXT_CHAT_DEFAULT.copy()
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
    
    upload_pdf = st.file_uploader(
    label = "Upload a PDF file", 
    help="Upload a PDF file to the chat. Only text content will be extracted from the PDF file.",
    type=["pdf"],
    accept_multiple_files=False,
    key=st.session_state.pdf_uploader_key)
    if upload_pdf:
        text = pdf_to_text(upload_pdf)
        st.session_state.messages.append({'role': 'user', 'type': 'PDF', 'file_name': upload_pdf.name, 'content': f"PDF File Content:\n\n{text}"})
        update_key("pdf")
        st.rerun()

# Main Interface
total_messages = len(st.session_state.messages)
for index, message in enumerate(st.session_state.messages):
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
                if message.get("reasoning"):
                    st.chat_message("assistant").expander("Reasoning", expanded=False).markdown(message["reasoning"])
                st.chat_message(message["role"]).markdown(message["content"])
                if message["role"] == "assistant" and "model" in message:
                    st.caption(f"Generated by: {message['model']}")
    else:
        if message["type"] == "PDF":
            st.chat_message("user").expander(message["file_name"], expanded=False).markdown(message["content"])
        elif message["role"] != "system":
            if message.get("reasoning"):
                st.chat_message("assistant").expander("Reasoning", expanded=False).markdown(message["reasoning"])
            st.chat_message(message["role"]).markdown(message["content"])
            if message["role"] == "assistant" and "model" in message:
                st.caption(f"Generated by: {message['model']}")

# Accept user input
input_container = st.empty()
prompt = input_container.chat_input("Enter your message here...",key=32768)
if prompt:
    st.chat_message("user").markdown(prompt)
    progress_bar = st.empty()
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # If user has set a system prompt, include it at the beginning of the current conversation
    if st.session_state.system_prompt:
        # Check if we need to add the system prompt (if it's not already the first message)
        if not (len(st.session_state.messages) > 0 and 
                st.session_state.messages[0].get('role') == 'system' and 
                st.session_state.messages[0].get('content') == st.session_state.system_prompt):
            # Insert system prompt at beginning of messages
            st.session_state.messages.insert(0, {
                'role': 'system', 
                'type': 'message', 
                'content': st.session_state.system_prompt
            })
    
    # Add date and user message
    st.session_state.messages.append({'role': 'system', 'type': 'message', 'content': "Current Date and Time: " + current_date})
    st.session_state.messages.append({'role': 'user', 'type': 'message', 'content': prompt})
    input_container.empty()
    response = get_text_to_text("text_chat", progress_bar)
    
    if st.session_state.autosave:
        if st.session_state.docker_mode:
            autosave_path = "/app/data/conversations.json"
        else:
            autosave_path = st.session_state.autosave_path
        with open(autosave_path, 'w') as f:
            json.dump(st.session_state.messages, f, indent=4)
    st.rerun()