#!/usr/bin/env python
import os
print(os.listdir())
    print("Welcome to the calculator app")
    num1 = float(input("Enter first number: "))
    num2 = float(input("Enter second number: "))
    try:
        operation = input("Enter operation (add, sub, mul, div): ")
        if operation not in ['add', 'sub', 'mul', 'div']:
            raise ValueError('Invalid operation')
    except ValueError as e:
        print("Error: ", str(e))
    if operation == 'add':
        print('Result:', calc.add(num1, num2))
    elif operation == 'sub':
