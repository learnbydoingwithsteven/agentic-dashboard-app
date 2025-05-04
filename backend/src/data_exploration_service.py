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
    Load a dataset from a file with flexible format detection.

    Args:
        file_path: Path to the dataset file

    Returns:
        Tuple containing the loaded DataFrame and a message about the loading process
    """
    message = ""
    df = None

    # Try different encodings and delimiters for CSV
    for encoding in ['latin-1', 'utf-8', 'cp1252']:
        for delimiter in [';', ',', '\t']:
            try:
                df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
                message = f"Successfully loaded CSV with encoding={encoding}, delimiter={delimiter}"
                break
            except Exception:
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
                message = "Successfully loaded Excel file"
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
        numeric_stats[col] = {
            "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
            "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
            "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
            "median": float(df[col].median()) if not pd.isna(df[col].median()) else None,
            "std": float(df[col].std()) if not pd.isna(df[col].std()) else None,
            "missing": int(df[col].isna().sum())
        }

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
    sample_data = df.head(5).to_dict(orient='records')

    return {
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

def generate_province_commitments_chart(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate an ECharts configuration for province commitments visualization.

    Args:
        df: The DataFrame containing the data

    Returns:
        ECharts configuration object
    """
    if 'Provincia competente' not in df.columns or 'Impegno totale' not in df.columns:
        return {
            "title": {"text": "Province Commitments (Data not available)"},
            "tooltip": {},
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [{"data": [], "type": "bar"}]
        }

    # Group by province and calculate total commitments
    province_totals = df.groupby('Provincia competente')['Impegno totale'].sum().reset_index()
    province_totals = province_totals.sort_values('Impegno totale', ascending=False)

    # Limit to top 10 provinces
    top_provinces = province_totals.head(10)

    # Fill NaN values before converting to list
    province_data = top_provinces['Impegno totale'].fillna(0).tolist()
    province_labels = top_provinces['Provincia competente'].fillna('N/A').tolist()

    # Format numbers for display (using original data before fillna for formatting if needed, but not strictly necessary here)
    # formatted_values = [f"{x:,.2f}" for x in top_provinces['Impegno totale'].tolist()] # Example if formatting needed original values

    return {
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
            "data": province_labels, # Use sanitized labels
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
            "data": province_data, # Use sanitized data
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

def generate_expense_type_chart(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate an ECharts configuration for expense type visualization.

    Args:
        df: The DataFrame containing the data

    Returns:
        ECharts configuration object
    """
    if 'Tipologia di spesa' not in df.columns and 'Descrizione Intervento' not in df.columns:
        # Try with alternative column
        expense_col = 'Descrizione Intervento' if 'Descrizione Intervento' in df.columns else None
        if expense_col is None:
            return {
                "title": {"text": "Expense Types (Data not available)"},
                "tooltip": {},
                "series": [{"data": [], "type": "pie"}]
            }
    else:
        expense_col = 'Tipologia di spesa' if 'Tipologia di spesa' in df.columns else 'Descrizione Intervento'

    if 'Impegno totale' not in df.columns:
        return {
            "title": {"text": "Expense Types (Data not available)"},
            "tooltip": {},
            "series": [{"data": [], "type": "pie"}]
        }

    # Group by expense type and calculate total
    expense_totals = df.groupby(expense_col)['Impegno totale'].sum().reset_index()
    expense_totals = expense_totals.sort_values('Impegno totale', ascending=False)

    # Limit to top 8 categories for better visualization
    if len(expense_totals) > 8:
        other_total = expense_totals.iloc[8:]['Impegno totale'].sum()
        top_expenses = expense_totals.iloc[:8].copy()
        top_expenses.loc[len(top_expenses)] = {'Tipologia di spesa' if 'Tipologia di spesa' in df.columns else 'Descrizione Intervento': 'Altre tipologie', 'Impegno totale': other_total}
        expense_totals = top_expenses

    return {
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
            # Fill NaN before creating the data list
            "data": [
                {"value": float(row['Impegno totale'] if pd.notna(row['Impegno totale']) else 0),
                 "name": str(row[expense_col] if pd.notna(row[expense_col]) else 'N/A')}
                for _, row in expense_totals.iterrows()
            ]
        }]
    }

def generate_payment_comparison_chart(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate an ECharts configuration for payment comparison visualization.

    Args:
        df: The DataFrame containing the data

    Returns:
        ECharts configuration object
    """
    if not all(col in df.columns for col in ['Provincia competente', 'Impegno totale', 'Pagamenti in CC', 'Pagamenti in CR']):
        return {
            "title": {"text": "Payment Comparison (Data not available)"},
            "tooltip": {},
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [{"data": [], "type": "bar"}]
        }

    # Group by province and calculate totals
    compare_df = df.groupby('Provincia competente').agg({
        'Impegno totale': 'sum',
        'Pagamenti in CC': 'sum',
        'Pagamenti in CR': 'sum'
    }).reset_index()

    # Calculate total payments
    compare_df['Pagato totale'] = compare_df['Pagamenti in CC'] + compare_df['Pagamenti in CR']

    # Sort by total commitment
    compare_df = compare_df.sort_values('Impegno totale', ascending=False)

    # Calculate payment ratio
    compare_df['Ratio'] = compare_df['Pagato totale'] / compare_df['Impegno totale'] * 100

    # Limit to top 10 provinces for better visualization
    if len(compare_df) > 10:
        compare_df = compare_df.iloc[:10]

    return {
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
            "data": compare_df['Provincia competente'].fillna('N/A').tolist(), # Sanitize labels
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
                "data": compare_df['Impegno totale'].fillna(0).tolist(), # Sanitize data
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
                "data": compare_df['Pagato totale'].fillna(0).tolist(), # Sanitize data
                "itemStyle": {
                    "color": "#91cc75"
                }
            }
        ]
    }

def get_dataset_visualizations(file_path: str) -> Dict[str, Any]:
    """
    Generate a set of ECharts visualizations for a dataset.

    Args:
        file_path: Path to the dataset file

    Returns:
        Dictionary containing ECharts configurations
    """
    # Load the dataset
    df, load_message = load_dataset(file_path)

    # Generate summary
    summary = get_dataset_summary(df)

    # Generate visualizations
    visualizations = {
        "province_commitments": generate_province_commitments_chart(df),
        "expense_types": generate_expense_type_chart(df),
        "payment_comparison": generate_payment_comparison_chart(df)
    }

    return {
        "load_message": load_message,
        "summary": summary,
        "visualizations": visualizations
    }
