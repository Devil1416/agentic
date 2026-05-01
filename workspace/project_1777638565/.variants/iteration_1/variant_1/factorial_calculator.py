def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def main():
    while True:
        try:
            num = int(input('Enter a non-negative integer (or "q" to quit): '))
            if num < 0:
                raise ValueError()
            print("The factorial of", num, "is", factorial(num))
        except ValueError:
            print("Invalid input. Please enter a non-negative integer.")
            
if __name__ == "__main__":
    main()