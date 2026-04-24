#!/usr/bin/env python3
import argparse
from utils import read_file, handle_error
from parser import parse_log
from analyzer import analyze

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Analyze log files.')
    parser.add_argument('filename', help='Log file to be analyzed.')
    args = parser.parse_args()

    try:
        data = read_file(args.filename)
        parsed_data = parse_log(data)
        report = analyze(parsed_data)
        print(report)
    except Exception as e:
        handle_error(e)

if __name__ == '__main__':
    main()