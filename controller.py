#!/usr/bin/python
# -*- coding: utf-8 -*-

# 目前假设 10个node 合作运行，使用一个matrix表示每个node上的可用资源情况
# 此文件是controller，负责收集每次各node的optimization计算结果；
# 然后进行资源分配的动态调整：orchestration

#几个假设：
# 1. 假设 computing cost和link cost 不随时间改变
# 2. 假设 每个node的computing capacity都相等，均为50


import numpy as np
import random

# neighbor relation
# 需要有一个数据结构来记录node间的依赖关系，注意：A和 B,C 是邻居，不能说明 B和C 是邻居； A==>B, 也不意味着 B==>A, 即 A会使用B的资源，B不一定会使用A的资源。
# 一个matrix：【】N x N的矩阵，每个元素X_ij 表示 node i 是否可使用 node j 的资源？ 1==> Yes, 0==> No
ALL_NODE = 10
CAPACITY = 50

# 设置依赖关系
relMatrix = np.identity(ALL_NODE, dtype = np.int16)
relMatrix[0][1] = 1
relMatrix[0][3] = 1 
relMatrix[0][4] = 1
relMatrix[1][4] = 1
relMatrix[1][5] = 1    
relMatrix[2][5] = 1
relMatrix[2][6] = 1 
relMatrix[3][0] = 1
relMatrix[3][5] = 1
relMatrix[4][0] = 1
relMatrix[4][7] = 1
relMatrix[4][8] = 1
relMatrix[5][1] = 1
relMatrix[5][2] = 1
relMatrix[5][6] = 1
relMatrix[6][2] = 1
relMatrix[6][9] = 1
relMatrix[7][3] = 1
relMatrix[7][4] = 1
relMatrix[7][8] = 1
relMatrix[8][5] = 1
relMatrix[8][7] = 1
relMatrix[8][9] = 1
relMatrix[9][8] = 1
relMatrix[9][6] = 1

#设置初始资源分配
initCapacity = np.zeros((ALL_NODE, ALL_NODE), dtype = np.int16)
for i in range(ALL_NODE):
	for j in range(ALL_NODE):
		if(i!=j and relMatrix[i][j]==1):
			initCapacity[i][j] = 5

for i in range(ALL_NODE):
	temp = 0
	for j in range(ALL_NODE):
		temp += initCapacity[j][i]
	for j in range(ALL_NODE):
		if(i==j):
			initCapacity[i][j] = CAPACITY - temp

# print(relMatrix)
# print(initCapacity)

# *************************************************************
# 启动10个子进程 模拟各自优化过程； controller等待子进程传回结果，尝试采用shared memory和message queue
# controller传给子进程的参数：
#（1）该node可使用的资源分配
#（2）此时的computer cost和link cost
#（3）该node在此timeslot会有多少request需要处理
#（4）一共有几个nodes可用
# 

