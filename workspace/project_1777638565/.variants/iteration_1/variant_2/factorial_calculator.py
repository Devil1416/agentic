def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

while True:
    try:
        num = int(input("Enter a non-negative integer to calculate its factorial (or 'q' to quit): "))
        if num < 0:
            raise ValueError()
        print(f"The factorial of {num} is {factorial(num)}")
    except ValueError:
        print("Invalid input. Please enter a non-negative integer.")