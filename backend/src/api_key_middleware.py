# backend/src/api_key_middleware.py

import os
from functools import wraps
from flask import request, jsonify

def validate_api_key(f):
    """
    Decorator to validate the API key from the request headers.
    If valid, sets the GROQ_API_KEY environment variable for the duration of the request.

    Special case: If the header contains "USE_OLLAMA=true", we'll allow the request
    without requiring a valid Groq API key.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from request header
        api_key = request.headers.get('X-API-KEY')
        use_ollama = request.headers.get('USE-OLLAMA', '').lower() == 'true'

        # If using Ollama, we don't need a valid Groq API key
        if not api_key and not use_ollama:
            return jsonify({"error": "API key is required. Please provide it in the X-API-KEY header or set USE-OLLAMA header to 'true'."}), 401

        # Store the original API key if it exists
        original_api_key = os.environ.get('GROQ_API_KEY')

        # Set the API key from the request for this request's duration
        if api_key:
            os.environ['GROQ_API_KEY'] = api_key

        # Set a flag to indicate we're using Ollama
        if use_ollama:
            os.environ['USE_OLLAMA'] = 'true'

        try:
            # Call the original function
            result = f(*args, **kwargs)
            return result
        finally:
            # Restore the original API key or remove it if it wasn't set
            if original_api_key:
                os.environ['GROQ_API_KEY'] = original_api_key
            elif 'GROQ_API_KEY' in os.environ and api_key:
                os.environ.pop('GROQ_API_KEY', None)

            # Remove the Ollama flag
            if 'USE_OLLAMA' in os.environ:
                os.environ.pop('USE_OLLAMA', None)

    return decorated_function
