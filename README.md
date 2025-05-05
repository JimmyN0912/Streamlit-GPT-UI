# Streamlit-GPT-UI

A versatile and user-friendly chat interface built with Streamlit that connects to multiple AI model providers. This application allows you to interact with various Large Language Models (LLMs) through a unified interface.

## Features

- **Multiple LLM Provider Support**:
  - Local Model Server (via relay server)
  - Google Gemini
  - Cloudflare Workers AI
  - Cohere
  - OpenRouter
  - Groq
  
- **Chat Interface**:
  - Streaming responses (for local models)
  - Message editing and regeneration
  - Chat history export/import
  - System prompt configuration
  - PDF upload and text extraction

- **Model Configuration**:
  - Temperature and max token adjustment
  - Model selection for each provider
  - Usage statistics tracking

- **Deployment Options**:
  - Docker support
  - GitHub CI/CD workflow
  
## Requirements

- Python 3.13 or higher (Developed with 3.12.8)
- Streamlit
- PyPDF2
- Flask and Waitress (for relay server)
- API keys for various LLM providers
- Docker for containerized deployment

## Installation

### Docker Deployment

1. Make sure Docker and Docker Compose are installed on your system.

2. Create a `.env` file with your API keys.

3. Build and start the containers:
   ```bash
   docker compose up -d --build
   ```

4. Access the application at http://localhost:8501

## Usage

### Selecting a Model Provider

1. Choose your preferred model provider from the sidebar dropdown menu.
2. Select a specific model from the available options for that provider.
3. Adjust temperature and max tokens according to your needs.

### Chat Features

- **System Prompt**: Add instructions that define the AI assistant's behavior at the start of the conversation.
- **Streaming**: Toggle streaming responses (local model only) for word-by-word generation.
- **Edit Message**: Click the ✏️ button to edit your last message.
- **Regenerate**: Click the 🔄️ button to get a new response for the same message.
- **Clear Chat**: Click the 🗑️ button to start a new conversation.
- **Export/Import**: Save and reload your conversations using the 💾 button and file uploader.

### PDF Handling

1. Upload a PDF file using the uploader in the sidebar.
2. The text content will be extracted and added to the chat.
3. Continue the conversation with context from the PDF.

## Local Model Setup

For local model use, you need to run a compatible LLM server that exposes an API endpoint at `http://192.168.0.175:8080/v1/chat/completions`. The relay server communicates with this endpoint to generate responses.

Recommended local server options:
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [LM Studio](https://lmstudio.ai/)
- [Ollama](https://ollama.ai/)
- [LocalAI](https://localai.io/)

## Configuration

The application uses several environment variables that should be set in a `.env` file:

```
# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key
CLOUDFLARE_WORKERS_AI_TOKEN=your_cloudflare_token
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDLFARE_AI_GATEWAY_GATEWAY_ID=your_cloudflare_gateway_id
COHERE_API_KEY=your_cohere_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
GROQ_API_KEY=your_groq_api_key
```

## Docker Containers

The application consists of two Docker containers:
1. **streamlit-app**: The main Streamlit web interface
2. **relay-server**: A Flask server that communicates with your local LLM

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/) for the wonderful web app framework
- All the LLM providers for their APIs
- All the LLM training teams for their hard work and dedication