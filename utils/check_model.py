import requests
import streamlit as st

url = "http://192.168.0.175:8080/v1/models"
headers = {"Content-Type": "application/json"}

def get_current_model_name():
    try:
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            response_json = response.json()
            model_path = response_json["data"][0]["id"]
            # Extract the model name from the path
            model_name = model_path.split("/")[-1].split("\\")[-1]
            return model_name
        else:
            return None
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        print(f"Error connecting to the server: {e}")
        st.toast("Couldn't connect to local LLM server.")
        return None