import pandas as pd
import numpy as np
import pytest

def test_dataframe_creation():
    # Test creating a DataFrame from a dictionary
    data = {'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['New York', 'London', 'Paris']}
    df = pd.DataFrame(data)
    
    assert df.shape == (3, 3)
    
    assert list(df.columns) == ['name', 'age', 'city']
    
    assert df['name'].dtype == object
    assert df['age'].dtype == int
    assert df['city'].dtype == object

def test_dataframe_indexing():
    # Create a sample DataFrame
    data = {'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': [7, 8, 9]}
    df = pd.DataFrame(data)
    
    assert df['A'].tolist() == [1, 2, 3]
    assert df['B'].tolist() == [4, 5, 6]
    assert df['C'].tolist() == [7, 8, 9]
    
    assert df.iloc[0].tolist() == [1, 4, 7]
    assert df.iloc[1].tolist() == [2, 5, 8]
    assert df.iloc[2].tolist() == [3, 6, 9]

def test_dataframe_merge():
    # Create two sample DataFrames
    df1 = pd.DataFrame({'key': ['A', 'B', 'C', 'D'],
                        'value1': [1, 2, 3, 4]})
    df2 = pd.DataFrame({'key': ['B', 'D', 'E', 'F'],
                        'value2': [5, 6, 7, 8]})
    
    merged_df = pd.merge(df1, df2, on='key')
    
    assert merged_df.shape == (2, 3)
    
    assert merged_df['key'].tolist() == ['B', 'D']
    assert merged_df['value1'].tolist() == [2, 4]
    assert merged_df['value2'].tolist() == [5, 6]

def test_dataframe_groupby():
    # Create a sample DataFrame
    data = {'category': ['A', 'B', 'A', 'B', 'A'],
            'value': [1, 2, 3, 4, 5]}
    df = pd.DataFrame(data)

    grouped_df = df.groupby('category').sum()

    assert grouped_df.shape == (2, 1)
    
    assert grouped_df.loc['A', 'value'] == 9
    assert grouped_df.loc['B', 'value'] == 6