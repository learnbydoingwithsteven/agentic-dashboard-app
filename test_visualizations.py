import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

def test_plotly_visualization():
    """Test creating a simple Plotly visualization"""
    # Create a sample DataFrame
    df = pd.DataFrame({
        'Category': ['A', 'B', 'C', 'D', 'E'],
        'Value': [10, 20, 30, 40, 50]
    })
    
    # Create a simple bar chart
    fig = px.bar(df, x='Category', y='Value', title='Test Bar Chart')
    
    # Convert to JSON to test serialization
    fig_json = fig.to_json()
    
    # Parse the JSON to verify it's valid
    fig_dict = json.loads(fig_json)
    
    # Check that the figure has the expected structure
    assert 'data' in fig_dict, "Figure JSON should have 'data' key"
    assert 'layout' in fig_dict, "Figure JSON should have 'layout' key"
    assert len(fig_dict['data']) == 1, "Figure should have 1 trace"
    assert fig_dict['data'][0]['type'] == 'bar', "Figure trace should be a bar chart"
    
    print("Plotly visualization test passed!")
    return fig_dict

def test_echarts_visualization():
    """Test creating a simple ECharts visualization config"""
    # Create a sample DataFrame
    df = pd.DataFrame({
        'Category': ['A', 'B', 'C', 'D', 'E'],
        'Value': [10, 20, 30, 40, 50]
    })
    
    # Create a simple ECharts config
    echarts_config = {
        'title': {'text': 'Test Bar Chart'},
        'tooltip': {},
        'xAxis': {
            'type': 'category',
            'data': df['Category'].tolist()
        },
        'yAxis': {'type': 'value'},
        'series': [{
            'data': df['Value'].tolist(),
            'type': 'bar'
        }]
    }
    
    # Convert to JSON to test serialization
    config_json = json.dumps(echarts_config)
    
    # Parse the JSON to verify it's valid
    config_dict = json.loads(config_json)
    
    # Check that the config has the expected structure
    assert 'title' in config_dict, "ECharts config should have 'title' key"
    assert 'xAxis' in config_dict, "ECharts config should have 'xAxis' key"
    assert 'yAxis' in config_dict, "ECharts config should have 'yAxis' key"
    assert 'series' in config_dict, "ECharts config should have 'series' key"
    assert len(config_dict['series']) == 1, "ECharts config should have 1 series"
    assert config_dict['series'][0]['type'] == 'bar', "ECharts series should be a bar chart"
    
    print("ECharts visualization test passed!")
    return config_dict

if __name__ == "__main__":
    print("Testing Plotly visualization...")
    plotly_fig = test_plotly_visualization()
    print(f"Plotly figure has {len(plotly_fig['data'])} traces")
    
    print("\nTesting ECharts visualization...")
    echarts_config = test_echarts_visualization()
    print(f"ECharts config has {len(echarts_config['series'])} series")
    
    print("\nAll visualization tests passed!")
