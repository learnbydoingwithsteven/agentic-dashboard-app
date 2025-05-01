# backend/src/main.py

import sys
import os
# Add the project root to the Python path to allow absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
import werkzeug.utils

# Import the agent service function
from src.agent_service import get_visualization_suggestions

app = Flask(__name__)

# Configure CORS to allow requests from the React frontend (adjust origin in production)
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Allow all origins for development

# Configuration
UPLOAD_FOLDER = 
'/home/ubuntu/agentic_viz_app/backend/uploads'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 # 16 MB limit

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store the path of the last uploaded file (simple approach for single user)
# In a real multi-user app, this would need a more robust session/user-based mechanism
last_uploaded_file_path = None

@app.route("/api/upload", methods=["POST"])
def upload_file():
    global last_uploaded_file_path
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == 
'':
        return jsonify({"error": "No selected file"}), 400
    if file:
        # Secure the filename
        filename = werkzeug.utils.secure_filename(file.filename)
        # Ensure it's a CSV
        if not filename.lower().endswith(".csv"):
            return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(filepath)
            last_uploaded_file_path = filepath # Store the path
            return jsonify({"message": "File uploaded successfully", "filename": filename, "filepath": filepath}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to save file: {str(e)}"}), 500
    return jsonify({"error": "File upload failed"}), 500

@app.route("/api/visualizations", methods=["GET"])
def get_initial_visualizations():
    global last_uploaded_file_path
    if not last_uploaded_file_path:
        # Try using the default dataset if no file uploaded yet
        default_path = 
'/home/ubuntu/upload/2015---Friuli-Venezia-Giulia---Gestione-finanziaria-Spese-Enti-Locali.csv'
        if os.path.exists(default_path):
             last_uploaded_file_path = default_path
             print(f"No file uploaded, using default: {default_path}")
        else:
            return jsonify({"error": "No dataset has been uploaded or found."}), 400

    if not os.path.exists(last_uploaded_file_path):
         return jsonify({"error": f"Dataset file not found at {last_uploaded_file_path}"}), 404

    print(f"Requesting initial visualizations for: {last_uploaded_file_path}")
    results = get_visualization_suggestions(last_uploaded_file_path)

    if "error" in results:
        return jsonify(results), 500 # Propagate agent errors
    else:
        return jsonify(results), 200

@app.route("/api/visualizations/prompt", methods=["POST"])
def get_prompted_visualization():
    global last_uploaded_file_path
    if not last_uploaded_file_path:
        # Try using the default dataset if no file uploaded yet
        default_path = 
'/home/ubuntu/upload/2015---Friuli-Venezia-Giulia---Gestione-finanziaria-Spese-Enti-Locali.csv'
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
    print(f"Requesting visualization for prompt: ", user_prompt)
    results = get_visualization_suggestions(last_uploaded_file_path, user_prompt=user_prompt)

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

