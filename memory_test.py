import psutil
import os
import subprocess
import sys

import lasio
import mem


def memory():
    total, shared, private = mem.working_set_size()
    total = float(total)
    return total / (1000 * 1000)


def file_test(fn, m0):
    print('!\t%.3f\t\t' % (os.stat(fn).st_size / (1000 * 1000), ), end='')
    l = lasio.read(fn)
    print('%.3f' % (memory() - m0, ))
    return memory() - m0


def test(n):
    # m = psutil.virtual_memory()
    # m0 = m.used / (1000 * 1000)
    print('!\tLAS file (MB)\tUsed Mem. (MB)')
    dm = 0
    for i in range(n):
        m0 = memory()
        dm += file_test('5MB.las', m0)
    print('!\t\t\t-----------------')
    print('!\t\t\taverage=%.3f MB\n!' % (dm / n, ))
    # l2 = file_test('9MB.las', m0)
    # l3 = file_test('16MB.las', m0)
    # l4 = file_test('21MB.las', m0)
    # l5 = file_test('52MB.las', m0)
    # l6 = file_test('193MB.las', m0)


if __name__ == '__main__':
    d = os.getcwd()
    os.chdir(r'..\lasio')
    git_cmd = 'git show --name-status --oneline'
    out = subprocess.check_output(git_cmd).decode('ascii')
    print('!$ %s\n! %s\n!' % (git_cmd, out.split('\n')[0]))
    os.chdir(d)
    test(int(sys.argv[1]))

