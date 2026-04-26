from lib.utils import fibonacci

def main():
    n = int(input("Enter a number to calculate its Fibonacci value: "))
    print(f"The {n}th Fibonacci number is {fibonacci(n)}")

if __name__ == '__main__':
    main()