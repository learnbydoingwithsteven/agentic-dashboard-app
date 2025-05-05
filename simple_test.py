import json

# Create a simple Plotly-like figure
figure = {
    'data': [
        {
            'type': 'bar',
            'x': ['A', 'B', 'C', 'D', 'E'],
            'y': [10, 20, 30, 40, 50]
        }
    ],
    'layout': {
        'title': 'Test Bar Chart'
    }
}

# Create a simple ECharts-like config
echarts_config = {
    'title': {'text': 'Test Bar Chart'},
    'xAxis': {
        'type': 'category',
        'data': ['A', 'B', 'C', 'D', 'E']
    },
    'yAxis': {'type': 'value'},
    'series': [{
        'data': [10, 20, 30, 40, 50],
        'type': 'bar'
    }]
}

# Convert to JSON to test serialization
figure_json = json.dumps(figure)
echarts_json = json.dumps(echarts_config)

# Parse the JSON to verify it's valid
figure_dict = json.loads(figure_json)
echarts_dict = json.loads(echarts_json)

# Print the results
print("Plotly figure:")
print(f"- Has data: {'data' in figure_dict}")
print(f"- Has layout: {'layout' in figure_dict}")
print(f"- Number of traces: {len(figure_dict['data'])}")
print(f"- Trace type: {figure_dict['data'][0]['type']}")

print("\nECharts config:")
print(f"- Has title: {'title' in echarts_dict}")
print(f"- Has xAxis: {'xAxis' in echarts_dict}")
print(f"- Has yAxis: {'yAxis' in echarts_dict}")
print(f"- Has series: {'series' in echarts_dict}")
print(f"- Number of series: {len(echarts_dict['series'])}")
print(f"- Series type: {echarts_dict['series'][0]['type']}")

print("\nAll tests passed!")
