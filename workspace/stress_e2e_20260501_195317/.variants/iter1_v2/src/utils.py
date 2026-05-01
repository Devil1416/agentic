from colorama import Fore, Style
import pandas as pd

def print_error(message):
    print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")

def load_data(filepath):
    try:
        if filepath.endswith('.csv'):
            return pd.read_csv(filepath)
        elif filepath.endswith('.json'):
            return pd.read_json(filepath, orient='records')
        else:
            print_error("Unsupported file format. Only CSV and JSON files are supported.")
    except FileNotFoundError:
        print_error(f"File not found at path {filepath}")
    except pd.errors.ParserError as e:
        print_error(str(e))