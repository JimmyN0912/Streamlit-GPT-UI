import streamlit as st
import requests
from os import getenv
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()

# Set up API Credentials
AUTH_TOKEN = getenv("CLOUDFLARE_WORKERS_AI_TOKEN")
ACCOUNT_ID = getenv("CLOUDFLARE_ACCOUNT_ID")
GATEWAY_ID = getenv("CLOUDLFARE_AI_GATEWAY_GATEWAY_ID")
base_url = f"https://gateway.ai.cloudflare.com/v1/{ACCOUNT_ID}/{GATEWAY_ID}/workers-ai/"

# Available Cloudflare models
models = {
    "Llama 4 Scout 17B 16E Instruct": "@cf/meta/llama-4-scout-17b-16e-instruct",
    "Llama 3.3 70B Instruct FP8 Fast": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "Llama 3.1 8B Instruct Fast": "@cf/meta/llama-3.1-8b-instruct-fast",
    "Gemma 3 12B Instruct": "@cf/google/gemma-3-12b-it",
    "Mistral Small 3.1 24B Instruct": "@cf/mistralai/mistral-small-3.1-24b-instruct",
    "QwQ 32B": "@cf/qwen/qwq-32b",
    "Qwen2.5 Coder 32B Instruct": "@cf/qwen/qwen2.5-coder-32b-instruct",
    "Deepseek R1 Distill Qwen 32B": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    "Llama 3.2 1B Instruct": "@cf/meta/llama-3.2-1b-instruct",
    "Llama 3.2 3B Instruct": "@cf/meta/llama-3.2-3b-instruct",
    "Llama 3.1 8B Instruct AWQ": "@cf/meta/llama-3.1-8b-instruct-awq",
    "Llama 3.1 8B Instruct FP8": "@cf/meta/llama-3.1-8b-instruct-fp8",
    "Llama 3.1 8B Instruct": "@cf/meta/llama-3.1-8b-instruct",
    "Llama 3 8B Instruct HF": "@hf/meta-llama/meta-llama-3-8b-instruct",
    "Llama 3 8B Instruct AWQ": "@cf/meta/llama-3-8b-instruct-awq",
    "Llama 3 8B Instruct CF": "@cf/meta/llama-3-8b-instruct",
    "UNA Cybertron 7B V2 BF16": "@cf/fblgit/una-cybertron-7b-v2-bf16",
    "Mistral 7B Instruct v0.2": "@hf/mistral/mistral-7b-instruct-v0.2",
    "Gemma 7B IT Lora": "@cf/google/gemma-7b-it-lora",
    "Gemma 2B IT Lora": "@cf/google/gemma-2b-it-lora",
    "Llama 2 7B Chat HF Lora": "@hf/meta-llama/llama-2-7b-chat-hf-lora",
    "Gemma 7B IT": "@cf/google/gemma-7b-it",
    "Starling LM 7B Beta": "@hf/nexusflow/starling-lm-7b-beta",
    "Hermes 2 Pro Mistral 7B": "@hf/nousresearch/hermes-2-pro-mistral-7b",
    "Mistral 7B Instruct v0.2 Lora": "@cf/mistral/mistral-7b-instruct-v0.2-lora",
    "Qwen1.5 1.8B Chat": "@cf/qwen/qwen1.5-1.8b-chat",
    "Phi-2": "@cf/microsoft/phi-2",
    "Tinyllama 1.1B Chat v1.0": "@cf/tinyllama/tinyllama-1.1b-chat-v1.0",
    "Qwen1.5 14B Chat AWQ": "@cf/qwen/qwen1.5-14b-chat-awq",
    "Qwen1.5 7B Chat AWQ": "@cf/qwen/qwen1.5-7b-chat-awq", 
    "Qwen1.5 0.5B Chat": "@cf/qwen/qwen1.5-0.5b-chat",
    "DiscoLM German 7B v1 AWQ": "@cf/thebloke/discolm-german-7b-v1-awq",
    "Falcon 7B Instruct": "@cf/tiiuae/falcon-7b-instruct",
    "OpenChat 3.5 0106": "@cf/openchat/openchat-3.5-0106",
    "SQLCoder 7B 2": "@cf/defog/sqlcoder-7b-2",
    "Deepseek Math 7B Instruct": "@cf/deepseek-ai/deepseek-math-7b-instruct",
    "Deepseek Coder 6.7B Instruct AWQ": "@hf/thebloke/deepseek-coder-6.7b-instruct-awq",
    "Deepseek Coder 6.7B Base AWQ": "@hf/thebloke/deepseek-coder-6.7b-base-awq",
    "Neural Chat 7B v3 1 AWQ": "@hf/thebloke/neural-chat-7b-v3-1-awq",
    "OpenHermes 2.5 Mistral 7B AWQ": "@hf/thebloke/openhermes-2.5-mistral-7b-awq",
    "Llama 2 13B Chat AWQ": "@hf/thebloke/llama-2-13b-chat-awq",
    "Mistral 7B Instruct v0.1 AWQ": "@hf/thebloke/mistral-7b-instruct-v0.1-awq",
    "Zephyr 7B Beta AWQ": "@hf/thebloke/zephyr-7b-beta-awq",
    "Llama 2 7B Chat FP16": "@cf/meta/llama-2-7b-chat-fp16",
    "Mistral 7B Instruct v0.1": "@cf/mistral/mistral-7b-instruct-v0.1",
    "Llama 2 7B Chat Int8": "@cf/meta/llama-2-7b-chat-int8",
    "Llama 3.1 70B Instruct": "@cf/meta/llama-3.1-70b-instruct"   
}

def get_response(message, progress_bar, message_placeholder=None):
    """Get response from Cloudflare Workers AI API"""

    if "enable_streaming" in st.session_state and st.session_state.enable_streaming:
        return get_streaming_response(message, progress_bar, message_placeholder)

    model = models[st.session_state.cloudflare_model]

    url = base_url + model

    messages = [{"role": msg['role'], "content": msg['content']} for msg in message]
    
    progress_bar.progress(50, "Sending request to Cloudflare Workers AI...")

    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        json={
            "messages": messages,
            "max_tokens": st.session_state.max_tokens,
            "temperature": st.session_state.temperature
        }
    )
    
    progress_bar.progress(90, "Response received, processing...")
    
    if response.status_code == 200:
        response_data = response.json()

        assistant_message = response_data.get('result', {}).get('response', '')
        st.session_state.usage_info = {
            'prompt_tokens': response_data.get('result', {}).get('usage', {}).get('prompt_tokens', 0),
            'completion_tokens': response_data.get('result', {}).get('usage', {}).get('completion_tokens', 0),
            'total_tokens': response_data.get('result', {}).get('usage', {}).get('total_tokens', 0)
        }
        
        st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': "Cloudflare " + st.session_state.cloudflare_model})
        
        progress_bar.progress(100, "Response processed successfully.")
        time.sleep(1)
        progress_bar.empty()
        
        return assistant_message
    
    else:
        st.error(f"Error from Cloudflare API: {response.status_code} - {response.text}")
        progress_bar.empty()
        return None
    
def get_streaming_response(message, progress_bar, message_placeholder):
    """Get streaming response from Cloudflare Workers AI API"""
    model = models[st.session_state.cloudflare_model]

    url = base_url + model

    messages = [{"role": msg['role'], "content": msg['content']} for msg in message]
    
    progress_bar.progress(50, "Sending request to Cloudflare Workers AI...")

    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={
                "messages": messages,
                "max_tokens": st.session_state.max_tokens,
                "temperature": st.session_state.temperature,
                "stream": True
            },
            stream=True
        )
        
        progress_bar.progress(90, "Streaming response...")
        
        if response.status_code == 200:
            assistant_message = ""
            for chunk in response.iter_lines():
                if chunk:
                    chunk_data = chunk.decode('utf-8')
                    if chunk_data.startswith("data:"):
                        try:
                            # Parse the JSON data after "data:" prefix
                            json_str = chunk_data[5:].strip()
                            if json_str == "[DONE]":
                                break
                            
                            chunk_json = json.loads(json_str)
                            if "response" in chunk_json:
                                chunk_text = chunk_json["response"]
                                assistant_message += chunk_text
                                message_placeholder.markdown(assistant_message + "▌")
                            
                            # Update usage info if present
                            if "usage" in chunk_json:
                                st.session_state.usage_info = chunk_json["usage"]
                                
                        except json.JSONDecodeError:
                            continue
            
            message_placeholder.markdown(assistant_message)
            
            st.session_state.messages.append({
                'role': 'assistant', 
                'type': 'message', 
                'content': assistant_message, 
                'model': "Cloudflare " + st.session_state.cloudflare_model
            })
            
            progress_bar.progress(100, "Response processed successfully.")
            time.sleep(1)
            progress_bar.empty()
            
            return assistant_message
        
        else:
            st.error(f"Error from Cloudflare API: {response.status_code} - {response.text}")
            progress_bar.empty()
            return None
        
    except Exception as e:
        st.error(f"Error with streaming: {str(e)}")
        progress_bar.empty()
        return None