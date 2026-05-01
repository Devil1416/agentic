import argparse
from src.analyzer import Analyzer
from src.utils import Utils
from colorama import Fore, Style

def main():
    parser = argparse.ArgumentParser(description='Analyze event logs for operational metrics')
    parser.add_argument('filepath', type=str, help='Path to the CSV or JSON file containing the events')
    args = parser.parse_args()
    
    # Load data
    try:
        analyzer = Analyzer(args.filepath)
    except Exception as e:
        print(Fore.RED + "Error loading data:" + Style.RESET_ALL, str(e))
        return
    
    # Calculate metrics
    total_events = analyzer.total_events()
    unique_users = analyzer.unique_users()
    top_actions = analyzer.top_n_actions(5)  # Top 5 actions by default
    
    # Print report
    print("\n--- EVENT ANALYSIS REPORT ---")
    print("Total events:", total_events)
    print("Unique users:", unique_users)
    print("\nTop 5 actions:")
    for action, count in top_actions.items():
        print(f"{action}: {count}")
    
    # Cleanup colorama styles
    print(Style.RESET_ALL)

if __name__ == "__main__":
    main()