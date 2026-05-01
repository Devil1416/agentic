import argparse
from src.analyzer import Analyzer
from src.utils import print_report

def main():
    parser = argparse.ArgumentParser(description='Analyze structured event logs (CSV and JSON) to derive key operational metrics like total events, unique users, and top actions.')
    parser.add_argument('filepath', type=str, help='The file path of the CSV or JSON log file.')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='The format of the event logs (default: csv).')
    
    args = parser.parse_args()
    
    analyzer = Analyzer(args.filepath, args.format)
    report = analyzer.generate_report()
    
    print_report(report)

if __name__ == "__main__":
    main()