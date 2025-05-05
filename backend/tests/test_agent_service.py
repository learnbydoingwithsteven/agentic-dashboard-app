import unittest
import os
import sys
import pandas as pd
import json
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agent_service import (
    generate_visualizations,
    extract_code_blocks,
    extract_plotly_figure,
    extract_echarts_config,
    create_default_visualization,
    get_visualization_suggestions,
    get_api_key,
    fetch_available_models,
    cancel_current_job
)

class TestAgentService(unittest.TestCase):
    def setUp(self):
        # Create a sample DataFrame for testing
        self.test_df = pd.DataFrame({
            'Category': ['A', 'B', 'C', 'D', 'E'],
            'Value': [10, 20, 30, 40, 50]
        })

        # Sample conversation history
        self.sample_conversation = """
        Data Analyst: I suggest a bar chart showing Value by Category.

        Visualization Coder: Here's the code:

        ```python
        import pandas as pd
        import plotly.express as px

        # Check if required columns exist
        cat_col = 'Category'
        num_col = 'Value'

        if cat_col not in df.columns or num_col not in df.columns:
            fig = px.bar(title="Error: Columns not found")
        else:
            fig = px.bar(
                df,
                x=cat_col,
                y=num_col,
                title='Value by Category'
            )
        ```
        """

        # Sample Plotly figure
        self.sample_plotly_figure = {
            'data': [{'type': 'bar', 'x': ['A', 'B', 'C', 'D', 'E'], 'y': [10, 20, 30, 40, 50]}],
            'layout': {'title': 'Value by Category'}
        }

        # Sample ECharts config
        self.sample_echarts_config = {
            'title': {'text': 'Value by Category'},
            'xAxis': {'type': 'category', 'data': ['A', 'B', 'C', 'D', 'E']},
            'yAxis': {'type': 'value'},
            'series': [{'type': 'bar', 'data': [10, 20, 30, 40, 50]}]
        }

    @patch('agent_service.autogen.UserProxyAgent')
    @patch('agent_service.autogen.AssistantAgent')
    @patch('agent_service.autogen.GroupChat')
    @patch('agent_service.autogen.GroupChatManager')
    @patch('agent_service.pd.read_csv')
    def test_generate_visualizations(self, mock_read_csv, mock_manager, mock_groupchat,
                                    mock_assistant, mock_user_proxy):
        # Mock the pandas read_csv to return our test DataFrame
        mock_read_csv.return_value = self.test_df

        # Mock the chat manager to return our sample conversation
        mock_manager_instance = mock_manager.return_value
        mock_manager_instance.run.return_value = self.sample_conversation

        # Call the function
        result = generate_visualizations('test.csv', 'Show me a bar chart')

        # Check that the function was called with the right parameters
        mock_read_csv.assert_called_once()
        mock_manager_instance.run.assert_called_once()

        # Check that the result contains the expected keys
        self.assertIn('conversation_history', result)
        self.assertIn('code_blocks', result)

        # We can't easily check the exact content because of the mocking,
        # but we can check that the function returned something
        self.assertIsNotNone(result)

    def test_extract_code_blocks(self):
        # Test with our sample conversation
        code_blocks = extract_code_blocks(self.sample_conversation)

        # Check that we extracted one code block
        self.assertEqual(len(code_blocks), 1)

        # Check that the code block contains the expected content
        self.assertIn('import pandas as pd', code_blocks[0])
        self.assertIn('import plotly.express as px', code_blocks[0])
        self.assertIn('fig = px.bar(', code_blocks[0])

    def test_extract_plotly_figure(self):
        # Create a sample code block that would generate a Plotly figure
        code_block = """
        import pandas as pd
        import plotly.express as px

        df = pd.DataFrame({
            'Category': ['A', 'B', 'C', 'D', 'E'],
            'Value': [10, 20, 30, 40, 50]
        })

        fig = px.bar(
            df,
            x='Category',
            y='Value',
            title='Value by Category'
        )
        """

        # Mock the globals and locals dictionaries
        mock_globals = {}
        mock_locals = {'df': self.test_df}

        # Mock exec to set fig in locals
        def mock_exec(code, globals_dict, locals_dict):
            locals_dict['fig'] = MagicMock()
            locals_dict['fig'].to_dict.return_value = self.sample_plotly_figure

        # Patch exec
        with patch('builtins.exec', mock_exec):
            # Call the function
            figure = extract_plotly_figure(code_block, mock_globals, mock_locals)

            # Check that we got a figure
            self.assertIsNotNone(figure)

            # Check that the figure has the expected structure
            self.assertIn('data', figure)
            self.assertIn('layout', figure)

    def test_extract_echarts_config(self):
        # Create a sample code block that would generate an ECharts config
        code_block = """
        import pandas as pd

        df = pd.DataFrame({
            'Category': ['A', 'B', 'C', 'D', 'E'],
            'Value': [10, 20, 30, 40, 50]
        })

        echarts_config = {
            'title': {'text': 'Value by Category'},
            'xAxis': {'type': 'category', 'data': df['Category'].tolist()},
            'yAxis': {'type': 'value'},
            'series': [{'type': 'bar', 'data': df['Value'].tolist()}]
        }
        """

        # Mock the globals and locals dictionaries
        mock_globals = {}
        mock_locals = {'df': self.test_df}

        # Mock exec to set echarts_config in locals
        def mock_exec(code, globals_dict, locals_dict):
            locals_dict['echarts_config'] = self.sample_echarts_config

        # Patch exec
        with patch('builtins.exec', mock_exec):
            # Call the function
            config = extract_echarts_config(code_block, mock_globals, mock_locals)

            # Check that we got a config
            self.assertIsNotNone(config)

            # Check that the config has the expected structure
            self.assertIn('title', config)
            self.assertIn('xAxis', config)
            self.assertIn('yAxis', config)
            self.assertIn('series', config)

    @patch('agent_service.pd.read_csv')
    def test_create_default_visualization(self, mock_read_csv):
        # Mock the pandas read_csv to return our test DataFrame
        mock_read_csv.return_value = self.test_df

        # Call the function
        result = create_default_visualization('test.csv')

        # Check that the function was called with the right parameters
        mock_read_csv.assert_called_once()

        # Check that the result contains the expected keys
        self.assertIn('figure', result)
        self.assertIn('echarts_config', result)

        # Check that the figure has the expected structure
        self.assertIn('data', result['figure'])
        self.assertIn('layout', result['figure'])

        # Check that the ECharts config has the expected structure
        self.assertIn('title', result['echarts_config'])
        self.assertIn('xAxis', result['echarts_config'])
        self.assertIn('yAxis', result['echarts_config'])
        self.assertIn('series', result['echarts_config'])

    @patch('os.environ.get')
    def test_get_api_key_groq(self, mock_environ_get):
        """Test getting the API key when using Groq."""
        # Mock the environment variables
        mock_environ_get.side_effect = lambda key, default=None: 'test_key' if key == 'GROQ_API_KEY' else None

        # Call the function
        api_key = get_api_key()

        # Check that the API key is correct
        self.assertEqual(api_key, 'test_key')

    @patch('os.environ.get')
    def test_get_api_key_ollama(self, mock_environ_get):
        """Test getting the API key when using Ollama."""
        # Mock the environment variables
        def mock_get(key, default=None):
            if key == 'GROQ_API_KEY':
                return None
            elif key == 'USE_OLLAMA':
                return 'true'
            return default

        mock_environ_get.side_effect = mock_get

        # Call the function
        api_key = get_api_key()

        # Check that a dummy key is returned
        self.assertEqual(api_key, 'dummy_key_for_ollama')

    @patch('os.environ.get')
    def test_get_api_key_missing(self, mock_environ_get):
        """Test getting the API key when it's missing and not using Ollama."""
        # Mock the environment variables
        mock_environ_get.return_value = None

        # Call the function and check that it raises an error
        with self.assertRaises(ValueError):
            get_api_key()

    @patch('src.agent_service.groq.Groq')
    def test_fetch_available_models_groq(self, mock_groq):
        """Test fetching available models from Groq."""
        # Mock the Groq client
        mock_client = MagicMock()
        mock_groq.return_value = mock_client

        # Mock the models.list method
        mock_models = MagicMock()
        mock_models.data = [
            {'id': 'llama3-70b-8192', 'owned_by': 'groq'},
            {'id': 'mixtral-8x7b-32768', 'owned_by': 'groq'}
        ]
        mock_client.models.list.return_value = mock_models

        # Set up environment variables
        with patch('os.environ.get') as mock_environ_get:
            mock_environ_get.side_effect = lambda key, default=None: 'test_key' if key == 'GROQ_API_KEY' else None

            # Call the function
            fetch_available_models()

            # Check that the Groq client was created with the right API key
            mock_groq.assert_called_once_with(api_key='test_key')

            # Check that models.list was called
            mock_client.models.list.assert_called_once()

    @patch('src.agent_service.subprocess.run')
    def test_fetch_available_models_ollama(self, mock_run):
        """Test fetching available models from Ollama."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "NAME TAG SIZE MODIFIED\nllama3 latest 4.7 GB 2 days ago\nmistral latest 4.1 GB 3 days ago"
        mock_run.return_value = mock_process

        # Set up environment variables
        with patch('os.environ.get') as mock_environ_get:
            def mock_get(key, default=None):
                if key == 'GROQ_API_KEY':
                    return 'test_key'
                elif key == 'USE_OLLAMA':
                    return 'true'
                return default

            mock_environ_get.side_effect = mock_get

            # Call the function
            fetch_available_models()

            # Check that subprocess.run was called with the right command
            mock_run.assert_called_once_with(['ollama', 'list'], capture_output=True, text=True)

    def test_cancel_current_job(self):
        """Test cancelling the current job."""
        # Set up the current job ID
        import src.agent_service
        src.agent_service.current_job_id = 'test_job_id'
        src.agent_service.cancel_requested = False

        # Call the function
        result = cancel_current_job()

        # Check that the cancellation was requested
        self.assertTrue(src.agent_service.cancel_requested)

        # Check that the function returned success
        self.assertEqual(result, {'status': 'success', 'message': 'Cancellation requested for job test_job_id'})

    def test_cancel_current_job_no_job(self):
        """Test cancelling when there's no current job."""
        # Set up no current job
        import src.agent_service
        src.agent_service.current_job_id = None
        src.agent_service.cancel_requested = False

        # Call the function
        result = cancel_current_job()

        # Check that the function returned an error
        self.assertEqual(result, {'status': 'error', 'message': 'No active job to cancel'})

        # Check that cancel_requested is still False
        self.assertFalse(src.agent_service.cancel_requested)

if __name__ == '__main__':
    unittest.main()
