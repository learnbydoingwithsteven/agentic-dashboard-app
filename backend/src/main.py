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
from src.agent_service import get_visualization_suggestions, AVAILABLE_MODELS, get_api_key, fetch_available_models, agent_logs, cancel_current_job, current_job_id
# Import API key middleware
from src.api_key_middleware import validate_api_key
# Import code execution service
from src.code_execution_service import execute_plotly_code

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
            "check_api_key": "/api/check_api_key",
            "cancel_job": "/api/cancel",
            "reset": "/api/reset",
            "execute_code": "/api/execute_code"
        }
    })

@app.route("/api/cancel", methods=["POST"])
@validate_api_key
def cancel_job():
    """Cancel the currently running agent job."""
    try:
        # Get the job ID from the request (optional)
        data = request.get_json() or {}
        job_id = data.get("job_id")

        # If a job ID is provided, check if it matches the current job
        if job_id and current_job_id and job_id != current_job_id:
            return jsonify({
                "status": "error",
                "message": f"Job ID mismatch. Requested to cancel {job_id} but current job is {current_job_id}"
            }), 400

        # Log the cancellation request
        log_agent_activity(
            timestamp=datetime.now().isoformat(),
            activity_type="cancel_request",
            content=f"User requested cancellation of job {current_job_id or 'unknown'}",
            step=0
        )

        # Cancel the current job
        result = cancel_current_job()
        return jsonify(result), 200

    except Exception as e:
        print(f"Error cancelling job: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to cancel job: {str(e)}"
        }), 500

@app.route("/api/reset", methods=["POST"])
@validate_api_key
def reset_backend():
    """Reset the backend state, clearing all logs and current job."""
    try:
        # Import the global variables
        from src.agent_service import agent_logs, current_job_id, cancel_requested, AVAILABLE_MODELS

        # Log the reset request
        log_agent_activity(
            timestamp=datetime.now().isoformat(),
            activity_type="reset_request",
            content="User requested backend reset",
            step=0
        )

        # Reset agent logs and state
        global agent_logs
        agent_logs = []

        # Reset agent service state
        from src.agent_service import reset_agent_state
        reset_agent_state()

        # Refresh available models
        fetch_available_models()

        return jsonify({
            "status": "success",
            "message": "Backend state reset successfully",
            "available_models": list(AVAILABLE_MODELS.keys())
        })
    except Exception as e:
        print(f"Error resetting backend: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to reset backend: {str(e)}"
        }), 500

@app.route("/api/check_api_key", methods=["GET"])
@validate_api_key
def check_api_key():
    """Check if the provided API key is valid by attempting to fetch models from Groq."""
    try:
        # Get API key and USE_OLLAMA flag from request headers
        api_key = request.headers.get('X-API-KEY')
        use_ollama = request.headers.get('USE-OLLAMA', '').lower() == 'true'

        print(f"API key validation request received. API Key: {'[SET]' if api_key else '[NOT SET]'}, USE_OLLAMA: {use_ollama}")

        # Force a refresh of available models with the current API key
        # This will use the API key from the request header (set by the middleware)
        global AVAILABLE_MODELS

        # Store the current models to check if fetch was successful
        old_models = AVAILABLE_MODELS.copy() if AVAILABLE_MODELS else {}

        # Fetch new models
        fetch_available_models()

        # Print the models for debugging
        print(f"Models after fetch: {list(AVAILABLE_MODELS.keys())}")

        # Check if we have any models available
        if AVAILABLE_MODELS:
            print(f"API key validation successful. Found {len(AVAILABLE_MODELS)} models.")
            return jsonify({
                "status": "success",
                "message": "API key is valid or Ollama models are available",
                "available_models": AVAILABLE_MODELS
            })
        else:
            # If no models were found but we had models before, use the old models
            # This prevents losing models if there's a temporary fetch issue
            if old_models:
                print(f"No new models found, but using {len(old_models)} previously fetched models.")
                AVAILABLE_MODELS.clear()
                AVAILABLE_MODELS.update(old_models)
                return jsonify({
                    "status": "success",
                    "message": "Using previously fetched models",
                    "available_models": AVAILABLE_MODELS
                })
            else:
                print("API key validation failed. No models found.")
                return jsonify({
                    "status": "error",
                    "message": "No models available. Please check your API key or ensure Ollama is running."
                }), 401
    except Exception as e:
        print(f"API key validation error: {str(e)}")
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

    # Check if we're using Ollama
    use_ollama = os.getenv("USE_OLLAMA") == "true"
    print(f"USE_OLLAMA environment variable is: {use_ollama}")

    # Refresh available models to ensure we have the latest
    try:
        fetch_available_models()
    except Exception as e:
        print(f"Error refreshing models: {e}")

    # Get models from query parameters
    analyst_model_id = request.args.get("analyst_model", "llama3-70b-8192")
    coder_model_id = request.args.get("coder_model", "llama3-70b-8192")
    manager_model_id = request.args.get("manager_model", "llama3-70b-8192")

    print(f"Requested models - Analyst: {analyst_model_id}, Coder: {coder_model_id}, Manager: {manager_model_id}")
    print(f"Available models: {list(AVAILABLE_MODELS.keys())}")

    # If using Ollama, make sure we're using Ollama models
    if use_ollama:
        # Check if the requested models are Ollama models
        if not analyst_model_id.startswith("ollama:"):
            # Find an Ollama model to use instead
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                analyst_model_id = ollama_models[0]
                print(f"Using Ollama model {analyst_model_id} for analyst instead of {request.args.get('analyst_model')}")
            else:
                analyst_model_id = "ollama:llama3"
                print(f"No Ollama models found, using default {analyst_model_id} for analyst")

        if not coder_model_id.startswith("ollama:"):
            # Find an Ollama model to use instead
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                coder_model_id = ollama_models[0]
                print(f"Using Ollama model {coder_model_id} for coder instead of {request.args.get('coder_model')}")
            else:
                coder_model_id = "ollama:llama3"
                print(f"No Ollama models found, using default {coder_model_id} for coder")

        if not manager_model_id.startswith("ollama:"):
            # Find an Ollama model to use instead
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                manager_model_id = ollama_models[0]
                print(f"Using Ollama model {manager_model_id} for manager instead of {request.args.get('manager_model')}")
            else:
                manager_model_id = "ollama:llama3"
                print(f"No Ollama models found, using default {manager_model_id} for manager")

    # Validate models against available models
    # We'll be more lenient here - if the model isn't available, we'll try to use a default
    if analyst_model_id not in AVAILABLE_MODELS:
        print(f"Warning: Analyst model {analyst_model_id} not in available models")
        # Try to find a default model
        if use_ollama:
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                analyst_model_id = ollama_models[0]
                print(f"Using Ollama model {analyst_model_id} for analyst instead")
            else:
                analyst_model_id = "ollama:llama3"
                print(f"Using default Ollama model {analyst_model_id} for analyst")
        else:
            # Use the first available model
            if AVAILABLE_MODELS:
                analyst_model_id = next(iter(AVAILABLE_MODELS.keys()))
                print(f"Using model {analyst_model_id} for analyst instead")
            else:
                return jsonify({"error": "No models available"}), 500

    if coder_model_id not in AVAILABLE_MODELS:
        print(f"Warning: Coder model {coder_model_id} not in available models")
        # Try to find a default model
        if use_ollama:
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                coder_model_id = ollama_models[0]
                print(f"Using Ollama model {coder_model_id} for coder instead")
            else:
                coder_model_id = "ollama:llama3"
                print(f"Using default Ollama model {coder_model_id} for coder")
        else:
            # Use the first available model
            if AVAILABLE_MODELS:
                coder_model_id = next(iter(AVAILABLE_MODELS.keys()))
                print(f"Using model {coder_model_id} for coder instead")
            else:
                return jsonify({"error": "No models available"}), 500

    if manager_model_id not in AVAILABLE_MODELS:
        print(f"Warning: Manager model {manager_model_id} not in available models")
        # Try to find a default model
        if use_ollama:
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                manager_model_id = ollama_models[0]
                print(f"Using Ollama model {manager_model_id} for manager instead")
            else:
                manager_model_id = "ollama:llama3"
                print(f"Using default Ollama model {manager_model_id} for manager")
        else:
            # Use the first available model
            if AVAILABLE_MODELS:
                manager_model_id = next(iter(AVAILABLE_MODELS.keys()))
                print(f"Using model {manager_model_id} for manager instead")
            else:
                return jsonify({"error": "No models available"}), 500

    try:
        print(f"Requesting initial visualizations with Analyst: {analyst_model_id}, Coder: {coder_model_id}, Manager: {manager_model_id}")
        results = get_visualization_suggestions(
            last_uploaded_file_path,
            analyst_model_id=analyst_model_id,
            coder_model_id=coder_model_id,
            manager_model_id=manager_model_id
        )
        return jsonify(results), 200 if "error" not in results else 500
    except Exception as e:
        error_message = str(e)
        print(f"Error generating visualizations: {error_message}")
        return jsonify({"error": f"Failed to get initial visualizations: {error_message}"}), 500

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

    # Check if we're using Ollama
    use_ollama = os.getenv("USE_OLLAMA") == "true"
    print(f"USE_OLLAMA environment variable is: {use_ollama}")

    # Refresh available models to ensure we have the latest
    try:
        fetch_available_models()
    except Exception as e:
        print(f"Error refreshing models: {e}")

    # Get models from request body, default if not provided
    analyst_model_id = data.get("analyst_model_id", "llama3-70b-8192")
    coder_model_id = data.get("coder_model_id", "llama3-70b-8192")
    manager_model_id = data.get("manager_model_id", "llama3-70b-8192")

    print(f"Requested models - Analyst: {analyst_model_id}, Coder: {coder_model_id}, Manager: {manager_model_id}")
    print(f"Available models: {list(AVAILABLE_MODELS.keys())}")

    # If using Ollama, make sure we're using Ollama models
    if use_ollama:
        # Check if the requested models are Ollama models
        if not analyst_model_id.startswith("ollama:"):
            # Find an Ollama model to use instead
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                analyst_model_id = ollama_models[0]
                print(f"Using Ollama model {analyst_model_id} for analyst instead of {data.get('analyst_model_id')}")
            else:
                analyst_model_id = "ollama:llama3"
                print(f"No Ollama models found, using default {analyst_model_id} for analyst")

        if not coder_model_id.startswith("ollama:"):
            # Find an Ollama model to use instead
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                coder_model_id = ollama_models[0]
                print(f"Using Ollama model {coder_model_id} for coder instead of {data.get('coder_model_id')}")
            else:
                coder_model_id = "ollama:llama3"
                print(f"No Ollama models found, using default {coder_model_id} for coder")

        if not manager_model_id.startswith("ollama:"):
            # Find an Ollama model to use instead
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                manager_model_id = ollama_models[0]
                print(f"Using Ollama model {manager_model_id} for manager instead of {data.get('manager_model_id')}")
            else:
                manager_model_id = "ollama:llama3"
                print(f"No Ollama models found, using default {manager_model_id} for manager")

    # Validate models against available models
    # We'll be more lenient here - if the model isn't available, we'll try to use a default
    if analyst_model_id not in AVAILABLE_MODELS:
        print(f"Warning: Analyst model {analyst_model_id} not in available models")
        # Try to find a default model
        if use_ollama:
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                analyst_model_id = ollama_models[0]
                print(f"Using Ollama model {analyst_model_id} for analyst instead")
            else:
                analyst_model_id = "ollama:llama3"
                print(f"Using default Ollama model {analyst_model_id} for analyst")
        else:
            # Use the first available model
            if AVAILABLE_MODELS:
                analyst_model_id = next(iter(AVAILABLE_MODELS.keys()))
                print(f"Using model {analyst_model_id} for analyst instead")
            else:
                return jsonify({"error": "No models available"}), 500

    if coder_model_id not in AVAILABLE_MODELS:
        print(f"Warning: Coder model {coder_model_id} not in available models")
        # Try to find a default model
        if use_ollama:
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                coder_model_id = ollama_models[0]
                print(f"Using Ollama model {coder_model_id} for coder instead")
            else:
                coder_model_id = "ollama:llama3"
                print(f"Using default Ollama model {coder_model_id} for coder")
        else:
            # Use the first available model
            if AVAILABLE_MODELS:
                coder_model_id = next(iter(AVAILABLE_MODELS.keys()))
                print(f"Using model {coder_model_id} for coder instead")
            else:
                return jsonify({"error": "No models available"}), 500

    if manager_model_id not in AVAILABLE_MODELS:
        print(f"Warning: Manager model {manager_model_id} not in available models")
        # Try to find a default model
        if use_ollama:
            ollama_models = [m for m in AVAILABLE_MODELS.keys() if m.startswith("ollama:")]
            if ollama_models:
                manager_model_id = ollama_models[0]
                print(f"Using Ollama model {manager_model_id} for manager instead")
            else:
                manager_model_id = "ollama:llama3"
                print(f"Using default Ollama model {manager_model_id} for manager")
        else:
            # Use the first available model
            if AVAILABLE_MODELS:
                manager_model_id = next(iter(AVAILABLE_MODELS.keys()))
                print(f"Using model {manager_model_id} for manager instead")
            else:
                return jsonify({"error": "No models available"}), 500

    print(f"Requesting visualization for prompt: '{user_prompt}' using Analyst: {analyst_model_id}, Coder: {coder_model_id}, Manager: {manager_model_id}")

    # Log agent activity
    log_agent_activity(
        timestamp=datetime.now().isoformat(),
        activity_type="action",
        content=f"Requesting visualization for prompt: {user_prompt}",
        step=len(agent_logs) + 1
    )

    try:
        # Pass the selected model_ids to the agent service
        results = get_visualization_suggestions(
            last_uploaded_file_path,
            user_prompt=user_prompt,
            analyst_model_id=analyst_model_id,
            coder_model_id=coder_model_id,
            manager_model_id=manager_model_id
        )
        if "error" in results:
            return jsonify(results), 500 # Propagate agent errors
        else:
            return jsonify(results), 200
    except Exception as e:
        error_message = str(e)
        print(f"Error generating visualizations: {error_message}")
        return jsonify({"error": f"Failed to get prompted visualization: {error_message}"}), 500

@app.route("/api/execute_code", methods=["POST"])
@validate_api_key
def execute_code_endpoint():
    """Execute Python code to generate a Plotly visualization."""
    global last_uploaded_file_path

    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({"error": "Missing 'code' in request body"}), 400

        code = data['code']

        # Use the last uploaded file path if available
        data_path = last_uploaded_file_path

        # If no file has been uploaded, check if we should use a default dataset
        if not data_path:
            # Try using the default dataset if no file uploaded yet
            # Construct path relative to the backend directory
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            default_filename = '2015---Friuli-Venezia-Giulia---Gestione-finanziaria-Spese-Enti-Locali.csv'
            default_path = os.path.join(backend_dir, 'uploads', default_filename)
            if os.path.exists(default_path):
                data_path = default_path
                print(f"No file uploaded, using default: {data_path}")
            else:
                print("No dataset available for code execution")

        # Log the code execution request
        log_agent_activity(
            timestamp=datetime.now().isoformat(),
            activity_type="code_execution",
            content=f"User requested code execution with {len(code)} characters of code",
            step=0
        )

        # Execute the code
        result = execute_plotly_code(code, data_path)

        # Log the result
        if result.get('error'):
            log_agent_activity(
                timestamp=datetime.now().isoformat(),
                activity_type="code_execution_error",
                content=f"Code execution failed: {result['error'][:200]}...",
                step=1
            )
        else:
            log_agent_activity(
                timestamp=datetime.now().isoformat(),
                activity_type="code_execution_success",
                content=f"Code execution succeeded, generated Plotly figure",
                step=1
            )

        return jsonify(result), 200 if not result.get('error') else 400

    except Exception as e:
        error_message = str(e)
        print(f"Error executing code: {error_message}")

        # Log the error
        log_agent_activity(
            timestamp=datetime.now().isoformat(),
            activity_type="code_execution_error",
            content=f"Code execution failed with exception: {error_message}",
            step=1
        )

        return jsonify({
            "error": f"Failed to execute code: {error_message}",
            "output": "",
            "figure": {},
            "code": data.get('code', '') if 'data' in locals() else ''
        }), 500

if __name__ == '__main__':
    # Run on 0.0.0.0 to be accessible externally if needed (e.g., via deploy_expose_port)
    # Use a port like 5001 to avoid conflicts
    print("Starting Flask server...")
    # Remind user about GROQ_API_KEY
    if not os.environ.get("GROQ_API_KEY"):
        print("\n*** WARNING: GROQ_API_KEY environment variable is not set. Visualization generation will fail. ***")
        print("Please set it using: export GROQ_API_KEY='your_groq_api_key'\n")
    app.run(host='0.0.0.0', port=5001, debug=True) # Use debug=False in production
