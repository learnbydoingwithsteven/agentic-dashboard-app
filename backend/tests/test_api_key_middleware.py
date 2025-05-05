import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify, request

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.api_key_middleware import validate_api_key

class TestApiKeyMiddleware(unittest.TestCase):
    def setUp(self):
        # Create a Flask app for testing
        self.app = Flask(__name__)
        
        # Store original environment variables
        self.original_api_key = os.environ.get('GROQ_API_KEY')
        self.original_use_ollama = os.environ.get('USE_OLLAMA')
        
        # Create a test route with the middleware
        @self.app.route('/test')
        @validate_api_key
        def test_route():
            return jsonify({
                'api_key': os.environ.get('GROQ_API_KEY'),
                'use_ollama': os.environ.get('USE_OLLAMA')
            })
        
        # Create a test client
        self.client = self.app.test_client()
    
    def tearDown(self):
        # Restore original environment variables
        if self.original_api_key:
            os.environ['GROQ_API_KEY'] = self.original_api_key
        elif 'GROQ_API_KEY' in os.environ:
            os.environ.pop('GROQ_API_KEY')
            
        if self.original_use_ollama:
            os.environ['USE_OLLAMA'] = self.original_use_ollama
        elif 'USE_OLLAMA' in os.environ:
            os.environ.pop('USE_OLLAMA')
    
    def test_missing_api_key(self):
        """Test that a request without an API key is rejected."""
        # Make a request without an API key
        response = self.client.get('/test')
        
        # Check that the response is a 401 Unauthorized
        self.assertEqual(response.status_code, 401)
        
        # Check that the response contains an error message
        self.assertIn('API key is required', response.json['error'])
    
    def test_valid_api_key(self):
        """Test that a request with a valid API key is accepted."""
        # Make a request with an API key
        response = self.client.get('/test', headers={'X-API-KEY': 'test_key'})
        
        # Check that the response is a 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the API key was set in the environment
        self.assertEqual(response.json['api_key'], 'test_key')
    
    def test_use_ollama_true(self):
        """Test that a request with USE-OLLAMA=true is accepted without an API key."""
        # Make a request with USE-OLLAMA=true
        response = self.client.get('/test', headers={'USE-OLLAMA': 'true'})
        
        # Check that the response is a 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that USE_OLLAMA was set to 'true' in the environment
        self.assertEqual(response.json['use_ollama'], 'true')
        
        # Check that a dummy API key was set
        self.assertEqual(response.json['api_key'], 'dummy_key_for_ollama')
    
    def test_use_ollama_false(self):
        """Test that a request with USE-OLLAMA=false requires an API key."""
        # Make a request with USE-OLLAMA=false but no API key
        response = self.client.get('/test', headers={'USE-OLLAMA': 'false'})
        
        # Check that the response is a 401 Unauthorized
        self.assertEqual(response.status_code, 401)
        
        # Check that the response contains an error message
        self.assertIn('API key is required when not using Ollama', response.json['error'])
    
    def test_use_ollama_false_with_api_key(self):
        """Test that a request with USE-OLLAMA=false and an API key is accepted."""
        # Make a request with USE-OLLAMA=false and an API key
        response = self.client.get('/test', headers={
            'USE-OLLAMA': 'false',
            'X-API-KEY': 'test_key'
        })
        
        # Check that the response is a 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that USE_OLLAMA was set to 'false' in the environment
        self.assertEqual(response.json['use_ollama'], 'false')
        
        # Check that the API key was set in the environment
        self.assertEqual(response.json['api_key'], 'test_key')
    
    def test_environment_restoration(self):
        """Test that the environment is restored after the request."""
        # Set initial environment variables
        os.environ['GROQ_API_KEY'] = 'original_key'
        os.environ['USE_OLLAMA'] = 'original_value'
        
        # Make a request with different values
        self.client.get('/test', headers={
            'USE-OLLAMA': 'true',
            'X-API-KEY': 'test_key'
        })
        
        # Check that the environment was restored
        self.assertEqual(os.environ.get('GROQ_API_KEY'), 'original_key')
        self.assertEqual(os.environ.get('USE_OLLAMA'), 'original_value')

if __name__ == '__main__':
    unittest.main()
