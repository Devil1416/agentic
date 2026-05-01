context line (unchanged)
line to add
def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        fact = 1
        for i in range(1, n + 1):
            fact *= i
        return fact
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