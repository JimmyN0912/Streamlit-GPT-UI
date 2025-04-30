FROM python:3.13-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory for chat history
RUN mkdir -p /app/data

# Copy source code
COPY . .

# Expose port for Streamlit
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the streamlit app
CMD ["streamlit", "run", "main_interface.py", "--server.port=8501", "--server.address=0.0.0.0"]