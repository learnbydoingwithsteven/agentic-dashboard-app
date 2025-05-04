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

        # Check for system calls or file operations or attempts to start a server
        if any(forbidden in line for forbidden in ['os.system', 'subprocess', 'eval(', 'exec(', '__import__', 'open(', 'plotly.offline.plot(fig, auto_open=True)']):
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
                for encoding in ['latin-1', 'utf-8', 'cp1252']:
                    for delimiter in [';', ',', '\t']:
                        try:
                            execution_vars['df'] = pd.read_csv(data_path, encoding=encoding, delimiter=delimiter)
                            # If we got here, the read was successful
                            stdout_buffer.write(f"Successfully loaded CSV with encoding={encoding}, delimiter={delimiter}\n")
                            break
                        except Exception:
                            continue
                    if 'df' in execution_vars:
                        break

                # If all attempts failed, try one more time with pandas defaults
                if 'df' not in execution_vars:
                    execution_vars['df'] = pd.read_csv(data_path)

            elif file_extension == '.xlsx':
                execution_vars['df'] = pd.read_excel(data_path)
            elif file_extension == '.json':
                execution_vars['df'] = pd.read_json(data_path)
            else:
                # Try to load as CSV anyway
                try:
                    execution_vars['df'] = pd.read_csv(data_path)
                except:
                    stderr_buffer.write(f"Warning: Unsupported file extension {file_extension}. Tried CSV format but failed.\n")

            # Auto-detect and convert numeric columns
            if 'df' in execution_vars:
                # Print dataframe info for debugging
                buffer = io.StringIO()
                execution_vars['df'].info(buf=buffer)
                stdout_buffer.write(f"DataFrame info:\n{buffer.getvalue()}\n")

                # Try to convert all columns that look numeric
                for col in execution_vars['df'].columns:
                    # Skip columns that are already numeric
                    if pd.api.types.is_numeric_dtype(execution_vars['df'][col]):
                        continue

                    # Check if column contains mostly numeric values
                    try:
                        # Try to convert and count how many values were successfully converted
                        numeric_series = pd.to_numeric(execution_vars['df'][col], errors='coerce')
                        non_na_count = numeric_series.count()
                        original_non_na_count = execution_vars['df'][col].count()

                        # If at least 70% of values could be converted to numeric, do the conversion
                        if original_non_na_count > 0 and non_na_count / original_non_na_count >= 0.7:
                            execution_vars['df'][col] = numeric_series
                            stdout_buffer.write(f"Converted column '{col}' to numeric type\n")
                    except:
                        # Skip columns that cause errors
                        continue

                # Also try specific columns that might be numeric based on common names
                common_numeric_columns = [
                    'Impegno totale', 'Pagato totale', 'amount', 'value', 'price',
                    'cost', 'revenue', 'sales', 'quantity', 'count', 'total'
                ]

                for col in execution_vars['df'].columns:
                    col_lower = col.lower()
                    if any(numeric_name in col_lower for numeric_name in common_numeric_columns):
                        try:
                            execution_vars['df'][col] = pd.to_numeric(execution_vars['df'][col], errors='coerce')
                            stdout_buffer.write(f"Converted column '{col}' to numeric based on name pattern\n")
                        except:
                            stderr_buffer.write(f"Warning: Failed to convert column '{col}' to numeric\n")
        except Exception as e:
            stderr_buffer.write(f"Warning: Error loading data file: {str(e)}\n{traceback.format_exc()}\n")

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
        if "labels=" in fixed_code:
            # Look for problematic labels dictionary patterns
            import re

            # Pattern 1: Multiple keys without proper formatting
            # Example: 'key1', 'key2': 'value'
            pattern1 = r"labels\s*=\s*{[^}]*'[^']+',\s*'[^']+':\s*'[^']+'[^}]*}"
            matches1 = re.findall(pattern1, fixed_code)

            for match in matches1:
                try:
                    # Extract the problematic part
                    dict_content = re.search(r"{([^}]*)}", match).group(1)
                    parts = dict_content.split(',')
                    fixed_parts = []

                    i = 0
                    while i < len(parts):
                        part = parts[i].strip()
                        # Check if this part contains a colon
                        if ':' in part:
                            fixed_parts.append(part)
                        else:
                            # This part doesn't have a colon, so it needs to be combined with the next part
                            if i + 1 < len(parts):
                                next_part = parts[i + 1].strip()
                                if ':' in next_part:
                                    # Extract the key from the current part
                                    key = part.strip("'\" ")
                                    # Extract the value from the next part
                                    value_parts = next_part.split(':')
                                    if len(value_parts) >= 2:
                                        next_key = value_parts[0].strip("'\" ")
                                        value = ':'.join(value_parts[1:]).strip()
                                        # Create two separate key-value pairs
                                        fixed_parts.append(f"'{key}': '{key}'")
                                        fixed_parts.append(f"'{next_key}': {value}")
                                        i += 1  # Skip the next part since we've processed it
                            else:
                                # This is the last part and doesn't have a colon, add it as is
                                fixed_parts.append(part)
                        i += 1

                    # Reconstruct the dictionary
                    fixed_dict = "{" + ", ".join(fixed_parts) + "}"
                    fixed_match = match.replace(re.search(r"{([^}]*)}", match).group(0), fixed_dict)
                    fixed_code = fixed_code.replace(match, fixed_match)
                except Exception as e:
                    print(f"Error fixing labels dictionary: {e}")

        # Fix string formatting issues with f-strings
        # Look for patterns like: f"{variable}" where variable might be a dictionary key
        f_string_pattern = r'f"[^"]*{([^}]*)}"'
        f_string_matches = re.findall(f_string_pattern, fixed_code)

        for match in f_string_matches:
            if "'" in match or '"' in match:
                # This might be a problematic f-string with quotes inside
                try:
                    # Replace with a safer version using string concatenation
                    old_pattern = f'f"{{{match}}}"'
                    new_pattern = f'str({match})'
                    fixed_code = fixed_code.replace(old_pattern, new_pattern)
                except Exception as e:
                    print(f"Error fixing f-string: {e}")

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

        # If we still have an error with "Invalid format specifier", try a more aggressive fix
        if "Invalid format specifier" in stderr:
            print("Detected 'Invalid format specifier' error, applying aggressive fix...")
            print(f"Error details: {stderr}")
            print(f"Problematic code section: {code}")

            # Replace all f-strings with simple strings to avoid format specifier issues
            aggressive_fixed_code = re.sub(r'f"([^"]*)"', r'"\1"', fixed_code)

            # Replace problematic dictionary patterns more aggressively
            # Look for patterns like 'key1', 'key2': 'value' in labels dictionaries
            label_pattern = r"labels\s*=\s*{([^}]*)}"
            label_matches = re.findall(label_pattern, aggressive_fixed_code)

            for label_content in label_matches:
                # Check if there are multiple keys without proper formatting
                if re.search(r"'[^']+',\s*'[^']+':", label_content):
                    fixed_content = label_content
                    # Find all instances of 'key1', 'key2': 'value'
                    key_pattern = r"'([^']+)',\s*'([^']+)':\s*'([^']+)'"
                    key_matches = re.findall(key_pattern, label_content)

                    for key1, key2, value in key_matches:
                        # Replace with proper dictionary format
                        old_str = f"'{key1}', '{key2}': '{value}'"
                        new_str = f"'{key1}': '{key1}', '{key2}': '{value}'"
                        fixed_content = fixed_content.replace(old_str, new_str)

                    # Replace in the original code
                    aggressive_fixed_code = aggressive_fixed_code.replace(
                        f"labels = {{{label_content}}}",
                        f"labels = {{{fixed_content}}}"
                    )

            # Also handle the specific case we know about
            aggressive_fixed_code = aggressive_fixed_code.replace(
                "'Provincia', 'Impegno totale': 'Impegno Totale (EUR)'",
                "'Provincia': 'Provincia', 'Impegno totale': 'Impegno Totale (EUR)'"
            )

            # Extract specific error patterns from the error message
            if "Invalid format specifier" in stderr:
                error_pattern = r"Invalid format specifier\s+'([^']+)'"
                error_match = re.search(error_pattern, stderr)
                if error_match:
                    problematic_str = error_match.group(1)
                    print(f"Found problematic format specifier: '{problematic_str}'")

                    # Try to fix this specific pattern
                    if "', '" in problematic_str and "': '" in problematic_str:
                        parts = problematic_str.split("', '")
                        if len(parts) >= 2:
                            key1 = parts[0].strip()
                            rest = parts[1].strip()
                            if ": '" in rest:
                                key2_value = rest.split(": '", 1)
                                if len(key2_value) == 2:
                                    key2 = key2_value[0].strip()
                                    value = key2_value[1].strip().rstrip("'")

                                    old_str = f"'{key1}', '{key2}': '{value}'"
                                    new_str = f"'{key1}': '{key1}', '{key2}': '{value}'"

                                    print(f"Fixing specific error pattern: {old_str} -> {new_str}")
                                    aggressive_fixed_code = aggressive_fixed_code.replace(old_str, new_str)

            # Handle more general cases with different quote styles and spacing
            # This pattern matches cases like "key1", "key2": "value" or 'key1', 'key2': "value", etc.
            general_pattern = r"[\"']([^\"']+)[\"'],\s*[\"']([^\"']+)[\"']:\s*[\"']([^\"']+)[\"']"

            # Find all matches in the entire code
            for match in re.finditer(general_pattern, aggressive_fixed_code):
                full_match = match.group(0)
                key1 = match.group(1)
                key2 = match.group(2)
                value = match.group(3)

                # Check if this is inside a dictionary context (to avoid false positives)
                # Get some context around the match
                start_pos = max(0, match.start() - 20)
                end_pos = min(len(aggressive_fixed_code), match.end() + 20)
                context = aggressive_fixed_code[start_pos:end_pos]

                # Only fix if it looks like it's in a dictionary
                if '{' in context and '}' in context and ('labels' in context or 'dict' in context):
                    # Create the fixed version with consistent quote style
                    fixed_str = f"'{key1}': '{key1}', '{key2}': '{value}'"
                    aggressive_fixed_code = aggressive_fixed_code.replace(full_match, fixed_str)
                    print(f"Fixed dictionary format: '{full_match}' -> '{fixed_str}'")

            # Try executing with the aggressive fixes
            sanitized_aggressive = sanitize_code(aggressive_fixed_code)
            fig_json_agg, stdout_agg, stderr_agg = execute_code(sanitized_aggressive, data_path)

            # If the aggressive fix worked better, use its results
            if not stderr_agg or (stderr and len(stderr_agg) < len(stderr)):
                fig_json, stdout, stderr = fig_json_agg, stdout_agg, stderr_agg
                sanitized_code = sanitized_aggressive

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
