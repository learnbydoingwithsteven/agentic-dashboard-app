import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Sample visualization result
        self.sample_visualization_result = {
            'conversation_history': 'Sample conversation',
            'code_blocks': ['import pandas as pd\nimport plotly.express as px\n\nfig = px.bar(df, x="Category", y="Value")'],
            'figure': {
                'data': [{'type': 'bar', 'x': ['A', 'B', 'C'], 'y': [10, 20, 30]}],
                'layout': {'title': 'Sample Plot'}
            },
            'echarts_config': {
                'title': {'text': 'Sample Chart'},
                'xAxis': {'type': 'category', 'data': ['A', 'B', 'C']},
                'yAxis': {'type': 'value'},
                'series': [{'type': 'bar', 'data': [10, 20, 30]}]
            }
        }

        # Sample dataset summary
        self.sample_dataset_summary = {
            'num_rows': 5,
            'num_columns': 3,
            'column_types': {
                'Category': 'object',
                'Value1': 'int64',
                'Value2': 'int64'
            },
            'head': [
                {'Category': 'A', 'Value1': 10, 'Value2': 5},
                {'Category': 'B', 'Value1': 20, 'Value2': 15},
                {'Category': 'C', 'Value1': 30, 'Value2': 25},
                {'Category': 'D', 'Value1': 40, 'Value2': 35},
                {'Category': 'E', 'Value1': 50, 'Value2': 45}
            ],
            'describe': {
                'Value1': {
                    'count': 5,
                    'mean': 30,
                    'std': 15.81,
                    'min': 10,
                    'max': 50
                },
                'Value2': {
                    'count': 5,
                    'mean': 25,
                    'std': 15.81,
                    'min': 5,
                    'max': 45
                }
            }
        }

    def test_root(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())
        self.assertIn('message', response.json())
        self.assertIn('endpoints', response.json())

    @patch('src.main.get_visualization_suggestions')
    def test_get_initial_visualizations(self, mock_get_visualization_suggestions):
        # Mock the get_visualization_suggestions function to return our sample result
        mock_get_visualization_suggestions.return_value = self.sample_visualization_result

        # Set the last_uploaded_file_path
        import src.main
        src.main.last_uploaded_file_path = 'test.csv'

        # Call the API endpoint
        response = self.client.get(
            '/api/visualizations?analyst_model=llama3-70b-8192&coder_model=llama3-70b-8192&manager_model=llama3-70b-8192'
        )

        # Check that the function was called with the right parameters
        mock_get_visualization_suggestions.assert_called_once()

        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.sample_visualization_result)

    @patch('src.main.get_visualization_suggestions', side_effect=Exception('Test error'))
    def test_get_initial_visualizations_error(self, mock_get_visualization_suggestions):
        # Set the last_uploaded_file_path
        import src.main
        src.main.last_uploaded_file_path = 'test.csv'

        # Call the API endpoint
        response = self.client.get(
            '/api/visualizations?analyst_model=llama3-70b-8192&coder_model=llama3-70b-8192&manager_model=llama3-70b-8192'
        )

        # Check that the function was called with the right parameters
        mock_get_visualization_suggestions.assert_called_once()

        # Check that the response indicates an error
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Failed to get initial visualizations: Test error')

    @patch('src.main.get_dataset_visualizations')
    def test_data_exploration(self, mock_get_dataset_visualizations):
        # Mock the get_dataset_visualizations function to return our sample result
        mock_get_dataset_visualizations.return_value = {
            'summary': self.sample_dataset_summary,
            'visualizations': [
                {'title': 'Bar Chart', 'type': 'bar', 'config': {}},
                {'title': 'Pie Chart', 'type': 'pie', 'config': {}}
            ]
        }

        # Set the last_uploaded_file_path
        import src.main
        src.main.last_uploaded_file_path = 'test.csv'

        # Call the API endpoint
        response = self.client.get('/api/data_exploration')

        # Check that the function was called
        mock_get_dataset_visualizations.assert_called_once()

        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
        self.assertIn('summary', response.json())
        self.assertIn('visualizations', response.json())

    @patch('src.main.execute_plotly_code')
    def test_execute_code(self, mock_execute_plotly_code):
        # Mock the execute_plotly_code function to return a result
        mock_execute_plotly_code.return_value = {
            'figure': self.sample_visualization_result['figure'],
            'output': 'Code executed successfully'
        }

        # Call the API endpoint
        response = self.client.post(
            '/api/execute_code',
            json={'code': 'import plotly.express as px\nfig = px.bar(df, x="Category", y="Value")'}
        )

        # Check that the function was called with the right parameters
        mock_execute_plotly_code.assert_called_once()

        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
        self.assertIn('figure', response.json())
        self.assertIn('output', response.json())

    def test_check_api_key(self):
        # Mock the fetch_available_models function
        with patch('src.main.fetch_available_models') as mock_fetch:
            # Set up the mock to update AVAILABLE_MODELS
            def side_effect():
                import src.main
                src.main.AVAILABLE_MODELS = {'llama3-70b-8192': 'Groq LLaMA 3 70B'}
            mock_fetch.side_effect = side_effect

            # Call the API endpoint
            response = self.client.get(
                '/api/check_api_key',
                headers={'X-API-KEY': 'test_key'}
            )

            # Check that the function was called
            mock_fetch.assert_called_once()

            # Check that the response is correct
            self.assertEqual(response.status_code, 200)
            self.assertIn('available_models', response.json())

    def test_admin_logs(self):
        # Mock the agent_logs
        import src.main
        src.main.agent_logs = [
            {'timestamp': '2023-01-01T00:00:00', 'type': 'info', 'content': 'Test log', 'step': 1}
        ]

        # Call the API endpoint
        response = self.client.get('/api/admin/logs')

        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
        self.assertIn('logs', response.json())

if __name__ == '__main__':
    unittest.main()
