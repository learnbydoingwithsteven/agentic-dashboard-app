import unittest
import os
import sys
import pandas as pd
import json
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data_exploration_service import (
    load_dataset,
    get_dataset_summary,
    generate_barchart_by_category,
    generate_piechart_by_category,
    generate_stacked_barchart_comparison,
    get_dataset_visualizations,
    _find_columns
)

class TestDataExplorationService(unittest.TestCase):
    def setUp(self):
        # Create a sample DataFrame for testing
        self.test_df = pd.DataFrame({
            'Category': ['A', 'B', 'C', 'D', 'E'],
            'Value1': [10, 20, 30, 40, 50],
            'Value2': [5, 15, 25, 35, 45]
        })

        # Create a sample CSV content
        self.csv_content = "Category,Value1,Value2\nA,10,5\nB,20,15\nC,30,25\nD,40,35\nE,50,45"

        # Create a sample Excel content (binary)
        self.excel_content = b'sample excel content'

        # Create a sample JSON content
        self.json_content = json.dumps([
            {"Category": "A", "Value1": 10, "Value2": 5},
            {"Category": "B", "Value1": 20, "Value2": 15},
            {"Category": "C", "Value1": 30, "Value2": 25},
            {"Category": "D", "Value1": 40, "Value2": 35},
            {"Category": "E", "Value1": 50, "Value2": 45}
        ])

    @patch('data_exploration_service.pd.read_csv')
    def test_load_dataset_csv(self, mock_read_csv):
        # Mock the pandas read_csv to return our test DataFrame
        mock_read_csv.return_value = self.test_df

        # Call the function with a CSV file path
        df, message = load_dataset('test.csv')

        # Check that the function was called with the right parameters
        mock_read_csv.assert_called()

        # Check that we got the expected DataFrame
        pd.testing.assert_frame_equal(df, self.test_df)

        # Check that the message indicates success
        self.assertIn('Successfully loaded', message)

    @patch('data_exploration_service.pd.read_excel')
    @patch('data_exploration_service.pd.read_csv', side_effect=Exception('CSV read failed'))
    def test_load_dataset_excel(self, mock_read_csv, mock_read_excel):
        # Mock the pandas read_excel to return our test DataFrame
        mock_read_excel.return_value = self.test_df

        # Call the function with an Excel file path
        df, message = load_dataset('test.xlsx')

        # Check that the function was called with the right parameters
        mock_read_excel.assert_called_once()

        # Check that we got the expected DataFrame
        pd.testing.assert_frame_equal(df, self.test_df)

        # Check that the message indicates success
        self.assertIn('Successfully loaded', message)

    @patch('data_exploration_service.pd.read_json')
    @patch('data_exploration_service.pd.read_excel', side_effect=Exception('Excel read failed'))
    @patch('data_exploration_service.pd.read_csv', side_effect=Exception('CSV read failed'))
    def test_load_dataset_json(self, mock_read_csv, mock_read_excel, mock_read_json):
        # Mock the pandas read_json to return our test DataFrame
        mock_read_json.return_value = self.test_df

        # Call the function with a JSON file path
        df, message = load_dataset('test.json')

        # Check that the function was called with the right parameters
        mock_read_json.assert_called_once()

        # Check that we got the expected DataFrame
        pd.testing.assert_frame_equal(df, self.test_df)

        # Check that the message indicates success
        self.assertIn('Successfully loaded', message)

    @patch('data_exploration_service.pd.read_csv', side_effect=Exception('CSV read failed'))
    @patch('data_exploration_service.pd.read_excel', side_effect=Exception('Excel read failed'))
    @patch('data_exploration_service.pd.read_json', side_effect=Exception('JSON read failed'))
    @patch('data_exploration_service.pd.read_parquet', side_effect=Exception('Parquet read failed'))
    @patch('data_exploration_service.pd.read_feather', side_effect=Exception('Feather read failed'))
    @patch('data_exploration_service.pd.read_hdf', side_effect=Exception('HDF read failed'))
    def test_load_dataset_fallback(self, mock_read_hdf, mock_read_feather, mock_read_parquet,
                                  mock_read_json, mock_read_excel, mock_read_csv):
        # Call the function with a file path that will fail all loading attempts
        df, message = load_dataset('test.unknown')

        # Check that all read functions were called
        mock_read_csv.assert_called()
        mock_read_excel.assert_called()

        # Check that we got a fallback DataFrame
        self.assertEqual(df.shape[0], 5)  # Should have 5 rows
        self.assertEqual(df.shape[1], 2)  # Should have 2 columns

        # Check that the message indicates failure
        self.assertIn('Failed to load', message)

    def test_get_dataset_summary(self):
        # Call the function with our test DataFrame
        summary = get_dataset_summary(self.test_df)

        # Check that the summary contains the expected keys
        self.assertIn('num_rows', summary)
        self.assertIn('num_columns', summary)
        self.assertIn('column_types', summary)
        self.assertIn('head', summary)
        self.assertIn('describe', summary)

        # Check that the summary values are correct
        self.assertEqual(summary['num_rows'], 5)
        self.assertEqual(summary['num_columns'], 3)
        self.assertEqual(len(summary['column_types']), 3)
        self.assertIn('Category', summary['column_types'])
        self.assertIn('Value1', summary['column_types'])
        self.assertIn('Value2', summary['column_types'])

    def test_generate_barchart_by_category(self):
        # Call the function with our test DataFrame
        chart_config = generate_barchart_by_category(self.test_df, 'Category', 'Value1', 'Test Bar Chart')

        # Check that the chart config contains the expected keys
        self.assertIn('title', chart_config)
        self.assertIn('xAxis', chart_config)
        self.assertIn('yAxis', chart_config)
        self.assertIn('series', chart_config)

        # Check that the chart data is correct
        self.assertEqual(chart_config['title']['text'], 'Test Bar Chart')
        self.assertEqual(len(chart_config['xAxis']['data']), 5)  # 5 categories
        self.assertEqual(len(chart_config['series'][0]['data']), 5)  # 5 data points

    def test_generate_piechart_by_category(self):
        # Call the function with our test DataFrame
        chart_config = generate_piechart_by_category(self.test_df, 'Category', 'Value1', 'Test Pie Chart')

        # Check that the chart config contains the expected keys
        self.assertIn('title', chart_config)
        self.assertIn('series', chart_config)

        # Check that the chart data is correct
        self.assertEqual(chart_config['title']['text'], 'Test Pie Chart')
        self.assertEqual(len(chart_config['series'][0]['data']), 5)  # 5 data points

    def test_generate_stacked_barchart_comparison(self):
        # Call the function with our test DataFrame
        chart_config = generate_stacked_barchart_comparison(
            self.test_df, 'Category', 'Value1', 'Value2', 'Test Stacked Bar Chart'
        )

        # Check that the chart config contains the expected keys
        self.assertIn('title', chart_config)
        self.assertIn('xAxis', chart_config)
        self.assertIn('yAxis', chart_config)
        self.assertIn('series', chart_config)

        # Check that the chart data is correct
        self.assertEqual(chart_config['title']['text'], 'Test Stacked Bar Chart')
        self.assertEqual(len(chart_config['xAxis']['data']), 5)  # 5 categories

    def test_find_columns(self):
        """Test the _find_columns helper function."""
        # Test with matching column names
        cat_col, num_col = _find_columns(
            self.test_df,
            categorical_hints=['category', 'type', 'name'],
            numerical_hints=['value', 'amount', 'total']
        )

        # Check that it found the right columns
        self.assertEqual(cat_col, 'Category')
        self.assertEqual(num_col, 'Value1')

        # Test with non-matching column names
        cat_col, num_col = _find_columns(
            self.test_df,
            categorical_hints=['region', 'province', 'city'],
            numerical_hints=['price', 'cost', 'revenue']
        )

        # Check that it falls back to the first categorical and numerical columns
        self.assertEqual(cat_col, 'Category')  # First categorical column
        self.assertEqual(num_col, 'Value1')    # First numerical column

        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        cat_col, num_col = _find_columns(
            empty_df,
            categorical_hints=['category'],
            numerical_hints=['value']
        )

        # Check that it returns None for both columns
        self.assertIsNone(cat_col)
        self.assertIsNone(num_col)

    def test_generate_barchart_by_category_invalid_columns(self):
        """Test generating a bar chart with invalid columns."""
        # Call the function with invalid columns
        chart_config = generate_barchart_by_category(
            self.test_df, 'NonExistentCategory', 'NonExistentValue', 'Test Bar Chart'
        )

        # Check that the chart config contains the expected keys
        self.assertIn('title', chart_config)
        self.assertIn('xAxis', chart_config)
        self.assertIn('yAxis', chart_config)
        self.assertIn('series', chart_config)

        # Check that the chart data is empty
        self.assertEqual(len(chart_config['xAxis']['data']), 0)
        self.assertEqual(len(chart_config['series'][0]['data']), 0)

        # Check that the title indicates data is not available
        self.assertIn('Data not available', chart_config['title']['text'])

    def test_generate_piechart_by_category_invalid_columns(self):
        """Test generating a pie chart with invalid columns."""
        # Call the function with invalid columns
        chart_config = generate_piechart_by_category(
            self.test_df, 'NonExistentCategory', 'NonExistentValue', 'Test Pie Chart'
        )

        # Check that the chart config contains the expected keys
        self.assertIn('title', chart_config)
        self.assertIn('series', chart_config)

        # Check that the chart data is empty
        self.assertEqual(len(chart_config['series'][0]['data']), 0)

        # Check that the title indicates data is not available
        self.assertIn('Data not available', chart_config['title']['text'])

    def test_generate_stacked_barchart_comparison_invalid_columns(self):
        """Test generating a stacked bar chart with invalid columns."""
        # Call the function with invalid columns
        chart_config = generate_stacked_barchart_comparison(
            self.test_df, 'NonExistentCategory', 'NonExistentValue1', 'NonExistentValue2', 'Test Stacked Bar Chart'
        )

        # Check that the chart config contains the expected keys
        self.assertIn('title', chart_config)
        self.assertIn('xAxis', chart_config)
        self.assertIn('yAxis', chart_config)
        self.assertIn('series', chart_config)

        # Check that the chart data is empty
        self.assertEqual(len(chart_config['xAxis']['data']), 0)
        self.assertEqual(len(chart_config['series']), 0)

        # Check that the title indicates data is not available
        self.assertIn('Data not available', chart_config['title']['text'])

    @patch('src.data_exploration_service.load_dataset')
    def test_get_dataset_visualizations(self, mock_load_dataset):
        """Test the get_dataset_visualizations function."""
        # Mock the load_dataset function to return our test DataFrame
        mock_load_dataset.return_value = (self.test_df, "Successfully loaded test dataset")

        # Call the function
        result = get_dataset_visualizations('test.csv')

        # Check that the function was called with the right parameters
        mock_load_dataset.assert_called_once_with('test.csv')

        # Check that the result contains the expected keys
        self.assertIn('load_message', result)
        self.assertIn('summary', result)
        self.assertIn('visualizations', result)

        # Check that the visualizations contain the expected charts
        self.assertIn('chart1_bar', result['visualizations'])
        self.assertIn('chart2_pie', result['visualizations'])
        self.assertIn('chart3_stacked_bar', result['visualizations'])

        # Check that the summary contains the expected information
        self.assertEqual(result['summary']['num_rows'], 5)
        self.assertEqual(result['summary']['num_cols'], 3)

    @patch('src.data_exploration_service.load_dataset')
    def test_get_dataset_visualizations_empty_dataset(self, mock_load_dataset):
        """Test the get_dataset_visualizations function with an empty dataset."""
        # Mock the load_dataset function to return an empty DataFrame
        mock_load_dataset.return_value = (pd.DataFrame(), "Failed to load dataset")

        # Call the function
        result = get_dataset_visualizations('test.csv')

        # Check that the function was called with the right parameters
        mock_load_dataset.assert_called_once_with('test.csv')

        # Check that the result contains the expected keys
        self.assertIn('load_message', result)
        self.assertIn('summary', result)
        self.assertIn('visualizations', result)

        # Check that the visualizations contain the expected charts
        self.assertIn('chart1_bar', result['visualizations'])
        self.assertIn('chart2_pie', result['visualizations'])
        self.assertIn('chart3_stacked_bar', result['visualizations'])

        # Check that the charts indicate data is not available
        self.assertIn('Data not available', result['visualizations']['chart1_bar']['title']['text'])
        self.assertIn('Data not available', result['visualizations']['chart2_pie']['title']['text'])
        self.assertIn('Data not available', result['visualizations']['chart3_stacked_bar']['title']['text'])

if __name__ == '__main__':
    unittest.main()
