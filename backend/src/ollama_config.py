# backend/src/ollama_config.py

import requests
import json
import os

# Default Ollama server URL
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Function to check if Ollama is running
def is_ollama_available():
    # First try using the CLI command
    try:
        import subprocess
        print("Checking if Ollama is available using CLI command...")
        result = subprocess.run(['ollama', 'list'],
                               capture_output=True,
                               text=True,
                               check=False,
                               timeout=3)

        if result.returncode == 0:
            print("Ollama is available (CLI check successful)")
            return True
        else:
            print(f"Ollama CLI check failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            # Continue to API check as fallback
    except Exception as e:
        print(f"Error checking Ollama via CLI: {e}")
        # Continue to API check as fallback

    # Fallback: Try using the API
    try:
        print("Falling back to API check for Ollama availability...")
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        is_available = response.status_code == 200
        print(f"Ollama API check result: {'Available' if is_available else 'Not available'}")
        return is_available
    except Exception as e:
        print(f"Ollama API check failed: {e}")
        return False

# Function to get available Ollama models
def get_ollama_models():
    models = {}

    # First try using the CLI command (more reliable)
    try:
        import subprocess
        import json

        print("Checking for Ollama models using 'ollama list' command...")
        result = subprocess.run(['ollama', 'list'],
                               capture_output=True,
                               text=True,
                               check=False)

        if result.returncode == 0 and result.stdout.strip():
            # Parse the text output (format: NAME TAG SIZE MODIFIED)
            try:
                # Skip the header line
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Skip the header line (NAME TAG SIZE MODIFIED)
                    for line in lines[1:]:
                        if line.strip():
                            # Split by whitespace and get the first column (NAME)
                            parts = line.split()
                            if len(parts) >= 1:
                                model_name = parts[0]
                                # Use the model name as both key and display name
                                models[f"ollama:{model_name}"] = f"Ollama: {model_name}"

                print(f"Found {len(models)} Ollama models via CLI: {list(models.keys())}")
                return models
            except Exception as e:
                print(f"Error parsing Ollama CLI output: {e}")
                # Continue to API method as fallback
        else:
            print(f"Ollama CLI command failed or returned no models. Return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            # Continue to API method as fallback
    except Exception as e:
        print(f"Error running Ollama CLI command: {e}")
        # Continue to API method as fallback

    # Fallback: Try using the API
    try:
        print("Falling back to Ollama API to get models...")
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            data = response.json()
            for model in data.get('models', []):
                model_name = model.get('name')
                if model_name:
                    # Use the model name as both key and display name
                    models[f"ollama:{model_name}"] = f"Ollama: {model_name}"
            print(f"Found {len(models)} Ollama models via API: {list(models.keys())}")
            return models
        else:
            print(f"Ollama API returned status code: {response.status_code}")
        return models  # Return whatever models we found, even if empty
    except Exception as e:
        print(f"Error fetching Ollama models via API: {e}")
        return models  # Return whatever models we found, even if empty

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
