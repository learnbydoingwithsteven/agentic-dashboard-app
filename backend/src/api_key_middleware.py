# backend/src/api_key_middleware.py

import os
from functools import wraps
from flask import request, jsonify

def validate_api_key(f):
    """
    Decorator to validate the API key from the request headers.
    If valid, sets the GROQ_API_KEY environment variable for the duration of the request.

    Special case: If the header contains "USE-OLLAMA=true", we'll allow the request
    without requiring a valid Groq API key and set up for Ollama usage.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from request header
        api_key = request.headers.get('X-API-KEY')
        use_ollama_header = request.headers.get('USE-OLLAMA', '').lower()
        use_ollama = use_ollama_header == 'true'

        # Log the headers for debugging
        print(f"Request headers: X-API-KEY: {'[PRESENT]' if api_key else '[MISSING]'}, USE-OLLAMA: {use_ollama}")

        # If using Ollama, we don't need a valid Groq API key
        if not api_key and not use_ollama:
            return jsonify({"error": "API key is required. Please provide it in the X-API-KEY header or set USE-OLLAMA header to 'true'."}), 401

        # Store the original environment variables
        original_api_key = os.environ.get('GROQ_API_KEY')
        original_use_ollama = os.environ.get('USE_OLLAMA')

        # Always clear and set environment variables to ensure we're using the correct ones
        # This prevents issues with stale environment variables

        # First, clear any existing environment variables
        if 'GROQ_API_KEY' in os.environ:
            os.environ.pop('GROQ_API_KEY', None)
        if 'USE_OLLAMA' in os.environ:
            os.environ.pop('USE_OLLAMA', None)

        # Set the API key from the request for this request's duration
        if api_key:
            os.environ['GROQ_API_KEY'] = api_key
            print(f"Set GROQ_API_KEY environment variable for this request")

        # Explicitly handle the USE-OLLAMA header
        # If the header is present (even if it's 'false'), we'll respect that value
        if use_ollama_header:
            if use_ollama:
                os.environ['USE_OLLAMA'] = 'true'
                print(f"Set USE_OLLAMA=true environment variable for this request")

                # If we're using Ollama and don't have an API key, set a dummy one to avoid errors
                if not api_key:
                    os.environ['GROQ_API_KEY'] = 'dummy_key_for_ollama'
                    print(f"Set dummy GROQ_API_KEY for Ollama usage")
            else:
                # Explicitly set USE_OLLAMA to 'false' if the header is 'false'
                os.environ['USE_OLLAMA'] = 'false'
                print(f"Set USE_OLLAMA=false environment variable for this request")

                # Make sure we have a valid API key when not using Ollama
                if not api_key:
                    return jsonify({"error": "API key is required when not using Ollama."}), 401

        try:
            # Call the original function
            result = f(*args, **kwargs)
            return result
        finally:
            # Restore the original environment
            if original_api_key:
                os.environ['GROQ_API_KEY'] = original_api_key
            elif 'GROQ_API_KEY' in os.environ and (api_key or use_ollama):
                os.environ.pop('GROQ_API_KEY', None)

            # Restore the original USE_OLLAMA flag
            if original_use_ollama:
                os.environ['USE_OLLAMA'] = original_use_ollama
            elif 'USE_OLLAMA' in os.environ:
                os.environ.pop('USE_OLLAMA', None)

    return decorated_function
