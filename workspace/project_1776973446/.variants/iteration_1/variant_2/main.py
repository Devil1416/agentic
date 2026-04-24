#!/usr/bin/env python
import os
from parser import Parser
from analyzer import Analyzer

def main():
    log_file = os.getcwd() + '/logs.txt'
    with open(log_file, 'r') as file:
        lines = file.readlines()
    parser = Parser()
    analyzer = Analyzer()
    parsed_data = [parser.parse(line) for line in lines]
    analyzer.load(parsed_data)
    print(analyzer.summary())

if __name__ == '__main__':
    main()