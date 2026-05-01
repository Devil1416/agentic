import pandas as pd
from colorama import Fore, Style

class Analyzer:
    def __init__(self):
        self.data = None

    def load_csv(self, filepath):
        self.data = pd.read_csv(filepath)

    def load_json(self, filepath):
        self.data = pd.read_json(filepath)

    def calculate_metrics(self):
        if self.data is None:
            print("No data loaded.")
            return
        
        total_events = len(self.data)
        unique_users = len(self.data['user_id'].unique())
        top_actions = self.data['action'].value_counts().idxmax()

        print(f"Total events: {Fore.GREEN}{total_events}{Style.RESET_ALL}")
        print(f"Unique users: {Fore.CYAN}{unique_users}{Style.RESET_ALL}")
        print(f"Top action:   {Fore.MAGENTA}{top_actions}{Style.RESET_ALL}")