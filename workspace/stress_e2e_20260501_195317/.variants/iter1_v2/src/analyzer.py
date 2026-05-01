import pandas as pd
from colorama import Fore, Style

class Analyzer:
    def __init__(self):
        self.data = None

    def load_csv(self, filepath):
        try:
            self.data = pd.read_csv(filepath)
            return True
        except Exception as e:
            print(f"{Fore.RED}Error loading CSV data: {e}{Style.RESET_ALL}")
            return False

    def load_json(self, filepath):
        try:
            self.data = pd.read_json(filepath)
            return True
        except Exception as e:
            print(f"{Fore.RED}Error loading JSON data: {e}{Style.RESET_ALL}")
            return False

    def calculate_metrics(self):
        if self.data is not None:
            total_events = len(self.data)
            unique_users = len(self.data['user_id'].unique())
            top_actions = self.data['action'].value_counts().idxmax()
            
            return {
                'total_events': total_events, 
                'unique_users': unique_users, 
                'top_actions': top_actions
            }
        else:
            print(f"{Fore.RED}No data to calculate metrics from. Load data first.{Style.RESET_ALL}")
            return None