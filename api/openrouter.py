import streamlit as st
import requests
from os import getenv
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()

# Set up API Credentials
OPENROUTER_API_KEY = getenv("OPENROUTER_API_KEY")
ACCOUNT_ID = getenv("CLOUDFLARE_ACCOUNT_ID")
GATEWAY_ID = getenv("CLOUDLFARE_AI_GATEWAY_GATEWAY_ID")
url = f"https://gateway.ai.cloudflare.com/v1/{ACCOUNT_ID}/{GATEWAY_ID}/openrouter/v1/chat/completions"

# Available OpenRouter models
models = {
    "NVIDIA Llama 3.3 Nemotron Super 49B v1": "nvidia/llama-3.3-nemotron-super-49b-v1:free",
    "NVIDIA Llama 3.1 Nemotron Ultra 253B V1": "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
    "NVIDIA Llama 3.1 Nemotron 70B Instruct": "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "NVIDIA Llama 3.1 Nemotron Nano 8B v1": "nvidia/llama-3.1-nemotron-nano-8b-v1:free",
    "Deepseek V3 0324": "deepseek/deepseek-chat-v3-0324:free",
    "Deepseek R1": "deepseek/deepseek-r1:free",
    "Deepseek V3": "deepseek/deepseek-chat:free",
    "Deepseek V3 Base": "deepseek/deepseek-v3-base:free",
    "Deepseek R1 Zero": "deepseek/deepseek-r1-zero:free",
    "Deepseek R1 Distill Llama 70B": "deepseek/deepseek-r1-distill-llama-70b:free",
    "Deepseek R1 Distill Qwen 32B": "deepseek/deepseek-r1-distill-qwen-32b:free",
    "Deepseek R1 Distill Qwen 14B": "deepseek/deepseek-r1-distill-qwen-14b:free",
    "Qwen QwQ 32B": "qwen/qwq-32b:free",
    "Qwen QwQ 32B Preview": "qwen/qwq-32b-preview:free",
    "Qwen2.5 VL 72B Instruct": "qwen/qwen2.5-vl-72b-instruct:free",
    "Qwen2.5 VL 32B Instruct": "qwen/qwen2.5-vl-32b-instruct:free",
    "Qwen2.5 VL 7B Instruct": "qwen/qwen2.5-vl-7b-instruct:free",
    "Qwen2.5 VL 3B Instruct": "qwen/qwen2.5-vl-3b-instruct:free",
    "Qwen2.5 72B Instruct": "qwen/qwen2.5-72b-instruct:free",
    "Qwen2.5 7B Instruct": "qwen/qwen2.5-7b-instruct:free",
    "Qwen2.5 Coder 32B Instruct": "qwen/qwen2.5-coder-32b-instruct:free",
    "Meta Llama 4 Scout": "meta-llama/llama-4-scout:free",
    "Meta Llama 4 Maverick": "meta-llama/llama-4-maverick:free",
    "Meta Llama 3.3 70B Instruct": "meta-llama/llama-3.3-70b-instruct:free",
    "Meta Llama 3.2 11B Vision Instruct": "meta-llama/llama-3.2-11b-vision-instruct:free",
    "Meta Llama 3.2 3B Instruct": "meta-llama/llama-3.2-3b-instruct:free",
    "Meta Llama 3.2 1B Instruct": "meta-llama/llama-3.2-1b-instruct:free",
    "Meta Llama 3.1 8B Instruct": "meta-llama/llama-3.1-8b-instruct:free",
    "Google Gemma 3 27B": "google/gemma-3-27b-it:free",
    "Google Gemma 3 12B": "google/gemma-3-12b-it:free",
    "Google Gemma 3 4B": "google/gemma-3-4b-it:free",
    "Google Gemma 3 1B": "google/gemma-3-1b-it:free",
    "Google Gemma 2 9B": "google/gemma-2-9b-it:free",
    "Google LearnLM 1.5 Pro Experimental": "google/learnlm-1.5-pro-experimental:free",
    "Mistral Nemo": "mistralai/mistral-nemo:free",
    "Mistral Small 3.1 24B": "mistralai/mistral-small-3.1-24b-instruct:free",
    "Mistral Small 3": "mistralai/mistral-small-24B-Instruct-2501:free",
    "Mistral 7B Instruct": "mistralai/mistral-7b-instruct:free",
    "Hugging Face Zephyr 7B": "huggingfaceh4/zephyr-7b-beta:free",
    "Moonshot AI Kimi VL A3B Thinking": "moonshotai/kimi-vl-a3b-thinking:free",
    "Moonshot AI Moonlight 16B A3B Instruct": "moonshotai/moonlight-16b-a3b-instruct:free",
    "Sophosympatheia Rogue Rose 103B v0.2": "sophosympatheia/rogue-rose-103b-v0.2:free",
    "Cognitivecomputations Dolphin3.0 Mistral 24B": "cognitivecomputations/dolphin3.0-mistral-24b:free",
    "Cognitivecomputations Dolphin3.0 R1 Mistral 24B": "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
    "Open-r1 OlympicCoder 32B": "open-r1/open-r1-olympiccoder-32b:free",
    "Open-r1 OlympicCoder 7B": "open-r1/open-r1-olympiccoder-7b:free",
    "Nous DeepHermes 3 Llama 3 8B Preview": "nousresearch/deephermes-3-llama-3-8b-preview:free",
    "Bytedance UI-TARS 72B": "bytedance-research/ui-tars-72b:free",
    "Reka Flash 3": "rekaai/reka-flash-3:free",
    "Featherless Qwerky 72B": "featherless/qwerky-72b:free",
    "AllenAI Molmo 7B D": "allenai/molmo-7b-d:free",
}

def get_response(message, progress_bar, message_placeholder=None):
    """Get response from Openrouter API"""

    if "enable_streaming" in st.session_state and st.session_state.enable_streaming:
        return get_streaming_response(message, progress_bar, message_placeholder)

    model = models[st.session_state.openrouter_model]

    messages = [{"role": msg['role'], "content": msg['content']} for msg in message]
    
    progress_bar.progress(50, "Sending request to Openrouter API...")
    
    response = requests.post(
        url=url,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": model,
            "messages": messages,
            "max_tokens": st.session_state.max_tokens,
            "temperature": st.session_state.temperature,
        }
    )
    
    progress_bar.progress(90, "Response received, processing...")
    
    if response.status_code == 200:
        response_data = response.json()

        assistant_message = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
        st.session_state.usage_info = {
            'prompt_tokens': response_data.get('usage', {}).get('prompt_tokens', 0),
            'completion_tokens': response_data.get('usage', {}).get('completion_tokens', 0),
            'total_tokens': response_data.get('usage', {}).get('total_tokens', 0)
        }
        
        if response_data['choices'][0]['message']['reasoning']:
            st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'reasoning': response_data['choices'][0]['message']['reasoning'], 'model': "OpenRouter " + st.session_state.openrouter_model})
        else:
            st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': "OpenRouter " + st.session_state.openrouter_model})
            
        progress_bar.progress(100, "Response processed successfully.")
        time.sleep(1)
        progress_bar.empty()

        return assistant_message
    else:
        st.error(f"Error from Openrouter API: {response.status_code} - {response.text}")
        progress_bar.empty()
        return None
    
def get_streaming_response(message, progress_bar, message_placeholder):
    """Get streaming response from Openrouter API"""
    model = models[st.session_state.openrouter_model]

    messages = [{"role": msg['role'], "content": msg['content']} for msg in message]
    
    progress_bar.progress(50, "Sending request to Openrouter API...")
    
    response = requests.post(
        url=url,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": model,
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
                if 'data: ' in chunk_data:
                    data = chunk_data.split('data: ')[1]
                    if data == '[DONE]':
                        break
                    else:
                        try:
                            json_data = json.loads(data)
                            content = json_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            if content:
                                assistant_message += content
                                message_placeholder.markdown(assistant_message + "▌")
                            last_chunk_data = json_data
                        except json.JSONDecodeError:
                            pass
        if last_chunk_data and 'usage' in last_chunk_data:
            st.session_state.usage_info = {
                'prompt_tokens': last_chunk_data.get('usage', {}).get('prompt_tokens', 0),
                'completion_tokens': last_chunk_data.get('usage', {}).get('completion_tokens', 0),
                'total_tokens': last_chunk_data.get('usage', {}).get('total_tokens', 0)
            }
        else:
            st.session_state.usage_info = {
                'prompt_tokens': "N/A",
                'completion_tokens': "N/A",
                'total_tokens': "N/A"
            }
        
        st.session_state.messages.append({'role': 'assistant', 'type': 'message', 'content': assistant_message, 'model': "OpenRouter " + st.session_state.openrouter_model})
        
        progress_bar.progress(100, "Response processed successfully.")
        time.sleep(1)
        progress_bar.empty()

        return assistant_message
    else:
        st.error(f"Error from Openrouter API: {response.status_code} - {response.text}")
        progress_bar.empty()
        return None