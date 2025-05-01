# backend/src/agent_service.py

import autogen
import pandas as pd
import os
import json
import subprocess
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
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set. Please set it using: export GROQ_API_KEY='your_groq_api_key'")
    return api_key

# Function to fetch available models
def fetch_available_models():
    global AVAILABLE_MODELS
    models = {}

    # Try to fetch Groq models
    try:
        api_key = get_api_key()
        print(f"Fetching available models from Groq API with API key: {api_key[:5]}...")
        client = Groq(api_key=api_key)
        models_response = client.models.list()

        for model in models_response.data:
            if "embedding" not in model.id.lower():
                models[model.id] = f"Groq: {model.id}"

        print(f"Found Groq models: {list([m for m in models.keys() if not m.startswith('ollama:')])}")
    except Exception as e:
        print(f"Error fetching models from Groq API: {e}. Using default.")

    # Check for Ollama models
    if is_ollama_available():
        print("Checking for local Ollama models...")
        from src.ollama_config import get_ollama_models
        ollama_models = get_ollama_models()
        if ollama_models:
            models.update(ollama_models)
            print(f"Found Ollama models: {list([m for m in models.keys() if m.startswith('ollama:')])}")
        else:
            print("No Ollama models found or Ollama is not running.")

    # Update available models if we found any
    if models:
        AVAILABLE_MODELS = models
        print(f"Total available models: {len(AVAILABLE_MODELS)}")
    else:
        print("Warning: No models found. Using default.")

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
    # Check if this is an Ollama model
    if model_id.startswith("ollama:"):
        return get_ollama_config(model_id)
    else:
        # This is a Groq model
        try:
            # Get the current API key
            api_key = get_api_key()
            return [
                {
                    "model": model_id,
                    "api_key": api_key,
                    "base_url": "https://api.groq.com/openai/v1",
                    # Use 'timeout' instead of 'request_timeout' for Groq client
                    "timeout": 60.0
                }
            ]
        except ValueError:
            # If no API key is available, try to use Ollama as fallback
            if is_ollama_available() and OLLAMA_MODELS:
                # Use the first available Ollama model
                ollama_model = next(iter(OLLAMA_MODELS.keys()))
                print(f"No Groq API key available, falling back to Ollama model: {ollama_model}")
                return get_ollama_config(ollama_model)
            else:
                # No Ollama models available either
                raise ValueError("No valid API key for Groq and no Ollama models available")

# Global agent logs (needed for the original structure)
# This will be imported by main.py
agent_logs = []

def get_visualization_suggestions(data_path, user_prompt=None, analyst_model_id="llama3-70b-8192", coder_model_id="llama3-70b-8192"):
    """Analyzes the dataset and suggests visualizations using Autogen agents with GroupChat."""
    global agent_logs, AVAILABLE_MODELS # Ensure we modify the global variables

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
        # Removed Code_Executor agent since ECharts runs in browser

        # --- Load Dataset ---
        df = pd.read_csv(data_path, encoding='latin-1', delimiter=';')
        # Get some basic info for the agents
        num_rows = len(df)
        columns = df.columns.tolist()
        data_head = df.head().to_string()
        data_sample_for_prompt = f"Dataset path: {data_path}\nNumber of rows: {num_rows}\nColumns: {columns}\n\nFirst 5 rows:\n{data_head}\n"

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
        data_analyst = autogen.AssistantAgent(
            name="Data_Analyst",
            system_message=f"""You are an expert data analyst specializing in Italian public finance data.
Your task is to analyze the provided dataset ({data_path}) and identify the most insightful visualizations.
Consider the columns: {columns}.
The data looks like this:
{data_head}

IMPORTANT INSTRUCTIONS:
1. Focus on providing diverse insights that reveal meaningful patterns in the data
2. Prioritize visualizations that show:
   - Financial distributions across provinces or expense types
   - Comparisons between committed amounts (Impegno) and paid amounts (Pagato)
   - Trends or patterns in financial allocations
   - Relationships between different financial metrics

3. For each visualization, provide DETAILED specifications:
   - The exact column names to use (must match the dataset exactly)
   - Precise data transformations with specific columns and operations
   - Appropriate chart type with justification
   - Descriptive titles and axis labels in Italian
   - Sorting and filtering criteria if applicable
   - Color schemes and visual elements recommendations

4. Data Processing Instructions:
   - Be explicit about grouping: "Group by 'Provincia competente'"
   - Specify exact aggregation functions: "Sum 'Impegno totale' for each group"
   - Include sorting: "Sort in descending order by the aggregated 'Impegno totale'"
   - Mention filtering if needed: "Filter to include only the top 10 provinces by total"
   - Suggest data transformations: "Calculate the ratio between 'Pagato totale' and 'Impegno totale'"

5. Visualization Enhancement Suggestions:
   - Recommend appropriate number formatting (e.g., thousands separators for currency)
   - Suggest axis label rotations for better readability
   - Recommend appropriate chart dimensions and layouts
   - Suggest tooltip content and formatting
   - Recommend legend positioning and styling

EXAMPLE FORMAT:
"Visualization 1: Distribuzione dell'Impegno Totale per Provincia
- Data Processing:
  * Group by: 'Provincia competente'
  * Aggregate: Sum 'Impegno totale' for each province
  * Sort: Descending by total 'Impegno totale'
  * Limit: Include only top 8 provinces, group others as 'Altre Province'
- Chart Type: Bar chart (vertical) with data labels
- Title: 'Distribuzione dell'Impegno Totale per Provincia'
- X-axis: Province names (rotated 45 degrees for readability)
- Y-axis: 'Impegno Totale (EUR)' with thousand separators
- Colors: Blue gradient for bars
- Tooltip: Show province name and exact value with thousand separators
- Insight: Reveals which provinces receive the largest financial commitments, highlighting regional disparities in resource allocation"

Remember, the Visualization_Coder will implement your suggestions using Apache ECharts, so be as specific as possible about data processing and visual elements.
""",
            llm_config=analyst_llm_config, # Use analyst specific config
        )

        visualization_coder = autogen.AssistantAgent(
            name="Visualization_Coder",
            system_message=f"""You are an expert in creating data visualizations using Apache ECharts.

            IMPORTANT: Your task is to create ECharts configurations that will be directly parsed as JSON and used in a React application.

            VISUALIZATION BEST PRACTICES:
            1. Always use REAL DATA from the dataset - never use placeholder or dummy data
            2. Process the data appropriately (grouping, aggregation, sorting) as specified by the Data Analyst
            3. Choose appropriate chart types based on the data characteristics and analysis goals
            4. Use clear, descriptive titles and axis labels (in Italian when appropriate)
            5. Include tooltips with formatted values for better user interaction
            6. Use appropriate color schemes that are visually appealing and accessible
            7. Format numbers with thousand separators and appropriate decimal places
            8. Ensure visualizations are not cluttered - limit categories if needed
            9. Add grid configurations to ensure proper spacing and layout
            10. Include legends when multiple series are present

            LAYOUT AND STYLING ENHANCEMENTS:
            1. Center titles and use appropriate font sizes (16px for titles)
            2. Add proper spacing with grid configuration (containLabel: true)
            3. Rotate axis labels when needed for better readability
            4. Use data labels for important values
            5. Add hover effects with emphasis properties
            6. Format tooltips to show relevant information
            7. Use appropriate chart dimensions
            8. Add borders and rounded corners for pie charts
            9. Position legends optimally (usually at bottom for horizontal charts)
            10. Use scroll for legends with many items

            TECHNICAL REQUIREMENTS:
            1. Generate complete ECharts configuration objects as valid JSON
            2. Use double quotes for all keys and string values
            3. Do not use JavaScript features that aren't valid in JSON (like functions or comments)
            4. Make sure all property names are in double quotes
            5. Avoid trailing commas

            Example of a well-formatted ECharts configuration with enhanced styling:
            ```javascript
            {{
              "title": {{
                "text": "Distribuzione per Tipologia di Spesa",
                "left": "center",
                "textStyle": {{
                  "fontSize": 16,
                  "fontWeight": "bold"
                }}
              }},
              "tooltip": {{
                "trigger": "item",
                "formatter": "{{b}}: {{c:,.2f}} EUR ({{d}}%)"
              }},
              "legend": {{
                "type": "scroll",
                "orient": "horizontal",
                "bottom": "bottom",
                "textStyle": {{
                  "fontSize": 10
                }}
              }},
              "grid": {{
                "left": "5%",
                "right": "5%",
                "bottom": "15%",
                "containLabel": true
              }},
              "xAxis": {{
                "type": "category",
                "data": ["Category 1", "Category 2", "Category 3"],
                "axisLabel": {{
                  "rotate": 45,
                  "fontSize": 10
                }}
              }},
              "yAxis": {{
                "type": "value",
                "name": "Value (EUR)",
                "axisLabel": {{
                  "formatter": "{{value:,.0f}}"
                }}
              }},
              "series": [
                {{
                  "name": "Series 1",
                  "type": "bar",
                  "data": [10000, 20000, 30000],
                  "itemStyle": {{
                    "color": "#5470c6"
                  }},
                  "label": {{
                    "show": true,
                    "position": "top",
                    "formatter": "{{c:,.0f}}",
                    "fontSize": 10
                  }}
                }}
              ]
            }}
            ```

            RESPONSE FORMAT:
            ```javascript
            {{
              // Your ECharts configuration here (with proper JSON syntax)
            }}
            ```

            IMPORTANT: Always ensure your configuration uses REAL DATA from the dataset, not placeholder values.""",
            llm_config=coder_llm_config, # Use coder specific config
        )

        user_proxy = autogen.UserProxyAgent(
            name="User_Proxy",
            human_input_mode="NEVER",
            # Let GroupChatManager handle termination logic based on speaker transitions
            # max_consecutive_auto_reply=2, # Manager controls this
            is_termination_msg=lambda x: "```javascript" in x.get("content", "") and "series" in x.get("content", ""), # Terminate when coder provides ECharts config
            code_execution_config=False,
            system_message="You are a proxy for the human user. Your role is to request visualizations and approve them when they look good. When the Visualization_Coder provides complete ECharts configurations, thank them and end the conversation.",
        )

        # --- Group Chat Setup ---
        groupchat = autogen.GroupChat(
            agents=[user_proxy, data_analyst, visualization_coder],
            messages=[],
            max_round=10, # Limit rounds to prevent infinite loops
            # Define speaker selection logic if needed, default is round robin
            # speaker_selection_method="auto"
        )
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config=analyst_llm_config # Manager needs an LLM config too, use analyst's for now
        )

        # --- Chat Initiation ---
        # Initial request for visualizations
        initial_request = f"""Analyze the dataset at {data_path} and provide 3 insightful visualizations using Apache ECharts.
Here is a sample of the data:
{data_sample_for_prompt}

Data Analyst: Please analyze this dataset and suggest 3 insightful visualizations with clear specifications.
Visualization Coder: Once you receive the specifications, create ECharts configurations that can be directly used in a React application."""

        # Follow-up request if user provides a prompt
        follow_up_request = f"""The user asks for a specific visualization: "{user_prompt}"
Analyze this request based on the dataset at {data_path} and create the visualization.
Here is a sample of the data:
{data_sample_for_prompt}

Data Analyst: Please analyze this specific request and suggest how to visualize it effectively.
Visualization Coder: Once you receive the specifications, create an ECharts configuration that can be directly used in a React application."""

        # Determine the message to initiate the chat
        chat_init_message = follow_up_request if user_prompt else initial_request

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

        # Store the conversation in the agent logs
        # global agent_logs # Already declared global
        conversation_log = {
            "timestamp": datetime.now().isoformat(),
            # Log both models used
            "analyst_model": analyst_model_id,
            "coder_model": coder_model_id,
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
        # Keep only the last 100 conversations
        if len(agent_logs) > 100:
            agent_logs = agent_logs[-100:]

        # Extract ECharts configurations from the chat history
        echarts_configs = []
        # Look in messages from the Visualization_Coder
        coder_messages = [m for m in all_messages if m.get("name") == "Visualization_Coder"]

        # Process each message from the Visualization_Coder
        for i, message in enumerate(coder_messages):
            content = message.get("content", "")
            print(f"\n--- Processing Visualization Code {i+1} ---")

            # Extract code between ```javascript and ``` markers
            import re
            js_code_blocks = re.findall(r'```javascript\s*([\s\S]*?)\s*```', content)

            if js_code_blocks:
                for j, js_code in enumerate(js_code_blocks):
                    print(f"Found JavaScript code block {j+1} in message {i+1}")

                    # Clean up the code to extract just the ECharts configuration object
                    # Remove any variable assignments like "option = " or "const option = "
                    cleaned_js = re.sub(r'(const\s+|let\s+|var\s+)?option\s*=\s*', '', js_code)
                    # Remove trailing semicolons
                    cleaned_js = cleaned_js.strip().rstrip(';')

                    try:
                        # Parse the JavaScript object as JSON
                        import json
                        # Handle some common JS syntax that's not valid JSON
                        # Replace single quotes with double quotes
                        cleaned_js = cleaned_js.replace("'", '"')
                        # Remove comments
                        cleaned_js = re.sub(r'//.*?\n', '\n', cleaned_js)
                        cleaned_js = re.sub(r'/\*.*?\*/', '', cleaned_js, flags=re.DOTALL)

                        print(f"Attempting to parse ECharts config: {cleaned_js[:100]}...")
                        echarts_config = json.loads(cleaned_js)
                        echarts_configs.append(echarts_config)
                        print(f"Successfully parsed ECharts configuration {j+1} from message {i+1}")
                    except json.JSONDecodeError as e:
                        print(f"Error parsing ECharts configuration: {str(e)}")
                        print("Attempting to fix common JSON parsing issues...")

                        # Try a more aggressive approach to fix the JSON
                        try:
                            # Replace JavaScript-style object keys without quotes
                            fixed_js = re.sub(r'(\s*)(\w+)(\s*):([^:])', r'\1"\2"\3:\4', cleaned_js)
                            # Fix trailing commas in arrays/objects
                            fixed_js = re.sub(r',(\s*[\]}])', r'\1', fixed_js)

                            print(f"Attempting to parse fixed ECharts config: {fixed_js[:100]}...")
                            echarts_config = json.loads(fixed_js)
                            echarts_configs.append(echarts_config)
                            print(f"Successfully parsed fixed ECharts configuration {j+1} from message {i+1}")
                        except json.JSONDecodeError as e2:
                            print(f"Failed to parse even after fixes: {str(e2)}")
                            # Create a simple fallback chart if parsing fails
                            fallback_config = {
                                "title": {"text": f"Visualization {i+1} (Parsing Error)"},
                                "tooltip": {},
                                "xAxis": {"type": "category", "data": ["Error"]},
                                "yAxis": {"type": "value"},
                                "series": [{"data": [0], "type": "bar"}]
                            }
                            echarts_configs.append(fallback_config)
            else:
                print(f"No JavaScript code blocks found in message {i+1}")
                # Try to find any JSON-like structure in the message
                try:
                    import json
                    # Look for anything that might be a JSON object
                    json_matches = re.findall(r'({[\s\S]*?})', content)
                    for json_str in json_matches:
                        try:
                            config = json.loads(json_str)
                            # Check if it looks like an ECharts config
                            if isinstance(config, dict) and any(key in config for key in ['title', 'series', 'xAxis', 'yAxis']):
                                echarts_configs.append(config)
                                print(f"Found and parsed JSON-like ECharts config in message {i+1}")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"Error searching for JSON structures: {str(e)}")

        # If no ECharts configs were found, create default ones
        if not echarts_configs:
            print("\n=== No valid ECharts configurations were found in the agent conversation. ===")
            print("Creating default visualizations...")

            # Create enhanced default visualizations based on the dataset with real data
            try:
                df = pd.read_csv(data_path, encoding='latin-1', delimiter=';')

                # Ensure numeric columns are properly converted
                numeric_columns = ['Impegno totale', 'Pagato totale']
                for col in numeric_columns:
                    if col in df.columns:
                        # Convert to numeric, coercing errors to NaN
                        df[col] = pd.to_numeric(df[col], errors='coerce')

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

        return {"visualizations": echarts_configs}

    except Exception as e:
        print(f"Error in get_visualization_suggestions: {str(e)}")
        # Log the full traceback for better debugging
        traceback.print_exc()
        return {"error": f"Failed to generate visualizations: {str(e)}"}


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