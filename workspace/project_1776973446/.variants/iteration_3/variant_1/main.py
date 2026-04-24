#!/usr/bin/env python
import argparse
from utils import read_file, handle_error
from parser import parse_log
from analyzer import analyze

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Log Analyzer.')
    parser.add_argument('-f', '--file', required=True, help='Path to log file.')
    args = parser.parse_args()

    # Read and parse the log file
    try:
        data = read_file(args.file)
        parsed_data = parse_log(data)
        report = analyze(parsed_data)
        print(report)
    except Exception as e:
        handle_error(e)

if __name__ == '__main__':
    main()