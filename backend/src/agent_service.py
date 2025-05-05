# backend/src/agent_service.py

import autogen
import pandas as pd
import os
import json
import subprocess
import uuid
import re
from groq import Groq
from datetime import datetime # Added missing import
import traceback
import requests

# Import Ollama configuration
from src.ollama_config import OLLAMA_MODELS, get_ollama_config, is_ollama_available

# Default available models in case we can't fetch them
AVAILABLE_MODELS = {"llama3-70b-8192": "llama3-70b-8192"}

# Function to get the current API key
def get_api_key():
    api_key = os.getenv("GROQ_API_KEY")
    use_ollama = os.getenv("USE_OLLAMA") == "true"

    # If we're using Ollama, we don't strictly need a valid API key
    if use_ollama:
        if not api_key:
            # Return a dummy key when using Ollama without an API key
            return "dummy_key_for_ollama"
        return api_key

    # For Groq, we need a valid API key
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set. Please set it using: export GROQ_API_KEY='your_groq_api_key'")
    return api_key

# Function to fetch available models
def fetch_available_models():
    global AVAILABLE_MODELS
    # Clear existing models to ensure we get fresh data
    AVAILABLE_MODELS.clear()  # Use clear() instead of reassigning
    models = {}
    use_ollama = os.getenv("USE_OLLAMA") == "true"
    use_ollama_explicit_false = os.getenv("USE_OLLAMA") == "false"
    api_key = os.getenv("GROQ_API_KEY")

    # Only print detailed logs when DEBUG is set
    debug_mode = os.getenv("DEBUG") == "true"

    if debug_mode:
        print(f"Fetching available models. USE_OLLAMA={use_ollama}, USE_OLLAMA_explicit_false={use_ollama_explicit_false}, API_KEY={'[SET]' if api_key else '[NOT SET]'}")

    # Check if we're using Ollama
    if use_ollama:
        if debug_mode:
            print("USE_OLLAMA is set to true, prioritizing Ollama models...")
        if is_ollama_available():
            if debug_mode:
                print("Checking for local Ollama models...")
            from src.ollama_config import get_ollama_models
            ollama_models = get_ollama_models()
            if ollama_models:
                models.update(ollama_models)
                if debug_mode:
                    print(f"Found Ollama models: {list([m for m in models.keys() if m.startswith('ollama:')])}")

                # If we found Ollama models and USE_OLLAMA is true, we can return early
                # This prevents trying to use Groq models when Ollama is selected
                if models:
                    AVAILABLE_MODELS.update(models)
                    if debug_mode:
                        print(f"Using Ollama models: {list(AVAILABLE_MODELS.keys())}")
                    return
            elif debug_mode:
                print("No Ollama models found or Ollama is not running.")

    # If USE_OLLAMA is explicitly set to false, we should only use Groq models
    # This is important for switching from Ollama back to Groq
    if use_ollama_explicit_false:
        if debug_mode:
            print("USE_OLLAMA is explicitly set to false, using only Groq models...")
        try:
            if api_key and api_key != "dummy_key_for_ollama":
                if debug_mode:
                    print(f"Fetching available models from Groq API with API key: {api_key[:5]}...")
                client = Groq(api_key=api_key)
                models_response = client.models.list()

                for model in models_response.data:
                    if "embedding" not in model.id.lower():
                        models[model.id] = f"Groq: {model.id}"

                if debug_mode:
                    print(f"Found Groq models: {list(models.keys())}")

                if models:
                    AVAILABLE_MODELS.update(models)
                    if debug_mode:
                        print(f"Total available models: {len(AVAILABLE_MODELS)}")
                        print(f"Available model keys: {list(AVAILABLE_MODELS.keys())}")
                    return
                elif debug_mode:
                    print("No Groq models found.")
            elif debug_mode:
                print("No valid API key for Groq.")
        except Exception as e:
            print(f"Error fetching models from Groq API: {e}")

    # If we're not using Ollama or no Ollama models were found, try Groq
    if not use_ollama or not models:
        try:
            api_key = get_api_key()
            # Don't print the API key if it's the dummy key
            if debug_mode:
                if api_key == "dummy_key_for_ollama":
                    print("Fetching available models from Groq API with dummy key (Ollama mode)...")
                else:
                    print(f"Fetching available models from Groq API with API key: {api_key[:5]}...")

            # Only try to fetch Groq models if we have a real API key
            if api_key != "dummy_key_for_ollama":
                client = Groq(api_key=api_key)
                models_response = client.models.list()

                # Clear any existing models if we're not in Ollama mode
                # This ensures we get fresh Groq models
                if not use_ollama:
                    models = {}

                for model in models_response.data:
                    if "embedding" not in model.id.lower():
                        models[model.id] = f"Groq: {model.id}"

                if debug_mode:
                    print(f"Found Groq models: {list([m for m in models.keys() if not m.startswith('ollama:')])}")
            elif debug_mode:
                print("Skipping Groq API call with dummy key")
        except Exception as e:
            print(f"Error fetching models from Groq API: {e}")

            # If we're using Ollama but couldn't find any Ollama models, add default Ollama models
            if use_ollama:
                if debug_mode:
                    print("Adding default Ollama models as fallback")
                # Add common Ollama models as defaults
                default_models = [
                    "llama3", "llama3:8b", "llama3:70b",
                    "llama2", "mistral", "gemma:7b", "gemma:2b"
                ]
                for model in default_models:
                    models[f"ollama:{model}"] = f"Ollama: {model}"
                if debug_mode:
                    print(f"Added {len(default_models)} default Ollama models")

    # If we still don't have any models, check for Ollama as a fallback (if not already checked)
    # Skip this if USE_OLLAMA is explicitly set to false
    if not models and not use_ollama and not use_ollama_explicit_false:
        if is_ollama_available():
            if debug_mode:
                print("No Groq models found, checking for Ollama models as fallback...")
            from src.ollama_config import get_ollama_models
            ollama_models = get_ollama_models()
            if ollama_models:
                models.update(ollama_models)
                if debug_mode:
                    print(f"Found Ollama models as fallback: {list(ollama_models.keys())}")

    # Update available models if we found any
    if models:
        # Update the global variable with the new models
        AVAILABLE_MODELS.update(models)  # Use update instead of reassigning
        if debug_mode:
            print(f"Total available models: {len(AVAILABLE_MODELS)}")
            print(f"Available model keys: {list(AVAILABLE_MODELS.keys())}")
    else:
        if debug_mode:
            print("Warning: No models found. Using default models.")
        # Add default Ollama models as a last resort
        # Skip this if USE_OLLAMA is explicitly set to false
        if not use_ollama_explicit_false:
            default_models = [
                "llama3", "llama3:8b", "llama3:70b",
                "llama2", "mistral", "gemma:7b", "gemma:2b"
            ]
            for model in default_models:
                AVAILABLE_MODELS[f"ollama:{model}"] = f"Ollama: {model} (default)"
            if debug_mode:
                print(f"Added {len(default_models)} default Ollama models")
                print(f"Default model keys: {list(AVAILABLE_MODELS.keys())}")
        else:
            # If USE_OLLAMA is explicitly false, add a default Groq model
            AVAILABLE_MODELS["llama-3.1-8b-instant"] = "Groq: llama-3.1-8b-instant (default)"
            if debug_mode:
                print("Added default Groq model as fallback")

# Initialize available models
try:
    fetch_available_models()
except Exception as e:
    print(f"Initial model fetch failed: {e}. Will try again on first request.")


# --- Original Hardcoded List (Commented out) ---
# AVAILABLE_MODELS = {
#     "llama3-70b-8192": "Llama 3 70B",
#     "allam-2-7b": "Allam 2 7B",

# Configuration for LLM
def get_llm_config(model_id):
    use_ollama = os.getenv("USE_OLLAMA") == "true"
    debug_mode = os.getenv("DEBUG") == "true"

    try:
        # Get the current API key
        api_key = get_api_key()
    except ValueError as e:
        print(f"Error getting API key: {e}")
        api_key = None

    use_ollama = os.getenv("USE_OLLAMA") == "true"
    debug_mode = os.getenv("DEBUG") == "true"

    # Prioritize Ollama if USE_OLLAMA is set to "true"
    if use_ollama or model_id.startswith("ollama:"):
        if debug_mode:
            print(f"Using Ollama model: {model_id}")
        return get_ollama_config(model_id)
    else:
        # Use Groq if USE_OLLAMA is not set and we have a valid API key
        if api_key:
            if debug_mode:
                print(f"Using Groq model: {model_id}")
            return [
                {
                    "model": model_id,
                    "api_key": api_key,
                    "base_url": "https://api.groq.com/openai/v1",
                    # Use 'timeout' instead of 'request_timeout' for Groq client
                    "timeout": 60.0
                }
            ]
        else:
            # If no API key is available, try to use Ollama as fallback
            if is_ollama_available():
                # Get available Ollama models
                from src.ollama_config import get_ollama_models
                ollama_models_dict = get_ollama_models()

                if ollama_models_dict:
                    # Use the first available Ollama model
                    ollama_model = next(iter(ollama_models_dict.keys()))
                    if debug_mode:
                        print(f"No valid Groq API key, falling back to Ollama model: {ollama_model}")
                    return get_ollama_config(ollama_model)
                else:
                    # No Ollama models available, try a default one
                    default_ollama_model = "ollama:llama3"
                    if debug_mode:
                        print(f"No Ollama models found. Trying default: {default_ollama_model}")
                    return get_ollama_config(default_ollama_model)
            else:
                # No Ollama available either
                raise ValueError("No valid API key for Groq and Ollama is not available")

# Global variables for agent state management
# These will be imported by main.py
agent_logs = []
current_job_id = None
cancel_requested = False

# Function to log agent activity in real-time
def log_agent_activity(timestamp, activity_type, content, step=0, agent_name=None, input_content=None):
    """Log agent activity for debugging and monitoring purposes."""
    log_message = f"[AGENT-LOG] {timestamp} - {activity_type} - Step {step}"
    if agent_name:
        log_message += f" - {agent_name}"
    log_message += f": {content[:100]}..."
    print(log_message)

    # Include input content in the log if available
    if input_content:
        print(f"[AGENT-INPUT] {timestamp} - {activity_type} - Step {step} - {agent_name}: {input_content[:100]}...")

    # This function could be extended to write to a file, database, or other monitoring system
    # For now, it just prints to the console

def cancel_current_job():
    """Request cancellation of the current agent job."""
    global cancel_requested
    cancel_requested = True
    log_agent_activity(
        timestamp=datetime.now().isoformat(),
        activity_type="cancel",
        content="Job cancellation requested by user",
        agent_name="User",
        step=0
    )
    return {"status": "success", "message": "Cancellation requested"}

def reset_agent_state():
    """Reset all agent state variables."""
    global agent_logs, current_job_id, cancel_requested
    agent_logs = []
    current_job_id = None
    cancel_requested = False
    log_agent_activity(
        timestamp=datetime.now().isoformat(),
        activity_type="reset",
        content="Agent state reset by user",
        agent_name="System",
        step=0
    )
    return {"status": "success", "message": "Agent state reset successfully"}

def get_visualization_suggestions(data_path, user_prompt=None, analyst_model_id="llama3-70b-8192", coder_model_id="llama3-70b-8192", manager_model_id="llama3-70b-8192", job_id=None):
    """Analyzes the dataset and suggests visualizations using Autogen agents with GroupChat."""
    global agent_logs, AVAILABLE_MODELS, current_job_id, cancel_requested # Ensure we modify the global variables

    # Set the current job ID and reset cancellation flag
    current_job_id = job_id or str(uuid.uuid4())
    cancel_requested = False

    # Log job start
    log_agent_activity(
        timestamp=datetime.now().isoformat(),
        activity_type="job_start",
        content=f"Starting job {current_job_id} with prompt: {user_prompt if user_prompt else 'Initial analysis'}",
        agent_name="System",
        step=0
    )

    # Refresh available models with the current API key
    try:
        fetch_available_models()
    except Exception as e:
        print(f"Warning: Failed to refresh models: {e}")

    try:
        # --- LLM Configs for Agents ---
        analyst_llm_config = {
            "config_list": get_llm_config(analyst_model_id),
            "cache_seed": 42
        }
        coder_llm_config = {
            "config_list": get_llm_config(coder_model_id),
            "cache_seed": 43 # Use different seed if desired
        }
        manager_llm_config = {
            "config_list": get_llm_config(manager_model_id),
            "cache_seed": 44 # Use different seed for manager
        }
        # Removed Code_Executor agent since ECharts runs in browser

        # --- Load Dataset with enhanced flexible format detection ---
        try:
            # Try different encodings and delimiters
            df = None
            error_messages = []

            # First try to determine file type from extension
            file_extension = os.path.splitext(data_path)[1].lower()

            # Try Excel formats first if extension suggests it
            if file_extension in ['.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt']:
                try:
                    df = pd.read_excel(data_path)
                    print(f"Successfully loaded Excel file based on extension {file_extension}")
                except Exception as e:
                    error_messages.append(f"Failed to load Excel file: {str(e)}")

            # Try JSON if extension suggests it
            elif file_extension in ['.json']:
                try:
                    df = pd.read_json(data_path)
                    print("Successfully loaded JSON file")
                except Exception as e:
                    error_messages.append(f"Failed to load JSON file: {str(e)}")

            # Try Parquet if extension suggests it
            elif file_extension in ['.parquet']:
                try:
                    df = pd.read_parquet(data_path)
                    print("Successfully loaded Parquet file")
                except Exception as e:
                    error_messages.append(f"Failed to load Parquet file: {str(e)}")

            # Try Feather if extension suggests it
            elif file_extension in ['.feather']:
                try:
                    df = pd.read_feather(data_path)
                    print("Successfully loaded Feather file")
                except Exception as e:
                    error_messages.append(f"Failed to load Feather file: {str(e)}")

            # Try HDF5 if extension suggests it
            elif file_extension in ['.h5', '.hdf5']:
                try:
                    df = pd.read_hdf(data_path)
                    print("Successfully loaded HDF5 file")
                except Exception as e:
                    error_messages.append(f"Failed to load HDF5 file: {str(e)}")

            # Try CSV with different encodings and delimiters if still not loaded or for CSV-like extensions
            if df is None:
                for encoding in ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']:
                    for delimiter in [';', ',', '\t', '|']:
                        try:
                            df = pd.read_csv(data_path, encoding=encoding, delimiter=delimiter)
                            print(f"Successfully loaded CSV with encoding={encoding}, delimiter={delimiter}")
                            break
                        except Exception as e:
                            error_messages.append(f"Failed with encoding={encoding}, delimiter={delimiter}: {str(e)}")
                            continue
                    if df is not None:
                        break

            # If all attempts failed, try one more time with pandas defaults
            if df is None:
                try:
                    df = pd.read_csv(data_path)
                    print("Successfully loaded CSV with pandas defaults")
                except Exception as e:
                    # Try Excel format as a last resort regardless of extension
                    try:
                        df = pd.read_excel(data_path)
                        print("Successfully loaded Excel file as last resort")
                    except Exception as excel_e:
                        # If we still can't load the file, raise an error with all the attempts
                        error_detail = "\n".join(error_messages)
                        raise ValueError(f"Failed to load dataset with all attempted methods:\n{error_detail}\nExcel attempt: {str(excel_e)}")

            # Auto-detect and convert numeric columns
            numeric_columns = []
            for col in df.columns:
                # Skip columns that are already numeric
                if pd.api.types.is_numeric_dtype(df[col]):
                    numeric_columns.append(col)
                    continue

                # Check if column contains mostly numeric values
                try:
                    # Try to convert and count how many values were successfully converted
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    non_na_count = numeric_series.count()
                    original_non_na_count = df[col].count()

                    # If at least 70% of values could be converted to numeric, do the conversion
                    if original_non_na_count > 0 and non_na_count / original_non_na_count >= 0.7:
                        df[col] = numeric_series
                        numeric_columns.append(col)
                        print(f"Converted column '{col}' to numeric type")
                except:
                    # Skip columns that cause errors
                    continue

            # Get some basic info for the agents
            num_rows = len(df)
            columns = df.columns.tolist()

            # Check if we're using Groq to further limit token usage
            use_groq = not (os.getenv("USE_OLLAMA") == "true")
            api_key = os.getenv("GROQ_API_KEY")
            is_groq = use_groq and api_key and api_key != "dummy_key_for_ollama"

            # Limit rows based on model provider
            if is_groq:
                # For Groq, be extremely conservative with tokens
                data_head = df.head(3).to_string(max_rows=3, max_cols=5)  # Limit to 3 rows and 5 columns for Groq
                # Create a minimal summary for Groq
                data_sample_for_prompt = f"""Rows: {num_rows}
Columns: {columns[:10]}... (truncated)
Numeric columns: {numeric_columns[:5]}... (truncated)

Sample (3 rows):
{data_head}
"""
            else:
                # For Ollama, also be more concise
                data_head = df.head(5).to_string(max_rows=5, max_cols=8)  # Limit to 5 rows and 8 columns for Ollama
                # Create a more concise summary for Ollama
                data_sample_for_prompt = f"""Rows: {num_rows}
Columns: {columns[:15]}... (truncated)
Numeric columns: {numeric_columns[:8]}... (truncated)

Sample (5 rows):
{data_head}

Brief summary:
{df.describe().head(3).to_string(max_cols=5)}
"""
        except Exception as e:
            error_message = f"Error loading dataset: {str(e)}"
            print(error_message)
            log_agent_activity(
                timestamp=datetime.now().isoformat(),
                activity_type="data_loading_error",
                content=error_message,
                agent_name="System",
                step=0
            )
            # Instead of using a minimal dataset, return an error response
            return {
                "error": error_message,
                "visualizations": []
            }

        # Check if API key is valid by trying to get it
        try:
            api_key = get_api_key()
        except ValueError:
            print("Warning: GROQ_API_KEY not configured. Using default visualization.")
            # Return a default visualization for testing
            return {
                "visualizations": [
                    {
                        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                        "data": {
                            "url": data_path
                        },
                        "mark": "bar",
                        "encoding": {
                            "x": {
                                "field": "Provincia competente",
                                "type": "nominal",
                                "title": "Province",
                                "sort": {"field": "Impegno totale", "order": "descending"}
                            },
                            "y": {
                                "field": "Impegno totale",
                                "type": "quantitative",
                                "title": "Total Commitment (EUR)",
                                "axis": {"format": ",.0f"}
                            }
                        },
                        "width": 600,
                        "height": 400,
                        "title": "Total Commitments by Province"
                    },
                    {
                        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                        "data": {
                            "url": data_path
                        },
                        "mark": "bar",
                        "encoding": {
                            "x": {
                                "field": "Tipologia di spesa",
                                "type": "nominal",
                                "title": "Expense Type",
                                "sort": {"field": "Impegno totale", "order": "descending"}
                            },
                            "y": {
                                "field": "Impegno totale",
                                "type": "quantitative",
                                "title": "Total Commitment (EUR)",
                                "axis": {"format": ",.0f"}
                            }
                        },
                        "width": 600,
                        "height": 400,
                        "title": "Total Commitments by Expense Type"
                    }
                ]
            }

        # Define Agents
        # Check if we're using Groq to further limit token usage
        use_groq = not (os.getenv("USE_OLLAMA") == "true")
        api_key = os.getenv("GROQ_API_KEY")
        is_groq = use_groq and api_key and api_key != "dummy_key_for_ollama"

        # Create a safe system message without f-strings
        try:
            if is_groq:
                # For Groq, use a more concise system message to save tokens
                analyst_system_message = """You are an expert data analyst specializing in data visualization.
Your task is to analyze the provided dataset and identify an insightful visualization.
"""
                # Add minimal dataset-specific information
                analyst_system_message += f"Dataset path: {data_path}\n"
                analyst_system_message += f"Columns: {columns}\n"
            else:
                # For Ollama, we can use the original system message
                analyst_system_message = """You are an expert data analyst specializing in data visualization and insights.
Your task is to analyze the provided dataset and identify the most insightful visualizations.
Consider the columns provided in the data.
"""
                # Add dataset-specific information safely
                analyst_system_message += f"Dataset path: {data_path}\n"
                analyst_system_message += f"Columns: {columns}\n"
                analyst_system_message += f"Data sample:\n{data_head}\n"
        except Exception as e:
            print(f"Warning: Error formatting analyst system message: {e}")
            # Fallback to a simpler message without potentially problematic formatting
            analyst_system_message = """You are an expert data analyst specializing in data visualization.
Your task is to analyze the provided dataset and identify an insightful visualization.
Consider the columns provided in the data sample."""

        # Check if we're using Groq to further limit token usage
        use_groq = not (os.getenv("USE_OLLAMA") == "true")
        api_key = os.getenv("GROQ_API_KEY")
        is_groq = use_groq and api_key and api_key != "dummy_key_for_ollama"

        # Create appropriate core task message based on model provider
        if is_groq:
            # For Groq, use a more concise core task message to save tokens
            core_task_message = """

CORE TASK: Suggest ONE clear visualization specification for the Visualization_Coder.

INSTRUCTIONS:
1. Use EXACT column names from the 'Columns' section.
2. Focus ONLY on the most important numerical relationships in the data.
3. Skip lengthy analysis and explanations.
4. Include ONLY:
   - Chart Type (bar, line, pie, scatter)
   - Categorical Column (x-axis/slices)
   - Numerical Column (y-axis/values)
   - Simple Data Processing (group by, sum)
   - Brief Title

EXAMPLE:
"Visualization:
- Chart Type: Bar chart
- Categorical Column: 'Region'
- Numerical Column: 'Total Sales'
- Data Processing: Group by 'Region', Sum 'Total Sales'
- Title: 'Total Sales by Region'"

Provide ONLY the specification with NO additional commentary.
"""
        else:
            # For Ollama, use a more concise message as well
            core_task_message = """

CORE TASK: Suggest ONE clear visualization specification for the Visualization_Coder.

INSTRUCTIONS:
1. Use EXACT column names from the 'Columns' section.
2. Focus ONLY on the most important numerical relationships in the data.
3. Skip lengthy analysis and explanations.
4. Include ONLY:
   - Chart Type (bar, line, pie, scatter)
   - Categorical Column (x-axis/slices)
   - Numerical Column (y-axis/values)
   - Simple Data Processing (group by, sum)
   - Brief Title

EXAMPLE:
"Visualization:
- Chart Type: Bar chart
- Categorical Column: 'Region'
- Numerical Column: 'Total Sales'
- Data Processing: Group by 'Region', Sum 'Total Sales'
- Title: 'Total Sales by Region'"

Provide ONLY the specification with NO additional commentary.
"""

        data_analyst = autogen.AssistantAgent(
            name="Data_Analyst",
            system_message=analyst_system_message + core_task_message,
            llm_config=analyst_llm_config, # Use analyst specific config
        )

        # Check if we're using Groq to further limit token usage
        use_groq = not (os.getenv("USE_OLLAMA") == "true")
        api_key = os.getenv("GROQ_API_KEY")
        is_groq = use_groq and api_key and api_key != "dummy_key_for_ollama"

        # Create appropriate system message for visualization coder based on model provider
        if is_groq:
            # For Groq, use a more concise system message to save tokens
            coder_system_message = """You are an expert Python coder specializing in Plotly visualizations.

CORE TASK: Write Python code using Plotly to generate the visualization specified by the Data_Analyst.

INSTRUCTIONS:
1. Follow the analyst's specifications exactly.
2. Use exact column names specified.
3. Assume `df` is already loaded.
4. Use pandas and plotly.express.
5. Check if columns exist before using them.
6. Create clean, minimal code with no comments.
7. Assign final figure to variable named `fig`.

EXAMPLE:
```python
import pandas as pd
import plotly.express as px

cat_col = 'Region'
num_col = 'Sales'

if cat_col not in df.columns or num_col not in df.columns:
    fig = px.bar(title="Error: Columns not found")
else:
    processed_df = df.groupby(cat_col)[num_col].sum().reset_index()
    processed_df = processed_df.sort_values(num_col, ascending=False)
    fig = px.bar(
        processed_df,
        x=cat_col,
        y=num_col,
        title='Sales by Region'
    )
```

Provide only the Python code block with no explanation.
"""
        else:
            # For Ollama, use a more concise system message as well
            coder_system_message = """You are an expert Python coder specializing in Plotly visualizations.

CORE TASK: Write Python code using Plotly to generate the visualization specified by the Data_Analyst.

INSTRUCTIONS:
1. Follow the analyst's specifications exactly.
2. Use exact column names specified.
3. Assume `df` is already loaded.
4. Use pandas and plotly.express.
5. Check if columns exist before using them.
6. Create clean, minimal code with no comments.
7. Assign final figure to variable named `fig`.

EXAMPLE:
```python
import pandas as pd
import plotly.express as px

cat_col = 'Region'
num_col = 'Sales'

if cat_col not in df.columns or num_col not in df.columns:
    fig = px.bar(title="Error: Columns not found")
else:
    processed_df = df.groupby(cat_col)[num_col].sum().reset_index()
    processed_df = processed_df.sort_values(num_col, ascending=False)
    fig = px.bar(
        processed_df,
        x=cat_col,
        y=num_col,
        title='Sales by Region'
    )
```

Provide only the Python code block with no explanation.
"""

        visualization_coder = autogen.AssistantAgent(
            name="Visualization_Coder",
            system_message=coder_system_message,
            llm_config=coder_llm_config, # Use coder specific config
        )

        user_proxy = autogen.UserProxyAgent(
            name="User_Proxy",
            human_input_mode="NEVER",
            # Terminate immediately when coder provides any Python code
            is_termination_msg=lambda x: "```python" in x.get("content", ""),
            code_execution_config=False,
            system_message="You are a proxy for the human user. Your role is to request visualizations. When the Visualization_Coder provides Python code, end the conversation immediately.",
        )

        # --- Group Chat Setup ---
        groupchat = autogen.GroupChat(
            agents=[user_proxy, data_analyst, visualization_coder],
            messages=[],
            max_round=3, # Limit rounds to keep conversation short and focused
            speaker_selection_method="round_robin" # Ensure predictable turn-taking
        )
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config=manager_llm_config # Use dedicated manager model
        )

        # --- Real-time Logging Setup ---
        # Create a custom message callback to log messages in real-time
        def on_new_message(message):
            """Callback function to log messages in real-time as they are generated."""
            # Get the current conversation or create a new one if it doesn't exist
            global agent_logs, cancel_requested

            # Check if cancellation was requested
            if cancel_requested:
                # Add a cancellation message to the log
                if agent_logs and len(agent_logs) > 0:
                    current_log = agent_logs[-1]
                    # Check if "messages" key exists in the log entry
                    if "messages" in current_log:
                        current_log["messages"].append({
                            "name": "System",
                            "content": "⚠️ Job cancelled by user. Stopping agent conversation.",
                            "role": "System"
                        })
                    else:
                        # Initialize the messages list if it doesn't exist
                        current_log["messages"] = [{
                            "name": "System",
                            "content": "⚠️ Job cancelled by user. Stopping agent conversation.",
                            "role": "System"
                        }]

                # Raise an exception to stop the agent conversation
                raise Exception("Job cancelled by user")

            # Check if we have an ongoing conversation
            if not agent_logs or len(agent_logs) == 0:
                # Create a new conversation log
                new_log = {
                    "timestamp": datetime.now().isoformat(),
                    "analyst_model": analyst_model_id,
                    "coder_model": coder_model_id,
                    "manager_model": manager_model_id,
                    "messages": [],
                    "job_id": current_job_id,
                    "status": "running"
                }
                agent_logs.append(new_log)

            # Add the new message to the most recent conversation
            current_log = agent_logs[-1]
            current_log["messages"].append({
                "name": message.get('name'),
                "content": message.get('content'),
                "role": message.get('role')
            })

            # Print the message for debugging
            print(f"\n[REAL-TIME] New message from {message.get('name')}: {message.get('content')[:100]}...")

        # Register the callback with the groupchat
        groupchat.on_new_message = on_new_message

        # --- Chat Initiation ---
        # Check if we're using Groq to further limit token usage
        use_groq = not (os.getenv("USE_OLLAMA") == "true")
        api_key = os.getenv("GROQ_API_KEY")
        is_groq = use_groq and api_key and api_key != "dummy_key_for_ollama"

        # Create initial request message safely without complex f-strings
        try:
            if is_groq:
                # For Groq, use a more concise prompt to save tokens
                initial_request = "Create 1 visualization for this dataset using Plotly.\n"
                initial_request += f"Dataset path: {data_path}\n"
                initial_request += "Data sample:\n"
                initial_request += data_sample_for_prompt + "\n\n"
                initial_request += """Data Analyst: Suggest 1 clear visualization.
Visualization Coder: Create Python code with Plotly based on the specification."""
            else:
                # For Ollama, use a more concise prompt as well
                initial_request = "Create 1 visualization for this dataset using Plotly.\n"
                initial_request += f"Dataset path: {data_path}\n"
                initial_request += "Data sample:\n"
                initial_request += data_sample_for_prompt + "\n\n"
                initial_request += """Data Analyst: Suggest 1 clear visualization.
Visualization Coder: Create Python code with Plotly based on the specification."""
        except Exception as e:
            print(f"Warning: Error formatting initial request: {e}")
            # Fallback to a simpler message
            initial_request = """Create a visualization for this dataset using Plotly.
Data Analyst: Suggest a visualization.
Visualization Coder: Create Python code with Plotly."""

        # Create follow-up request message safely without complex f-strings
        try:
            if is_groq:
                # For Groq, use a more concise prompt to save tokens
                follow_up_request = f"Create visualization: \"{user_prompt}\"\n"
                follow_up_request += f"Dataset: {data_path}\n"
                follow_up_request += "Data sample:\n"
                follow_up_request += data_sample_for_prompt + "\n\n"
                follow_up_request += """Data Analyst: Suggest visualization for this request.
Visualization Coder: Create Python code with Plotly."""
            else:
                # For Ollama, use a more concise prompt as well
                follow_up_request = f"Create visualization: \"{user_prompt}\"\n"
                follow_up_request += f"Dataset: {data_path}\n"
                follow_up_request += "Data sample:\n"
                follow_up_request += data_sample_for_prompt + "\n\n"
                follow_up_request += """Data Analyst: Suggest visualization for this request.
Visualization Coder: Create Python code with Plotly."""
        except Exception as e:
            print(f"Warning: Error formatting follow-up request: {e}")
            # Fallback to a simpler message
            follow_up_request = f"Create visualization: \"{user_prompt}\"\n"
            follow_up_request += """Data Analyst: Suggest a visualization.
Visualization Coder: Create Python code with Plotly."""

        # Determine the message to initiate the chat
        chat_init_message = follow_up_request if user_prompt else initial_request

        # Log the start of a new conversation
        log_agent_activity(
            timestamp=datetime.now().isoformat(),
            activity_type="start",
            content=f"Starting new conversation with prompt: {user_prompt if user_prompt else 'Initial analysis'}",
            agent_name="User_Proxy",
            input_content=chat_init_message,
            step=1
        )

        # Initiate chat using the GroupChatManager
        # The user_proxy starts the conversation by sending the initial message to the manager
        user_proxy.initiate_chat(
            manager,
            message=chat_init_message,
        )

        # --- Log Conversation ---
        # Messages are stored in the groupchat object
        all_messages = groupchat.messages
        print("\n=== Agent Conversation ===")
        for msg in all_messages:
            print(f"\n[{msg.get('name')}] {msg.get('content', '')}")

        # Since we're already logging messages in real-time, we don't need to create a new log entry
        # Just make sure the last log entry is complete and up-to-date
        if agent_logs and len(agent_logs) > 0:
            # Update the timestamp to the current time
            agent_logs[-1]["timestamp"] = datetime.now().isoformat()

            # Ensure all messages are included (in case some were missed by the callback)
            # Check if "messages" key exists in the log entry
            if "messages" in agent_logs[-1]:
                current_messages = [m.get('content') for m in agent_logs[-1]["messages"]]
                for msg in all_messages:
                    # Check if this message is already in the log
                    if msg.get('content') not in current_messages:
                        agent_logs[-1]["messages"].append({
                            "name": msg.get('role'),
                            "content": msg.get('content'),
                            "role": msg.get('role')
                        })
            else:
                # Initialize the messages list if it doesn't exist
                agent_logs[-1]["messages"] = [
                    {
                        "name": m.get('role'),
                        "content": m.get('content'),
                        "role": m.get('role')
                    }
                    for m in all_messages
                ]
        else:
            # If for some reason we don't have a log entry yet, create one
            conversation_log = {
                "timestamp": datetime.now().isoformat(),
                # Log all models used
                "analyst_model": analyst_model_id,
                "coder_model": coder_model_id,
                "manager_model": manager_model_id,
                "messages": [
                    {
                        # GroupChat messages have 'role' which corresponds to the agent name
                        "name": m.get('role'),
                        "content": m.get('content'),
                        "role": m.get('role')
                    }
                    for m in all_messages
                ]
            }
            agent_logs.append(conversation_log)

        # Update job status and log completion
        if agent_logs and len(agent_logs) > 0:
            agent_logs[-1]["status"] = "completed"

        log_agent_activity(
            timestamp=datetime.now().isoformat(),
            activity_type="complete",
            content=f"Conversation completed with {len(all_messages)} messages",
            agent_name="System",
            step=len(all_messages) + 1
        )

        # Keep only the last 100 conversations
        if len(agent_logs) > 100:
            agent_logs = agent_logs[-100:]

        # Check if cancellation was requested before processing results
        if cancel_requested:
            # Update job status
            if agent_logs and len(agent_logs) > 0:
                agent_logs[-1]["status"] = "cancelled"

            log_agent_activity(
                timestamp=datetime.now().isoformat(),
                activity_type="cancel_complete",
                content="Job cancellation completed",
                agent_name="System",
                step=len(all_messages) + 2
            )

            # Return a cancellation message
            return {
                "error": "Job cancelled by user",
                "visualizations": []
            }

        # Extract Python code for Plotly visualizations from the chat history
        plotly_code_blocks = []
        # Look in messages from the Visualization_Coder
        coder_messages = [m for m in all_messages if m.get("name") == "Visualization_Coder"]

        # Process each message from the Visualization_Coder
        for i, message in enumerate(coder_messages):
            content = message.get("content", "")
            print(f"\n--- Processing Visualization Code {i+1} ---")

            # Extract code between ```python and ``` markers
            import re
            python_code_blocks = re.findall(r'```python\s*([\s\S]*?)\s*```', content)

            if python_code_blocks:
                for j, python_code in enumerate(python_code_blocks):
                    print(f"Found Python code block {j+1} in message {i+1}")

                    # Store the Python code for execution
                    plotly_code_blocks.append({
                        "code": python_code,
                        "message_index": i,
                        "block_index": j
                    })
                    print(f"Added Python code block {j+1} from message {i+1} for execution")
            else:
                print(f"No Python code blocks found in message {i+1}")
                # Try to find Python code in plain text
                try:
                    # Look for patterns that might indicate Python code with Plotly
                    if "import plotly" in content or "fig = px." in content or "fig = go." in content:
                        print(f"Found potential Python code without code blocks in message {i+1}")

                        # Try to extract the code
                        potential_code = ""
                        lines = content.split('\n')
                        in_code_section = False

                        for line in lines:
                            if "import plotly" in line or "import pandas" in line:
                                in_code_section = True
                                potential_code += line + "\n"
                            elif in_code_section:
                                potential_code += line + "\n"
                                if "fig.show()" in line or "fig" in line and len(line.strip()) < 10:
                                    # Likely the end of the code section
                                    break

                        if potential_code and ("fig = " in potential_code or "fig=" in potential_code):
                            plotly_code_blocks.append({
                                "code": potential_code,
                                "message_index": i,
                                "block_index": 0,
                                "extracted": True
                            })
                            print(f"Extracted potential Python code from message {i+1}")

                except Exception as e:
                    print(f"Error searching for Python code: {str(e)}")

        # Execute the Python code blocks to generate Plotly visualizations
        from src.code_execution_service import execute_plotly_code

        # List to store the executed visualization results
        visualization_results = []

        # If we have Python code blocks, execute them
        if plotly_code_blocks:
            print(f"\n=== Executing {len(plotly_code_blocks)} Python code blocks ===")

            for i, code_block in enumerate(plotly_code_blocks):
                print(f"\n--- Executing Python code block {i+1} ---")

                # Execute the code
                result = execute_plotly_code(code_block["code"], data_path)

                # Add metadata about the code block
                result["block_index"] = code_block.get("block_index", 0)
                result["message_index"] = code_block.get("message_index", 0)

                # Add the result to the list
                visualization_results.append(result)

                # Log the execution
                log_agent_activity(
                    timestamp=datetime.now().isoformat(),
                    activity_type="code_execution",
                    content=f"Executed Python code block {i+1} with result: {'success' if result.get('figure') else 'error'}",
                    agent_name="Code_Executor",
                    input_content=code_block["code"],
                    step=len(agent_logs) + i + 1
                )

        # If no code blocks were found or execution failed, create default visualizations
        if not plotly_code_blocks or not any(r.get('figure') for r in visualization_results):
            print("\n=== No valid Python code blocks were found or execution failed. ===")
            print("Creating default visualizations...")

            # Initialize echarts_configs list
            echarts_configs = []

            # Create enhanced default visualizations based on the dataset with real data
            try:
                # Try to load the dataset with enhanced flexible format detection
                df = None
                error_messages = []

                # First try to determine file type from extension
                file_extension = os.path.splitext(data_path)[1].lower()

                # Try Excel formats first if extension suggests it
                if file_extension in ['.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt']:
                    try:
                        df = pd.read_excel(data_path)
                        print(f"Default viz: Successfully loaded Excel file based on extension {file_extension}")
                    except Exception as e:
                        error_messages.append(f"Failed to load Excel file: {str(e)}")

                # Try JSON if extension suggests it
                elif file_extension in ['.json']:
                    try:
                        df = pd.read_json(data_path)
                        print("Default viz: Successfully loaded JSON file")
                    except Exception as e:
                        error_messages.append(f"Failed to load JSON file: {str(e)}")

                # Try Parquet if extension suggests it
                elif file_extension in ['.parquet']:
                    try:
                        df = pd.read_parquet(data_path)
                        print("Default viz: Successfully loaded Parquet file")
                    except Exception as e:
                        error_messages.append(f"Failed to load Parquet file: {str(e)}")

                # Try CSV with different encodings and delimiters if still not loaded or for CSV-like extensions
                if df is None:
                    for encoding in ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']:
                        for delimiter in [';', ',', '\t', '|']:
                            try:
                                df = pd.read_csv(data_path, encoding=encoding, delimiter=delimiter)
                                print(f"Default viz: Successfully loaded CSV with encoding={encoding}, delimiter={delimiter}")
                                break
                            except Exception as e:
                                error_messages.append(f"Failed with encoding={encoding}, delimiter={delimiter}: {str(e)}")
                                continue
                        if df is not None:
                            break

                # If all attempts failed, try with pandas defaults
                if df is None:
                    try:
                        df = pd.read_csv(data_path)
                        print("Default viz: Successfully loaded CSV with pandas defaults")
                    except Exception:
                        try:
                            df = pd.read_excel(data_path)
                            print("Default viz: Successfully loaded Excel file as last resort")
                        except Exception as e:
                            print(f"Default viz: Failed to load dataset: {str(e)}")
                            # Create a minimal dataset for testing
                            df = pd.DataFrame({
                                'Column1': [1, 2, 3, 4, 5],
                                'Column2': ['A', 'B', 'C', 'D', 'E']
                            })

                # Auto-detect numeric columns
                numeric_columns = []
                for col in df.columns:
                    # Skip columns that are already numeric
                    if pd.api.types.is_numeric_dtype(df[col]):
                        numeric_columns.append(col)
                        continue

                    # Check if column contains mostly numeric values
                    try:
                        # Try to convert and count how many values were successfully converted
                        numeric_series = pd.to_numeric(df[col], errors='coerce')
                        non_na_count = numeric_series.count()
                        original_non_na_count = df[col].count()

                        # If at least 70% of values could be converted to numeric, do the conversion
                        if original_non_na_count > 0 and non_na_count / original_non_na_count >= 0.7:
                            df[col] = numeric_series
                            numeric_columns.append(col)
                            print(f"Default viz: Converted column '{col}' to numeric type")
                    except:
                        # Skip columns that cause errors
                        continue

                # Default visualization 1: Enhanced bar chart of total commitments by province
                if 'Provincia competente' in df.columns and 'Impegno totale' in df.columns:
                    province_totals = df.groupby('Provincia competente')['Impegno totale'].sum().reset_index()
                    province_totals = province_totals.sort_values('Impegno totale', ascending=False)

                    # Format numbers for display
                    formatted_values = [f"{x:,.2f}" for x in province_totals['Impegno totale'].tolist()]

                    echarts_configs.append({
                        "title": {
                            "text": "Impegno Totale per Provincia",
                            "left": "center",
                            "textStyle": {
                                "fontSize": 16,
                                "fontWeight": "bold"
                            }
                        },
                        "tooltip": {
                            "trigger": "axis",
                            "formatter": "{b}: {c} EUR"
                        },
                        "grid": {
                            "left": "5%",
                            "right": "5%",
                            "bottom": "15%",
                            "containLabel": True
                        },
                        "xAxis": {
                            "type": "category",
                            "data": province_totals['Provincia competente'].tolist(),
                            "axisLabel": {
                                "rotate": 45,
                                "fontSize": 10,
                                "interval": 0
                            }
                        },
                        "yAxis": {
                            "type": "value",
                            "name": "Impegno Totale (EUR)",
                            "axisLabel": {
                                "formatter": "{value:,.0f}"
                            }
                        },
                        "series": [{
                            "name": "Impegno Totale",
                            "type": "bar",
                            "data": province_totals['Impegno totale'].tolist(),
                            "itemStyle": {
                                "color": "#5470c6"
                            },
                            "label": {
                                "show": True,
                                "position": "top",
                                "formatter": "{c:,.0f}",
                                "fontSize": 10
                            },
                            "emphasis": {
                                "itemStyle": {
                                    "color": "#3a56b4"
                                }
                            }
                        }]
                    })

                # Default visualization 2: Enhanced pie chart of expense types
                if 'Tipologia di spesa' in df.columns and 'Impegno totale' in df.columns:
                    expense_totals = df.groupby('Tipologia di spesa')['Impegno totale'].sum().reset_index()
                    expense_totals = expense_totals.sort_values('Impegno totale', ascending=False)

                    # Limit to top 8 categories for better visualization
                    if len(expense_totals) > 8:
                        other_total = expense_totals.iloc[8:]['Impegno totale'].sum()
                        top_expenses = expense_totals.iloc[:8].copy()
                        top_expenses.loc[len(top_expenses)] = {'Tipologia di spesa': 'Altre tipologie', 'Impegno totale': other_total}
                        expense_totals = top_expenses

                    echarts_configs.append({
                        "title": {
                            "text": "Distribuzione per Tipologia di Spesa",
                            "left": "center",
                            "textStyle": {
                                "fontSize": 16,
                                "fontWeight": "bold"
                            }
                        },
                        "tooltip": {
                            "trigger": "item",
                            "formatter": "{b}: {c:,.2f} EUR ({d}%)"
                        },
                        "legend": {
                            "type": "scroll",
                            "orient": "horizontal",
                            "bottom": "bottom",
                            "textStyle": {
                                "fontSize": 10
                            }
                        },
                        "series": [{
                            "name": "Tipologia di Spesa",
                            "type": "pie",
                            "radius": ["30%", "70%"],
                            "center": ["50%", "50%"],
                            "avoidLabelOverlap": True,
                            "itemStyle": {
                                "borderRadius": 10,
                                "borderColor": "#fff",
                                "borderWidth": 2
                            },
                            "label": {
                                "show": True,
                                "formatter": "{b}: {d}%",
                                "fontSize": 10
                            },
                            "emphasis": {
                                "label": {
                                    "show": True,
                                    "fontSize": 12,
                                    "fontWeight": "bold"
                                }
                            },
                            "labelLine": {
                                "show": True
                            },
                            "data": [
                                {"value": float(row['Impegno totale']), "name": row['Tipologia di spesa']}
                                for _, row in expense_totals.iterrows()
                            ]
                        }]
                    })

                # Default visualization 3: Stacked bar chart comparing committed vs paid amounts by province
                if all(col in df.columns for col in ['Provincia competente', 'Impegno totale', 'Pagato totale']):
                    # Group by province and calculate totals
                    compare_df = df.groupby('Provincia competente').agg({
                        'Impegno totale': 'sum',
                        'Pagato totale': 'sum'
                    }).reset_index()

                    # Sort by total commitment
                    compare_df = compare_df.sort_values('Impegno totale', ascending=False)

                    # Calculate payment ratio
                    compare_df['Ratio'] = compare_df['Pagato totale'] / compare_df['Impegno totale'] * 100

                    # Limit to top 10 provinces for better visualization
                    if len(compare_df) > 10:
                        compare_df = compare_df.iloc[:10]

                    echarts_configs.append({
                        "title": {
                            "text": "Confronto tra Impegno e Pagato per Provincia",
                            "left": "center",
                            "textStyle": {
                                "fontSize": 16,
                                "fontWeight": "bold"
                            }
                        },
                        "tooltip": {
                            "trigger": "axis",
                            "axisPointer": {
                                "type": "shadow"
                            },
                            "formatter": "{b}<br/>{a0}: {c0:,.0f} EUR<br/>{a1}: {c1:,.0f} EUR"
                        },
                        "legend": {
                            "data": ["Impegno totale", "Pagato totale"],
                            "bottom": "bottom"
                        },
                        "grid": {
                            "left": "5%",
                            "right": "5%",
                            "bottom": "15%",
                            "top": "10%",
                            "containLabel": True
                        },
                        "xAxis": {
                            "type": "category",
                            "data": compare_df['Provincia competente'].tolist(),
                            "axisLabel": {
                                "rotate": 45,
                                "fontSize": 10,
                                "interval": 0
                            }
                        },
                        "yAxis": {
                            "type": "value",
                            "name": "EUR",
                            "axisLabel": {
                                "formatter": "{value:,.0f}"
                            }
                        },
                        "series": [
                            {
                                "name": "Impegno totale",
                                "type": "bar",
                                "stack": "total",
                                "emphasis": {
                                    "focus": "series"
                                },
                                "data": compare_df['Impegno totale'].tolist(),
                                "itemStyle": {
                                    "color": "#5470c6"
                                }
                            },
                            {
                                "name": "Pagato totale",
                                "type": "bar",
                                "stack": "total",
                                "emphasis": {
                                    "focus": "series"
                                },
                                "data": compare_df['Pagato totale'].tolist(),
                                "itemStyle": {
                                    "color": "#91cc75"
                                }
                            }
                        ]
                    })
            except Exception as e:
                print(f"Error creating default visualizations: {str(e)}")
                # Provide very basic fallback visualizations
                echarts_configs = [
                    {
                        "title": {"text": "Default Visualization (Error occurred)"},
                        "tooltip": {},
                        "xAxis": {"type": "category", "data": ["Please check logs"]},
                        "yAxis": {"type": "value"},
                        "series": [{"data": [0], "type": "bar"}]
                    }
                ]

            # Ensure all configs have required properties for ECharts BEFORE creating the response
            for i, config in enumerate(echarts_configs):
                # Make sure each config has at least these basic properties
                if not config.get('title'):
                    config['title'] = {"text": f"Visualization {i+1}"}

                if not config.get('tooltip'):
                    config['tooltip'] = {}

                if not config.get('xAxis'):
                    config['xAxis'] = {"type": "category", "data": []}

                if not config.get('yAxis'):
                    config['yAxis'] = {"type": "value"}

                if not config.get('series') or not isinstance(config.get('series'), list) or len(config.get('series')) == 0:
                    config['series'] = [{"type": "bar", "data": []}]

                # Ensure each series has a type and data
                for series in config.get('series', []):
                    if not series.get('type'):
                        series['type'] = 'bar'
                    if not series.get('data') or not isinstance(series.get('data'), list):
                        series['data'] = []

            # Create the response using the validated ECharts configs
            response = {
                "visualizations": echarts_configs,
                "code_blocks": [],
                "outputs": [],
                "errors": []
            }
        else:
            # This else block corresponds to the 'if plotly_code_blocks:' condition (Line 995)
            # If Plotly code was executed successfully, prepare the response using Plotly figures
            response = {
                "visualizations": [r.get('figure', {}) for r in visualization_results if r.get('figure')],
            "code_blocks": [r.get('code', '') for r in visualization_results],
            "outputs": [r.get('output', '') for r in visualization_results],
            "errors": [r.get('error', '') for r in visualization_results]
        }

        print(f"Returning {len(response['visualizations'])} visualizations")
        return response

    except Exception as e:
        print(f"Error in get_visualization_suggestions: {str(e)}")
        # Log the full traceback for better debugging
        traceback.print_exc()

        # Update job status on error
        if agent_logs and len(agent_logs) > 0:
            if "cancelled" in str(e).lower():
                agent_logs[-1]["status"] = "cancelled"
            else:
                agent_logs[-1]["status"] = "error"

            # Add error message to the log
            # Check if "messages" key exists in the log entry
            if "messages" in agent_logs[-1]:
                agent_logs[-1]["messages"].append({
                    "name": "System",
                    "content": f"⚠️ Error: {str(e)}",
                    "role": "System"
                })
            else:
                # Initialize the messages list if it doesn't exist
                agent_logs[-1]["messages"] = [{
                    "name": "System",
                    "content": f"⚠️ Error: {str(e)}",
                    "role": "System"
                }]

        log_agent_activity(
            timestamp=datetime.now().isoformat(),
            activity_type="error",
            content=f"Job failed with error: {str(e)}",
            agent_name="System",
            step=0
        )

        return {
            "error": f"Failed to generate visualizations: {str(e)}",
            "visualizations": []
        }


# Example usage (for testing) - Keep original relative path logic
if __name__ == "__main__":
    # Make sure the GROQ_API_KEY is set in your environment
    # export GROQ_API_KEY='your_key_here'
    if not groq_api_key:
        print("Please set the GROQ_API_KEY environment variable to test.")
    else:
        # Use a relative path for the test dataset (assuming it's in backend/uploads)
        backend_dir = os.path.dirname(__file__) # src directory
        test_data_filename = '2015---Friuli-Venezia-Giulia---Gestione-finanziaria-Spese-Enti-Locali.csv'
        # Corrected path construction relative to backend/src
        test_data_path = os.path.join(os.path.dirname(backend_dir), 'uploads', test_data_filename)
        if not os.path.exists(test_data_path):
            print(f"Test data file not found at expected location: {test_data_path}")
            # Try path relative to backend/ directory itself (if uploads is inside src)
            test_data_path_alt = os.path.join(backend_dir, 'uploads', test_data_filename)
            if os.path.exists(test_data_path_alt):
                test_data_path = test_data_path_alt
                print(f"Found test data at alternative path: {test_data_path_alt}")
            else:
                 print(f"Also not found at: {test_data_path_alt}")
                 test_data_path = None # Indicate file not found

        if test_data_path:
            print(f"\n--- Requesting initial visualizations for {test_data_path} ---")
            # Test with default models
            results = get_visualization_suggestions(test_data_path)
            print(json.dumps(results, indent=2))

            print("\n--- Requesting specific visualization (default models) --- ")
            prompt = "Show the total Impegno totale per Provincia competente, ordered by amount."
            results_specific = get_visualization_suggestions(test_data_path, user_prompt=prompt)
            print(json.dumps(results_specific, indent=2))

            print("\n--- Requesting specific visualization (different models) --- ")
            # Example: Use a different model for the coder if available and valid
            available_coder_model = "mistral-saba-24b" # Example, adjust if needed
            if available_coder_model in AVAILABLE_MODELS:
                 results_specific_models = get_visualization_suggestions(
                     test_data_path,
                     user_prompt=prompt,
                     analyst_model_id="llama3-70b-8192", # Keep analyst default
                     coder_model_id=available_coder_model
                 )
                 print(json.dumps(results_specific_models, indent=2))
            else:
                 print(f"Skipping multi-model test, coder model '{available_coder_model}' not in AVAILABLE_MODELS")
        else:
            print("Skipping tests as test data file could not be located.")