import random
import sys
print(sys.argv[1:])
nmax = int(sys.argv[1])

n = 0
cols = 19
while n < nmax:
    items = ['%.2f' % (n / 100.)]
    for c in range(cols):
        items.append('%.4f' % random.random())
    print('   '.join(items))
    n += 1