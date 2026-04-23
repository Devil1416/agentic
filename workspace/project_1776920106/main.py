#!/usr/bin/env python3
import calculator as calc

def main():
    print("Welcome to the calculator app")
    num1 = float(input("Enter first number: "))
    num2 = float(input("Enter second number: "))
    operation = input("Enter operation (add, sub, mul, div): ")
    if operation == 'add':
        print('Result:', calc.add(num1, num2))
    elif operation == 'sub':
        print('Result:', calc.subtract(num1, num2))
    elif operation == 'mul':
        print('Result:', calc.multiply(num1, num2))
    elif operation == 'div':
        if num2 != 0:
            print('Result:', calc.divide(num1, num2))
        else:
            print("Error: Division by zero")

if __name__ == "__main__":
    main()