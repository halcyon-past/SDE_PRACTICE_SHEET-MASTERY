def square(x):
    return x**2

def even(n):
    return n%2==0

l = list(range(1,51))
m = list(map(square,l))
n = list(filter(lambda z: even(z),m))
x = [s for s in n if s>500]
y = x[::-2]


print(l)
print(m)
print(n)
print(x)
print(y)