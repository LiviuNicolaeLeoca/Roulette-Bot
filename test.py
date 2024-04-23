import datetime


def fibonacci_sequence(length):
    fib = [1, 1]
    while len(fib) < length:
        fib.append(fib[-1] + fib[-2])
    return fib

fib_seq=fibonacci_sequence(7)

print(fib_seq)
print(sum(fib_seq)*0.5)
print(len(fib_seq))
fib_seq.pop(0)
fib_seq.pop(0)
print(fib_seq)
print(len(fib_seq))

print(datetime.datetime.now())