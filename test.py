# from multiprocessing import Pool, Manager
# import os, time, random
# from func1 import gurobi

# def long_time_task(name,n):
#     print('Run task %s (%s)...' % (name, os.getpid()))
#     start = time.time()
#     time.sleep(random.random() * 3)
#     n.value += 1
#     end = time.time()
#     print('Task %s runs %0.2f seconds.' % (name, (end - start)))

# if __name__=='__main__':
#     print('Parent process %s.' % os.getpid())
#     p = Pool(4)
#     manager = Manager()
#     # array = manager.Array('i', [1,2])
#     num = manager.Value('i', 0)
#     for i in range(1):
#         p.apply_async(long_time_task, (1, num,))
#     print('Waiting for all subprocesses done...')
#     p.close()
#     p.join()
#     print('All subprocesses done.')
#     # print(array)
#     print(num.value)

# import os

# os.system("python3 nodeOptimizer.py")

# from multiprocessing import Process, Value, Array

# def f(n, a):
#     n.value = 3.1415927
#     for i in range(len(a)):
#         a[i] = -a[i]

# if __name__ == '__main__':
#     num = Value('d', 0.0)
#     arr = Array('i', range(10))

#     p = Process(target=f, args=(num, arr))
#     p.start()
#     p.join()

#     print(num.value)
#     print(arr[:])

import numpy as np
import random

a = [1, 2]
b = a
b[0] = 100
print(a[0])