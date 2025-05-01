# backend/src/ollama_config.py

import requests
import json
import os

# Default Ollama server URL
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Function to check if Ollama is running
def is_ollama_available():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False

# Function to get available Ollama models
def get_ollama_models():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            data = response.json()
            models = {}
            for model in data.get('models', []):
                model_name = model.get('name')
                if model_name:
                    # Use the model name as both key and display name
                    models[f"ollama:{model_name}"] = f"Ollama: {model_name}"
            return models
        return {}
    except Exception as e:
        print(f"Error fetching Ollama models: {e}")
        return {}

# Function to get Ollama LLM config for Autogen
def get_ollama_config(model_name):
    # Remove the "ollama:" prefix if present
    if model_name.startswith("ollama:"):
        model_name = model_name[7:]
    
    return [
        {
            "model": model_name,
            "base_url": f"{OLLAMA_BASE_URL}/v1",
            "api_type": "openai",
            "api_key": "ollama",  # Ollama doesn't need an API key, but we need to provide something
            "timeout": 120.0
        }
    ]

# Initialize available Ollama models
OLLAMA_MODELS = get_ollama_models() if is_ollama_available() else {}
