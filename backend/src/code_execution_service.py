"""
Code Execution Service for Agentic Visualization.

This module provides a secure sandbox for executing Python code,
specifically for generating Plotly visualizations.
"""

import os
import sys
import json
import traceback
import contextlib
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import numpy as np
import re
from datetime import datetime
import uuid
import tempfile
from typing import Dict, Any, Tuple, Optional

# Maximum execution time in seconds
MAX_EXECUTION_TIME = 10

# Allowed modules for code execution
ALLOWED_MODULES = {
    'pandas', 'numpy', 'plotly', 'datetime', 're', 'math', 'json',
    'plotly.express', 'plotly.graph_objects', 'plotly.subplots'
}

class CodeExecutionError(Exception):
    """Exception raised for errors during code execution."""
    pass

def sanitize_code(code: str) -> str:
    """
    Sanitize the code to prevent malicious execution.

    Args:
        code: The Python code to sanitize

    Returns:
        Sanitized code
    """
    # Remove any imports that aren't in the allowed list
    lines = code.split('\n')
    sanitized_lines = []

    for line in lines:
        # Check for import statements
        if re.match(r'^\s*import\s+', line) or re.match(r'^\s*from\s+\S+\s+import', line):
            # Extract the module name
            if 'import' in line and 'from' not in line:
                # Case: import module
                module_match = re.match(r'^\s*import\s+([^\s,]+)', line)
                if module_match:
                    module_name = module_match.group(1)
                    if module_name not in ALLOWED_MODULES:
                        # Skip this import
                        sanitized_lines.append(f"# Skipped: {line} (module not allowed)")
                        continue
            elif 'from' in line:
                # Case: from module import something
                module_match = re.match(r'^\s*from\s+([^\s.]+)', line)
                if module_match:
                    module_name = module_match.group(1)
                    if module_name not in ALLOWED_MODULES:
                        # Skip this import
                        sanitized_lines.append(f"# Skipped: {line} (module not allowed)")
                        continue

        # Check for system calls or file operations
        if any(forbidden in line for forbidden in ['os.system', 'subprocess', 'eval(', 'exec(', '__import__', 'open(']):
            sanitized_lines.append(f"# Skipped: {line} (forbidden operation)")
            continue

        sanitized_lines.append(line)

    return '\n'.join(sanitized_lines)

def execute_code(code: str, data_path: Optional[str] = None) -> Tuple[Dict[str, Any], str, str]:
    """
    Execute Python code in a secure sandbox and return the Plotly figure.

    Args:
        code: The Python code to execute
        data_path: Optional path to a data file to load

    Returns:
        Tuple containing:
        - The Plotly figure as a JSON object
        - The output of the code execution
        - Any error messages
    """
    # Sanitize the code
    sanitized_code = sanitize_code(code)

    # Create a string buffer to capture output
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    # Variables to be exposed in the execution environment
    execution_vars = {
        'pd': pd,
        'np': np,
        'px': px,
        'go': go,
        'json': json,
        'fig': None,  # Will hold the Plotly figure
        'data_path': data_path,
    }

    # Add data loading code if a data path is provided
    if data_path and os.path.exists(data_path):
        file_extension = os.path.splitext(data_path)[1].lower()
        try:
            if file_extension == '.csv':
                # Try different encodings and delimiters
                try:
                    execution_vars['df'] = pd.read_csv(data_path, encoding='latin-1', delimiter=';')
                except:
                    try:
                        execution_vars['df'] = pd.read_csv(data_path, encoding='utf-8')
                    except:
                        execution_vars['df'] = pd.read_csv(data_path)
            elif file_extension == '.xlsx':
                execution_vars['df'] = pd.read_excel(data_path)
            elif file_extension == '.json':
                execution_vars['df'] = pd.read_json(data_path)

            # Ensure numeric columns are properly converted
            if 'df' in execution_vars:
                numeric_columns = ['Impegno totale', 'Pagato totale']
                for col in numeric_columns:
                    if col in execution_vars['df'].columns:
                        # Convert to numeric, coercing errors to NaN
                        execution_vars['df'][col] = pd.to_numeric(execution_vars['df'][col], errors='coerce')
        except Exception as e:
            stderr_buffer.write(f"Warning: Error loading data file: {str(e)}\n")

    try:
        # Redirect stdout and stderr
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            # Execute the code
            exec(sanitized_code, execution_vars)

        # Get the output
        stdout = stdout_buffer.getvalue()
        stderr = stderr_buffer.getvalue()

        # Check if a figure was created
        fig = execution_vars.get('fig')
        if fig is None:
            # Look for any Plotly figure in the execution variables
            for var_name, var_value in execution_vars.items():
                if var_name not in ['pd', 'np', 'px', 'go', 'json', 'data_path', 'df'] and (
                    isinstance(var_value, go.Figure) or
                    hasattr(var_value, 'to_json')
                ):
                    fig = var_value
                    break

        if fig is None:
            return {}, stdout, "No Plotly figure was created. Make sure to assign your figure to a variable named 'fig'."

        # Convert the figure to JSON
        try:
            fig_json = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
            return fig_json, stdout, stderr
        except Exception as json_err:
            # Handle JSON serialization errors
            error_msg = f"Error serializing Plotly figure: {str(json_err)}\n{traceback.format_exc()}"
            return {}, stdout, error_msg

    except Exception as e:
        # Capture the exception
        error_msg = f"Error executing code: {str(e)}\n{traceback.format_exc()}"
        return {}, stdout_buffer.getvalue(), error_msg

def execute_plotly_code(code: str, data_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute Python code that generates a Plotly visualization.

    Args:
        code: The Python code to execute
        data_path: Optional path to a data file to load

    Returns:
        A dictionary containing:
        - 'figure': The Plotly figure as a JSON object
        - 'output': The output of the code execution
        - 'error': Any error messages
        - 'code': The sanitized code that was executed
    """
    try:
        # Fix common string formatting issues in the code
        fixed_code = code

        # Fix common issues with labels dictionary in Plotly
        if "labels=" in fixed_code and "'Provincia'" in fixed_code and "'Impegno totale'" in fixed_code:
            # Look for problematic labels dictionary patterns
            import re
            label_pattern = r"labels\s*=\s*{[^}]*'Provincia'[^}]*'Impegno totale'[^}]*}"
            label_matches = re.findall(label_pattern, fixed_code)

            for match in label_matches:
                # Check if the match has formatting issues
                if "'" not in match.split(":")[0] or "'" not in match.split(":")[-1]:
                    # Try to fix the formatting
                    fixed_match = match.replace("'Provincia', 'Impegno totale': 'Impegno Totale (EUR)'",
                                               "'Provincia': 'Provincia', 'Impegno totale': 'Impegno Totale (EUR)'")
                    fixed_code = fixed_code.replace(match, fixed_match)

        # Execute the code with potential fixes
        sanitized_code = sanitize_code(fixed_code)
        fig_json, stdout, stderr = execute_code(sanitized_code, data_path)

        # If there was an error and we didn't apply any fixes, try with the original code
        if stderr and fixed_code != code:
            print("First attempt failed, trying with original code...")
            sanitized_original = sanitize_code(code)
            fig_json_orig, stdout_orig, stderr_orig = execute_code(sanitized_original, data_path)

            # If the original code worked better, use its results
            if not stderr_orig or len(stderr_orig) < len(stderr):
                fig_json, stdout, stderr = fig_json_orig, stdout_orig, stderr_orig
                sanitized_code = sanitized_original

        # Prepare the response
        response = {
            'figure': fig_json,
            'output': stdout,
            'error': stderr,
            'code': sanitized_code
        }

        return response
    except Exception as e:
        # Catch any unexpected errors in our error handling code
        error_msg = f"Error in execute_plotly_code: {str(e)}\n{traceback.format_exc()}"
        return {
            'figure': {},
            'output': "",
            'error': error_msg,
            'code': code
        }
