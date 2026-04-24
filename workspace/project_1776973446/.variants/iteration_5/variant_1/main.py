#!/usr/bin/env python
import argparse
from utils import read_log_file, LogParseError
from parser import parse_log_line
from analyzer import analyze_stats

def main(args):
    log_data = read_log_file(args.log_path)
    parsed_logs = [parse_log_line(log) for log in log_data]
    stats = analyze_stats(parsed_logs)
    print(stats)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_path", required=True, help="Path to the log file")
    args = parser.parse_args()
    main(args)
