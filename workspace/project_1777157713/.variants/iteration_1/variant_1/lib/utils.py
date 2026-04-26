def fibonacci_iterative(n):
    if n <= 0:
        return "Input should be a positive integer."
    elif n == 1:
        return 0
    elif n == 2:
        return 1
    else:
        a, b = 0, 1
        for _ in range(n - 2):
            a, b = b, a + b
        return b

def fibonacci_recursive(n):
    if n <= 0:
        return "Input should be a positive integer."
    elif n == 1:
        return 0
    elif n == 2:<｜begin▁of▁sentence｜>:
        return 1
    else:
        return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)