# backend/src/main.py

import sys
import os
from datetime import datetime
# Add the project root to the Python path to allow absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check if GROQ_API_KEY is set
if not os.getenv("GROQ_API_KEY"):
    print("*** WARNING: GROQ_API_KEY environment variable is not set. Visualization generation will fail. ***")
    print("Please set it using: export GROQ_API_KEY='your_groq_api_key'")

from flask import Flask, request, jsonify
from flask_cors import CORS
import werkzeug.utils

# Import the agent service function and logs
from src.agent_service import get_visualization_suggestions, AVAILABLE_MODELS, get_api_key, fetch_available_models, agent_logs
# Import API key middleware
from src.api_key_middleware import validate_api_key

app = Flask(__name__)

# Configure CORS to allow requests from the React frontend (adjust origin in production)
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Allow all origins for development

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 # 16 MB limit

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store the path of the last uploaded file (simple approach for single user)
# In a real multi-user app, this would need a more robust session/user-based mechanism
last_uploaded_file_path = None

def log_agent_activity(timestamp, activity_type, content, step):
    global agent_logs
    log_entry = {
        "timestamp": timestamp,
        "type": activity_type,
        "content": content,
        "step": step
    }
    agent_logs.append(log_entry)
    # Keep only the last 1000 logs
    if len(agent_logs) > 1000:
        agent_logs = agent_logs[-1000:]

@app.route("/api/upload", methods=["POST"])
@validate_api_key
def upload_file():
    global last_uploaded_file_path
    print("\n--- /api/upload endpoint hit ---") # Add very early log
    try:
        print(f"Request Headers: {request.headers}") # Log headers
        print(f"Files in request: {request.files.keys()}")

        if 'file' not in request.files:
            print("No file part in request")
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        print(f"Received file: {file.filename}")

        if file.filename == '':
            print("Empty filename")
            return jsonify({"error": "No selected file"}), 400

        if file:
            # Secure the filename
            filename = werkzeug.utils.secure_filename(file.filename)
            print(f"Secure filename: {filename}")

            # Ensure it's a CSV
            if not filename.lower().endswith(".csv"):
                print("Invalid file type")
                return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            print(f"Saving file to: {filepath}")

            try:
                file.save(filepath)
                print(f"File saved successfully")
                last_uploaded_file_path = filepath # Store the path
                return jsonify({"message": "File uploaded successfully", "filename": filename, "filepath": filepath}), 200
            except Exception as e:
                print(f"Error saving file: {str(e)}")
                return jsonify({"error": f"Failed to save file: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error in upload: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/")
def root():
    return jsonify({
        "status": "ok",
        "message": "Agentic Visualization API is running",
        "endpoints": {
            "upload": "/api/upload",
            "visualizations": "/api/visualizations",
            "prompted_visualizations": "/api/visualizations/prompt",
            "check_api_key": "/api/check_api_key"
        }
    })

@app.route("/api/check_api_key", methods=["GET"])
@validate_api_key
def check_api_key():
    """Check if the provided API key is valid by attempting to fetch models from Groq."""
    try:
        # This will use the API key from the request header (set by the middleware)
        fetch_available_models()

        # Check if we have any models available
        if AVAILABLE_MODELS:
            return jsonify({
                "status": "success",
                "message": "API key is valid or Ollama models are available",
                "available_models": AVAILABLE_MODELS
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No models available. Please check your API key or ensure Ollama is running."
            }), 401
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"API key validation failed: {str(e)}"
        }), 401

@app.route("/api/admin/logs", methods=["GET"])
@validate_api_key
def get_admin_logs():
    """Get agent activity logs."""
    return jsonify({
        # Pass the agent_logs which now contain conversation details
        "logs": agent_logs,
        "available_models": AVAILABLE_MODELS
    })

@app.route("/api/visualizations", methods=["GET"])
@validate_api_key
def get_initial_visualizations():
    """Get initial visualization suggestions based on the uploaded dataset."""
    if not last_uploaded_file_path:
        return jsonify({"error": "No dataset uploaded yet."}), 400

    # Get models from query parameters, default to llama3-70b-8192 for both
    analyst_model_id = request.args.get("analyst_model", "llama3-70b-8192")
    coder_model_id = request.args.get("coder_model", "llama3-70b-8192")

    if analyst_model_id not in AVAILABLE_MODELS:
        return jsonify({"error": f"Invalid analyst model ID: {analyst_model_id}. Available models: {list(AVAILABLE_MODELS.keys())}"}), 400
    if coder_model_id not in AVAILABLE_MODELS:
        return jsonify({"error": f"Invalid coder model ID: {coder_model_id}. Available models: {list(AVAILABLE_MODELS.keys())}"}), 400

    try:
        print(f"Requesting initial visualizations with Analyst: {analyst_model_id}, Coder: {coder_model_id}")
        results = get_visualization_suggestions(
            last_uploaded_file_path,
            analyst_model_id=analyst_model_id,
            coder_model_id=coder_model_id
        )
        return jsonify(results), 200 if "error" not in results else 500
    except Exception as e:
        return jsonify({"error": f"Failed to get initial visualizations: {str(e)}"}), 500

@app.route("/api/visualizations/prompt", methods=["POST"])
@validate_api_key
def get_prompted_visualization():
    global last_uploaded_file_path
    if not last_uploaded_file_path:
        # Try using the default dataset if no file uploaded yet
        # Construct path relative to the backend directory
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        default_filename = '2015---Friuli-Venezia-Giulia---Gestione-finanziaria-Spese-Enti-Locali.csv'
        default_path = os.path.join(backend_dir, 'uploads', default_filename)
        if os.path.exists(default_path):
            last_uploaded_file_path = default_path
            print(f"No file uploaded, using default: {default_path}")
        else:
            return jsonify({"error": "No dataset has been uploaded or found."}), 400

    if not os.path.exists(last_uploaded_file_path):
        return jsonify({"error": f"Dataset file not found at {last_uploaded_file_path}"}), 404

    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing 'prompt' in request body"}), 400

    user_prompt = data['prompt']
    # Get models from request body, default if not provided
    analyst_model_id = data.get("analyst_model_id", "llama3-70b-8192")
    coder_model_id = data.get("coder_model_id", "llama3-70b-8192")

    if analyst_model_id not in AVAILABLE_MODELS:
        return jsonify({"error": f"Invalid analyst model ID: {analyst_model_id}. Available models: {list(AVAILABLE_MODELS.keys())}"}), 400
    if coder_model_id not in AVAILABLE_MODELS:
         return jsonify({"error": f"Invalid coder model ID: {coder_model_id}. Available models: {list(AVAILABLE_MODELS.keys())}"}), 400

    print(f"Requesting visualization for prompt: '{user_prompt}' using Analyst: {analyst_model_id}, Coder: {coder_model_id}")



    # Log agent activity
    log_agent_activity(
        timestamp=datetime.now().isoformat(),
        activity_type="action",
        content=f"Requesting visualization for prompt: {user_prompt}",
        step=len(agent_logs) + 1
    )

    # Pass the selected model_ids to the agent service
    results = get_visualization_suggestions(
        last_uploaded_file_path,
        user_prompt=user_prompt,
        analyst_model_id=analyst_model_id,
        coder_model_id=coder_model_id
    )
    if "error" in results:
        return jsonify(results), 500 # Propagate agent errors
    else:
        return jsonify(results), 200

if __name__ == '__main__':
    # Run on 0.0.0.0 to be accessible externally if needed (e.g., via deploy_expose_port)
    # Use a port like 5001 to avoid conflicts
    print("Starting Flask server...")
    # Remind user about GROQ_API_KEY
    if not os.environ.get("GROQ_API_KEY"):
        print("\n*** WARNING: GROQ_API_KEY environment variable is not set. Visualization generation will fail. ***")
        print("Please set it using: export GROQ_API_KEY='your_groq_api_key'\n")
    app.run(host='0.0.0.0', port=5001, debug=True) # Use debug=False in production
