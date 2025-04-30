import queue
import threading
import requests
from flask import Flask, request, jsonify, Response
import json
from waitress import serve

app = Flask(__name__)

# Create a queue to hold the requests
request_queue = queue.Queue()
responses = {}
headers = {"Content-Type": "application/json"}

# Connect to your external LLM server
ttt_url = "http://192.168.0.175:8080/v1/chat/completions"

# Function to process requests from the queue
def process_requests():
    while True:
        req_data = request_queue.get()
        if req_data is None:
            break  # Exit the thread if None is received

        request_id = req_data['request_id']
        print(f'Processing request {request_id}... Queue size: {request_queue.qsize() + 1}')
        text = req_data['text']
        max_tokens = req_data['max_tokens']
        temperature = req_data['temperature']
        data = {
            "mode": "instruct",
            "messages": text,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            response = requests.post(ttt_url, headers=headers, json=data, timeout=300)
            response.raise_for_status()  # Raise an exception for HTTP errors
            response_json = response.json()

            # Extract and display the usage part
            usage = response_json.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 'N/A')
            completion_tokens = usage.get('completion_tokens', 'N/A')
            total_tokens = usage.get('total_tokens', 'N/A')

            assistant_message = response_json["choices"][0]["message"]["content"]

            # Store the response
            responses[request_id] = {
                'assistant_message': assistant_message,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
            }
        except requests.exceptions.RequestException as e:
            # Handle request exceptions
            responses[request_id] = {
                'error': str(e)
            }
        except ValueError:
            # Handle JSON decode error
            responses[request_id] = {
                'error': 'Invalid JSON response'
            }

        print(f'Request {request_id} processing complete. Queue size: {request_queue.qsize()}')
        request_queue.task_done()

# Start a worker thread to process the requests
worker_thread = threading.Thread(target=process_requests, daemon=True)
worker_thread.start()

@app.route('/relay', methods=['POST'])
def relay():
    req_data = request.get_json()
    text = req_data['text']
    request_id = req_data['request_id']
    max_tokens = req_data['max_tokens']
    temperature = req_data['temperature']
    request_queue.put({'text': text, 'request_id': request_id, 'max_tokens': max_tokens, 'temperature': temperature})
    queue_position = request_queue.qsize()
    return jsonify({'status': 'queued', 'position': queue_position})

@app.route('/stream', methods=['POST'])
def stream():
    """Endpoint for streaming responses directly from the LLM server"""
    req_data = request.get_json()
    text = req_data['text']
    request_id = req_data['request_id']
    max_tokens = req_data['max_tokens']
    temperature = req_data['temperature']
    
    # Set up the request to the LLM server with streaming enabled
    data = {
        "mode": "instruct",
        "messages": text,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True  # Enable streaming from the LLM server
    }
    
    # Create a generator function that yields streamed chunks
    def generate():
        try:
            # Make request to LLM server with streaming=True
            response = requests.post(ttt_url, headers=headers, json=data, stream=True)
            response.raise_for_status()
            
            # Record statistics for token usage tracking
            token_stats = {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }
            
            # Stream each chunk with proper SSE format
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data:'):
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            json_data = json.loads(chunk)
                            
                            # Track token usage if available in response
                            if 'usage' in json_data:
                                usage = json_data['usage']
                                token_stats['prompt_tokens'] = usage.get('prompt_tokens', 0)
                                token_stats['completion_tokens'] = usage.get('completion_tokens', 0)
                                token_stats['total_tokens'] = usage.get('total_tokens', 0)
                            
                            # Format as SSE event and yield
                            yield f"data: {json.dumps(json_data)}\n\n"
                        except json.JSONDecodeError:
                            pass
                    
            # Store final usage statistics for later retrieval
            responses[request_id] = {
                'prompt_tokens': token_stats['prompt_tokens'],
                'completion_tokens': token_stats['completion_tokens'],
                'total_tokens': token_stats['total_tokens'],
            }
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"
            responses[request_id] = {'error': str(e)}
    
    # Return a streaming response
    return Response(generate(), mimetype='text/event-stream')

@app.route('/status/<request_id>', methods=['GET'])
def get_status(request_id):
    if request_id in responses:
        return jsonify({'status': 'completed'})
    else:
        for item in list(request_queue.queue):
            if item['request_id'] == request_id:
                return jsonify({'status': 'queued'})
        return jsonify({'status': 'processing'})

@app.route('/response/<request_id>', methods=['GET'])
def get_response(request_id):
    if request_id in responses:
        return jsonify(responses.pop(request_id))
    else:
        return jsonify({'status': 'pending'}), 202

@app.route('/queue_size', methods=['GET'])
def get_queue_size():
    return jsonify({'queue_size': request_queue.qsize()})

# Ensure the worker thread exits cleanly when the application stops
def stop_worker_thread():
    request_queue.put(None)
    worker_thread.join()

# Register the stop function to be called when the script exits
import atexit
atexit.register(stop_worker_thread)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)