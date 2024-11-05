Here is the equivalent Python code:
```
#!/usr/bin/python

def fibonacci(n):
    fib = [0, 1]
    for i in range(2, n+1):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# Get first 10 Fibonacci numbers
sequence = fibonacci(10)
print("Fibonacci sequence:", *sequence)
```
Note that in Python, we don't have to use `shift` to get the first argument of a function like we do in Perl. Instead, we can simply pass the number of elements we want as an argument to the function, like we did in the Python code above. Also, in Python, we can unpack a list directly into the argument list using the `*` operator, which is why we use `print("Fibonacci sequence:", *sequence)` instead of `print "Fibonacci sequence: @sequence"`.