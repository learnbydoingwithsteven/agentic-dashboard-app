import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.code_execution_service import (
    sanitize_code,
    execute_code,
    execute_plotly_code
)

class TestCodeExecutionService(unittest.TestCase):
    def setUp(self):
        # Sample valid code
        self.valid_code = """
import pandas as pd
import plotly.express as px

# Create a sample dataframe
df = pd.DataFrame({
    'Category': ['A', 'B', 'C', 'D', 'E'],
    'Value': [10, 20, 30, 40, 50]
})

# Create a bar chart
fig = px.bar(df, x='Category', y='Value', title='Sample Bar Chart')
"""

        # Sample malicious code
        self.malicious_code = """
import pandas as pd
import plotly.express as px
import os

# Attempt to execute system command
os.system('echo "Malicious command"')

# Create a sample dataframe
df = pd.DataFrame({
    'Category': ['A', 'B', 'C', 'D', 'E'],
    'Value': [10, 20, 30, 40, 50]
})

# Create a bar chart
fig = px.bar(df, x='Category', y='Value', title='Sample Bar Chart')
"""

        # Sample invalid code (syntax error)
        self.invalid_code = """
import pandas as pd
import plotly.express as px

# Syntax error
if True
    print("Missing colon")

# Create a sample dataframe
df = pd.DataFrame({
    'Category': ['A', 'B', 'C', 'D', 'E'],
    'Value': [10, 20, 30, 40, 50]
})

# Create a bar chart
fig = px.bar(df, x='Category', y='Value', title='Sample Bar Chart')
"""

        # Sample code with file operations
        self.file_operations_code = """
import pandas as pd
import plotly.express as px

# Attempt to open a file
with open('test.txt', 'w') as f:
    f.write('Test')

# Create a sample dataframe
df = pd.DataFrame({
    'Category': ['A', 'B', 'C', 'D', 'E'],
    'Value': [10, 20, 30, 40, 50]
})

# Create a bar chart
fig = px.bar(df, x='Category', y='Value', title='Sample Bar Chart')
"""

        # Sample expected Plotly figure
        self.expected_figure = {
            'data': [{'type': 'bar', 'x': ['A', 'B', 'C', 'D', 'E'], 'y': [10, 20, 30, 40, 50]}],
            'layout': {'title': {'text': 'Sample Bar Chart'}}
        }

    def test_sanitize_code_valid(self):
        """Test that valid code is not modified by sanitization."""
        sanitized = sanitize_code(self.valid_code)
        self.assertEqual(sanitized.strip(), self.valid_code.strip())

    def test_sanitize_code_malicious(self):
        """Test that malicious code is properly sanitized."""
        sanitized = sanitize_code(self.malicious_code)
        self.assertNotIn('os.system', sanitized)
        self.assertIn('# Skipped:', sanitized)

    def test_sanitize_code_file_operations(self):
        """Test that code with file operations is properly sanitized."""
        sanitized = sanitize_code(self.file_operations_code)
        self.assertNotIn('open(', sanitized)
        self.assertIn('# Skipped:', sanitized)

    @patch('src.code_execution_service.exec')
    def test_execute_code_valid(self, mock_exec):
        """Test execution of valid code."""
        # Mock the exec function to set the fig variable
        def side_effect(code, globals_dict):
            import plotly.graph_objects as go
            globals_dict['fig'] = go.Figure()
            globals_dict['fig'].add_trace(go.Bar(x=['A', 'B', 'C', 'D', 'E'], y=[10, 20, 30, 40, 50]))
            globals_dict['fig'].update_layout(title='Sample Bar Chart')
        
        mock_exec.side_effect = side_effect

        # Execute the code
        fig_json, stdout, stderr = execute_code(self.valid_code)

        # Check that exec was called
        mock_exec.assert_called_once()

        # Check that the figure was returned
        self.assertIsNotNone(fig_json)
        self.assertIn('data', fig_json)
        self.assertIn('layout', fig_json)

        # Check that there are no errors
        self.assertEqual(stderr, '')

    @patch('src.code_execution_service.exec')
    def test_execute_code_invalid(self, mock_exec):
        """Test execution of invalid code."""
        # Mock the exec function to raise a SyntaxError
        mock_exec.side_effect = SyntaxError('invalid syntax')

        # Execute the code
        fig_json, stdout, stderr = execute_code(self.invalid_code)

        # Check that exec was called
        mock_exec.assert_called_once()

        # Check that no figure was returned
        self.assertEqual(fig_json, {})

        # Check that there is an error
        self.assertIn('Error executing code', stderr)
        self.assertIn('SyntaxError', stderr)

    @patch('src.code_execution_service.execute_code')
    def test_execute_plotly_code_valid(self, mock_execute_code):
        """Test execution of valid Plotly code."""
        # Mock the execute_code function to return a figure
        mock_execute_code.return_value = (self.expected_figure, 'Output', '')

        # Execute the code
        result = execute_plotly_code(self.valid_code)

        # Check that execute_code was called
        mock_execute_code.assert_called_once()

        # Check that the result contains the expected keys
        self.assertIn('figure', result)
        self.assertIn('output', result)
        self.assertIn('code', result)

        # Check that the figure is correct
        self.assertEqual(result['figure'], self.expected_figure)

        # Check that there is no error
        self.assertNotIn('error', result)

    @patch('src.code_execution_service.execute_code')
    def test_execute_plotly_code_error(self, mock_execute_code):
        """Test execution of Plotly code that results in an error."""
        # Mock the execute_code function to return an error
        mock_execute_code.return_value = ({}, 'Output', 'Error message')

        # Execute the code
        result = execute_plotly_code(self.invalid_code)

        # Check that execute_code was called
        mock_execute_code.assert_called_once()

        # Check that the result contains the expected keys
        self.assertIn('output', result)
        self.assertIn('error', result)
        self.assertIn('code', result)

        # Check that the error message is correct
        self.assertEqual(result['error'], 'Error message')

    @patch('src.code_execution_service.pd.read_csv')
    @patch('src.code_execution_service.execute_code')
    def test_execute_plotly_code_with_data(self, mock_execute_code, mock_read_csv):
        """Test execution of Plotly code with a data file."""
        # Mock the execute_code function to return a figure
        mock_execute_code.return_value = (self.expected_figure, 'Output', '')

        # Mock the pandas read_csv function
        mock_read_csv.return_value = pd.DataFrame({
            'Category': ['A', 'B', 'C', 'D', 'E'],
            'Value': [10, 20, 30, 40, 50]
        })

        # Execute the code with a data path
        result = execute_plotly_code(self.valid_code, 'test.csv')

        # Check that execute_code was called with the data path
        mock_execute_code.assert_called_once()
        self.assertEqual(mock_execute_code.call_args[0][1], 'test.csv')

        # Check that the result contains the expected keys
        self.assertIn('figure', result)
        self.assertIn('output', result)
        self.assertIn('code', result)

        # Check that the figure is correct
        self.assertEqual(result['figure'], self.expected_figure)

        # Check that there is no error
        self.assertNotIn('error', result)

if __name__ == '__main__':
    unittest.main()
