"""
Data Exploration Service for Agentic Dashboard App.

This module provides functions for exploring datasets and generating ECharts visualizations.
"""

import os
import pandas as pd
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

def load_dataset(file_path: str) -> Tuple[pd.DataFrame, str]:
    """
    Load a dataset from a file with enhanced flexible format detection.

    Args:
        file_path: Path to the dataset file

    Returns:
        Tuple containing the loaded DataFrame and a message about the loading process
    """
    message = ""
    df = None
    error_messages = []

    # First try to determine file type from extension
    file_extension = os.path.splitext(file_path)[1].lower()

    # Try Excel formats first if extension suggests it
    if file_extension in ['.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt']:
        try:
            df = pd.read_excel(file_path)
            message = f"Successfully loaded Excel file based on extension {file_extension}"
        except Exception as e:
            error_messages.append(f"Failed to load Excel file: {str(e)}")

    # Try JSON if extension suggests it
    elif file_extension in ['.json']:
        try:
            df = pd.read_json(file_path)
            message = "Successfully loaded JSON file"
        except Exception as e:
            error_messages.append(f"Failed to load JSON file: {str(e)}")

    # Try Parquet if extension suggests it
    elif file_extension in ['.parquet']:
        try:
            df = pd.read_parquet(file_path)
            message = "Successfully loaded Parquet file"
        except Exception as e:
            error_messages.append(f"Failed to load Parquet file: {str(e)}")

    # Try Feather if extension suggests it
    elif file_extension in ['.feather']:
        try:
            df = pd.read_feather(file_path)
            message = "Successfully loaded Feather file"
        except Exception as e:
            error_messages.append(f"Failed to load Feather file: {str(e)}")

    # Try HDF5 if extension suggests it
    elif file_extension in ['.h5', '.hdf5']:
        try:
            df = pd.read_hdf(file_path)
            message = "Successfully loaded HDF5 file"
        except Exception as e:
            error_messages.append(f"Failed to load HDF5 file: {str(e)}")

    # Try CSV with different encodings and delimiters if still not loaded or for CSV-like extensions
    if df is None:
        for encoding in ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']:
            for delimiter in [';', ',', '\t', '|']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
                    message = f"Successfully loaded CSV with encoding={encoding}, delimiter={delimiter}"
                    break
                except Exception as e:
                    error_messages.append(f"Failed with encoding={encoding}, delimiter={delimiter}: {str(e)}")
                    continue
            if df is not None:
                break

    # If all attempts failed, try with pandas defaults
    if df is None:
        try:
            df = pd.read_csv(file_path)
            message = "Successfully loaded CSV with pandas defaults"
        except Exception:
            try:
                df = pd.read_excel(file_path)
                message = "Successfully loaded Excel file as last resort"
            except Exception as e:
                message = f"Failed to load dataset: {str(e)}"
                # Create a minimal dataset for testing
                df = pd.DataFrame({
                    'Column1': [1, 2, 3, 4, 5],
                    'Column2': ['A', 'B', 'C', 'D', 'E']
                })

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
                message += f"\nConverted column '{col}' to numeric type"
        except:
            # Skip columns that cause errors
            continue

    return df, message

def get_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a summary of the dataset.

    Args:
        df: The DataFrame to summarize

    Returns:
        Dictionary containing summary information
    """
    # Basic info
    num_rows, num_cols = df.shape

    # Column types
    column_types = {}
    numeric_columns = []
    categorical_columns = []
    date_columns = []

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            column_types[col] = "numeric"
            numeric_columns.append(col)
        elif pd.api.types.is_datetime64_dtype(df[col]):
            column_types[col] = "datetime"
            date_columns.append(col)
        else:
            column_types[col] = "categorical"
            categorical_columns.append(col)

    # Summary statistics for numeric columns
    numeric_stats = {}
    for col in numeric_columns:
        # Ensure NaN values from pandas aggregations are converted to None
        stats_dict = {
            "min": df[col].min(),
            "max": df[col].max(),
            "mean": df[col].mean(),
            "median": df[col].median(),
            "std": df[col].std(),
        }
        # Convert values to float if not NaN, otherwise None
        numeric_stats[col] = {
            key: float(value) if pd.notna(value) and np.isfinite(value) else None
            for key, value in stats_dict.items()
        }
        # Add missing count separately
        numeric_stats[col]["missing"] = int(df[col].isna().sum())

    # Value counts for categorical columns (limited to top 10)
    categorical_stats = {}
    for col in categorical_columns:
        value_counts = df[col].value_counts().head(10).to_dict()
        categorical_stats[col] = {
            "unique_values": int(df[col].nunique()),
            "top_values": {str(k): int(v) for k, v in value_counts.items()},
            "missing": int(df[col].isna().sum())
        }

    # Sample data (first 5 rows)
    # Convert potential NaN/NaT in sample data to None for JSON
    sample_data = df.head(5).replace({np.nan: None}).to_dict(orient='records')

    # Ensure the final summary dictionary is JSON serializable (replace any remaining NaN)
    summary_dict = {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "columns": list(df.columns),
        "column_types": column_types,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "date_columns": date_columns,
        "numeric_stats": numeric_stats,
        "categorical_stats": categorical_stats,
        "sample_data": sample_data
    }
    # Although the above steps should handle most NaNs, a final check/conversion might be needed
    # depending on how Flask serializes. For now, assume the explicit conversions are sufficient.
    return summary_dict

def _find_columns(df: pd.DataFrame, categorical_hints: List[str], numerical_hints: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """Helper to find the best categorical and numerical columns based on hints."""
    categorical_col = None
    numerical_col = None

    # Find categorical column
    for hint in categorical_hints:
        for col in df.columns:
            if hint in col.lower() and pd.api.types.is_object_dtype(df[col]):
                categorical_col = col
                break
        if categorical_col:
            break
    # Fallback: Find first object/category column with reasonable unique values
    if not categorical_col:
        for col in df.select_dtypes(include=['object', 'category']).columns:
            if 1 < df[col].nunique() < 50: # Avoid IDs or overly diverse columns
                 categorical_col = col
                 break

    # Find numerical column
    for hint in numerical_hints:
        for col in df.columns:
            if hint in col.lower() and pd.api.types.is_numeric_dtype(df[col]):
                numerical_col = col
                break
        if numerical_col:
            break
    # Fallback: Find first numeric column
    if not numerical_col:
        numeric_cols = df.select_dtypes(include=np.number).columns
        if len(numeric_cols) > 0:
            numerical_col = numeric_cols[0]

    return categorical_col, numerical_col

def generate_barchart_by_category(df: pd.DataFrame, category_col: Optional[str], value_col: Optional[str], chart_title: str) -> Dict[str, Any]:
    """
    Generate a generic ECharts bar chart configuration grouping by a category.

    Args:
        df: The DataFrame containing the data.
        category_col: The name of the categorical column to group by.
        value_col: The name of the numerical column to aggregate.
        chart_title: The title for the chart.

    Returns:
        ECharts configuration object or an error message config.
    """
    if not category_col or not value_col or category_col not in df.columns or value_col not in df.columns:
        return {
            "title": {"text": f"{chart_title} (Data not available)"},
            "tooltip": {},
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [{"data": [], "type": "bar"}]
        }

    # Group by category and calculate total value
    grouped_data = df.groupby(category_col)[value_col].sum().reset_index()
    grouped_data = grouped_data.sort_values(value_col, ascending=False)

    # Limit to top 10-15 categories for readability
    top_data = grouped_data.head(15)

    # Fill NaN values before converting to list
    chart_data = top_data[value_col].fillna(0).tolist()
    chart_labels = top_data[category_col].fillna('N/A').tolist()

    return {
        "title": {
            "text": chart_title,
            "left": "center",
            "textStyle": {
                "fontSize": 16,
                "fontWeight": "bold"
            }
        },
        "tooltip": {
            "trigger": "axis",
            "formatter": "{b}: {c:,.0f}" # Generic formatter
        },
        "grid": {
            "left": "5%",
            "right": "5%",
            "bottom": "15%", # Adjust bottom margin for rotated labels
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": chart_labels, # Use dynamic labels
            "axisLabel": {
                "rotate": 45,
                "fontSize": 10,
                "interval": 0 # Show all labels
            }
        },
        "yAxis": {
            "type": "value",
            "name": value_col, # Use dynamic axis name
            "axisLabel": {
                "formatter": "{value:,.0f}" # Generic formatter
            }
        },
        "series": [{
            "name": value_col, # Use dynamic series name
            "type": "bar",
            "data": chart_data, # Use dynamic data
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
    }

def generate_piechart_by_category(df: pd.DataFrame, category_col: Optional[str], value_col: Optional[str], chart_title: str) -> Dict[str, Any]:
    """
    Generate a generic ECharts pie chart configuration grouping by a category.

    Args:
        df: The DataFrame containing the data.
        category_col: The name of the categorical column for slices.
        value_col: The name of the numerical column for slice values.
        chart_title: The title for the chart.

    Returns:
        ECharts configuration object or an error message config.
    """
    if not category_col or not value_col or category_col not in df.columns or value_col not in df.columns:
        return {
            "title": {"text": f"{chart_title} (Data not available)"},
            "tooltip": {},
            "series": [{"data": [], "type": "pie"}]
        }

    # Group by category and calculate total value
    grouped_data = df.groupby(category_col)[value_col].sum().reset_index()
    grouped_data = grouped_data.sort_values(value_col, ascending=False)

    # Limit categories for better visualization (e.g., top 8 + 'Other')
    if len(grouped_data) > 8:
        other_total = grouped_data.iloc[8:][value_col].sum()
        top_data = grouped_data.iloc[:8].copy()
        # Use .loc to add the 'Other' row safely
        top_data.loc[len(top_data)] = {category_col: 'Other Categories', value_col: other_total}
        grouped_data = top_data

    # Prepare data for ECharts, handling potential NaN values
    pie_data = [
        {"value": float(row[value_col]) if pd.notna(row[value_col]) else 0,
         "name": str(row[category_col]) if pd.notna(row[category_col]) else 'N/A'}
        for _, row in grouped_data.iterrows()
    ]

    return {
        "title": {
            "text": chart_title,
            "left": "center",
            "textStyle": {
                "fontSize": 16,
                "fontWeight": "bold"
            }
        },
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c:,.0f} ({d}%)" # Generic formatter
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
            "name": category_col, # Use dynamic series name
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
            "data": pie_data # Use dynamic data
        }]
    }

def generate_stacked_barchart_comparison(df: pd.DataFrame, category_col: Optional[str], value_col1: Optional[str], value_col2: Optional[str], chart_title: str) -> Dict[str, Any]:
    """
    Generate a generic ECharts stacked bar chart comparing two values by category.

    Args:
        df: The DataFrame containing the data.
        category_col: The name of the categorical column to group by.
        value_col1: The name of the first numerical column.
        value_col2: The name of the second numerical column.
        chart_title: The title for the chart.

    Returns:
        ECharts configuration object or an error message config.
    """
    if not category_col or not value_col1 or not value_col2 or \
       category_col not in df.columns or value_col1 not in df.columns or value_col2 not in df.columns:
        return {
            "title": {"text": f"{chart_title} (Data not available)"},
            "tooltip": {},
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [{"data": [], "type": "bar"}]
        }

    # Group by category and calculate totals
    compare_df = df.groupby(category_col).agg({
        value_col1: 'sum',
        value_col2: 'sum'
    }).reset_index()

    # Sort by the first value column
    compare_df = compare_df.sort_values(value_col1, ascending=False)

    # Limit to top 10-15 categories for readability
    if len(compare_df) > 15:
        compare_df = compare_df.iloc[:15]

    # Prepare data for ECharts, handling potential NaN values
    labels = compare_df[category_col].fillna('N/A').tolist()
    data1 = compare_df[value_col1].fillna(0).tolist()
    data2 = compare_df[value_col2].fillna(0).tolist()

    return {
        "title": {
            "text": chart_title,
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
            "formatter": "{b}<br/>{a0}: {c0:,.0f}<br/>{a1}: {c1:,.0f}" # Generic formatter
        },
        "legend": {
            "data": [value_col1, value_col2], # Use dynamic legend names
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
            "data": labels, # Use dynamic labels
            "axisLabel": {
                "rotate": 45,
                "fontSize": 10,
                "interval": 0 # Show all labels
            }
        },
        "yAxis": {
            "type": "value",
            "name": "Value", # Generic axis name
            "axisLabel": {
                "formatter": "{value:,.0f}" # Generic formatter
            }
        },
        "series": [
            {
                "name": value_col1, # Use dynamic series name
                "type": "bar",
                "stack": "total", # Keep stacking for comparison
                "emphasis": {
                    "focus": "series"
                },
                "data": data1, # Use dynamic data
                "itemStyle": {
                    "color": "#5470c6"
                }
            },
            # Removed extra closing brace and comma from the line above
            {
                "name": value_col2, # Use dynamic series name
                "type": "bar",
                "stack": "total", # Keep stacking for comparison
                "emphasis": {
                    "focus": "series"
                },
                "data": data2, # Use dynamic data
                "itemStyle": {
                    "color": "#91cc75"
                }
            }
        ]
    }

def get_dataset_visualizations(file_path: str) -> Dict[str, Any]:
    """
    Generate a set of ECharts visualizations for a dataset, attempting to
    dynamically identify relevant columns. Ensures result is JSON serializable.

    Args:
        file_path: Path to the dataset file

    Returns:
        Dictionary containing ECharts configurations and summary info.
    """
    # Load the dataset
    df, load_message = load_dataset(file_path)

    # Generate summary (already handles NaN conversion)
    summary = get_dataset_summary(df)
    numeric_cols = summary.get("numeric_columns", [])
    categorical_cols = summary.get("categorical_columns", [])

    # --- Dynamically identify columns for charts ---
    # (Column identification logic remains the same)
    cat1_col, val1_col = _find_columns(df, ['province', 'region', 'area', 'competente'], ['total', 'impegno', 'value', 'amount'])
    chart1_title = f"{val1_col} by {cat1_col}" if cat1_col and val1_col else "Category Breakdown"
    vis1 = generate_barchart_by_category(df, cat1_col, val1_col, chart1_title)

    cat2_col = None
    potential_cat2_cols = [c for c in categorical_cols if c != cat1_col]
    if potential_cat2_cols:
        for hint in ['type', 'desc', 'kind', 'intervento', 'tipologia']:
             for col in potential_cat2_cols:
                 if hint in col.lower():
                     cat2_col = col
                     break
             if cat2_col:
                 break
        if not cat2_col:
            cat2_col = potential_cat2_cols[0]
    val2_col = val1_col
    chart2_title = f"{val2_col} Distribution by {cat2_col}" if cat2_col and val2_col else "Value Distribution"
    vis2 = generate_piechart_by_category(df, cat2_col, val2_col, chart2_title)

    cat3_col = cat1_col
    val3_col1 = None
    val3_col2 = None
    payment_hints = ['payment', 'pagato', 'paid']
    commitment_hints = ['commitment', 'impegno', 'total']
    for hint in commitment_hints:
        for col in numeric_cols:
            if hint in col.lower():
                val3_col1 = col
                break
        if val3_col1:
            break
    if not val3_col1 and len(numeric_cols) > 0:
        val3_col1 = numeric_cols[0]
    for hint in payment_hints:
        for col in numeric_cols:
            if hint in col.lower() and col != val3_col1:
                val3_col2 = col
                break
        if val3_col2:
            break
    if not val3_col2 and len(numeric_cols) > 1:
        potential_val3_col2 = [c for c in numeric_cols if c != val3_col1]
        if potential_val3_col2:
            val3_col2 = potential_val3_col2[0]
    chart3_title = f"{val3_col1} vs {val3_col2} by {cat3_col}" if cat3_col and val3_col1 and val3_col2 else "Value Comparison"
    vis3 = generate_stacked_barchart_comparison(df, cat3_col, val3_col1, val3_col2, chart3_title)

    # Assemble visualizations
    visualizations = {
        "chart1_bar": vis1,
        "chart2_pie": vis2,
        "chart3_stacked_bar": vis3
    }

    # --- Ensure final result is JSON serializable ---
    final_result = {
        "load_message": load_message,
        "summary": summary, # Summary already handles NaN
        "visualizations": visualizations # Chart functions should handle NaN
    }

    # Recursively replace NaN with None in the final structure
    def replace_nan_with_none(obj):
        if isinstance(obj, dict):
            return {k: replace_nan_with_none(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_nan_with_none(elem) for elem in obj]
        # Check for both numpy NaN and standard float NaN
        elif isinstance(obj, float) and np.isnan(obj):
            return None
        # Handle potential pandas NaT (Not a Time) values if date columns exist
        elif pd.isna(obj) and not isinstance(obj, (str, bool, int)): # Avoid converting valid types
             return None
        return obj

    return replace_nan_with_none(final_result)
