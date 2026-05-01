from colorama import Fore, Style
import pandas as pd

def print_error(message):
    print(f"{Fore.RED}{Style.BRIGHT}Error: {message}{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}{Style.BRIGHT}Success: {message}{Style.RESET_ALL}")

def load_dataframe(filepath, filetype='csv'):
    try:
        if filetype == 'csv':
            df = pd.read_csv(filepath)
        elif filetype == 'json':
            df = pd.read_json(filepath)
        else:
            raise ValueError("Invalid file type. Only CSV and JSON are supported.")
    except Exception as e:
        print_error(f"Failed to load data from {filepath}. Reason: {str(e)}")
        return None
    
    if df is not None:
        print_success(f"Successfully loaded data from {filepath}.")
    return df