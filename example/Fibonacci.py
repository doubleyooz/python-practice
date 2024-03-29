def fibonacci(n):
    fib_series = [0, 1]
    while fib_series[len(fib_series) - 1] <= n:
        fib_series.append(fib_series[-1] + fib_series[-2])
    return fib_series

def is_fibonacci(n):
    fib_series = [0, 1]
    if n in fib_series:
        return True
    fib_series.append(fib_series[-1] + fib_series[-2])
    while fib_series[len(fib_series) - 1] <= n:
        if n in fib_series:
            return True
        else:
            fib_series.append(fib_series[-1] + fib_series[-2])
    return False

num = 130
print(f'is {num} in fibonacci')
print(fibonacci(num))
print(is_fibonacci(num))
