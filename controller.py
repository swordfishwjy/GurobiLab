#!/usr/bin/python
# -*- coding: utf-8 -*-

# 目前假设 10个node 合作运行，使用一个matrix表示每个node上的可用资源情况
# 此文件是controller，负责收集每次各node的optimization计算结果；
# 然后进行资源分配的动态调整：orchestration

#几个假设：
# 1. 假设 computing cost和link cost 不随时间改变
# 2. 假设 每个node的computing capacity都相等，均为50


import numpy as np
from gurobipy import *
import random
import os
from multiprocessing import Manager, Process, Pool
from func1 import gurobi

# neighbor relation
# 需要有一个数据结构来记录node间的依赖关系，注意：A和 B,C 是邻居，不能说明 B和C 是邻居； A==>B, 也不意味着 B==>A, 即 A会使用B的资源，B不一定会使用A的资源。
# 一个matrix：【】N x N的矩阵，每个元素X_ij 表示 node i 是否可使用 node j 的资源？ 1==> Yes, 0==> No
ALL_NODE = 10
CAPACITY = 50
random.seed(20)
updateTag = 1
ITERATION_NUM = 48

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

# 设置node的computer cost
compCost = np.zeros((ALL_NODE, ALL_NODE), dtype = np.int16)
for i in range(ALL_NODE):
	for j in range(ALL_NODE):
		if(i==j):
			compCost[i][j] = 1

compCost[0][1] = 2
compCost[0][3] = 3 
compCost[0][4] = 3
compCost[1][4] = 2
compCost[1][5] = 3    
compCost[2][5] = 2
compCost[2][6] = 3 
compCost[3][0] = 3
compCost[3][5] = 3
compCost[4][0] = 2
compCost[4][7] = 3
compCost[4][8] = 2
compCost[5][1] = 3
compCost[5][2] = 2
compCost[5][6] = 3
compCost[6][2] = 2
compCost[6][9] = 3
compCost[7][3] = 2
compCost[7][4] = 3
compCost[7][8] = 2
compCost[8][5] = 2
compCost[8][7] = 3
compCost[8][9] = 2
compCost[9][8] = 3
compCost[9][6] = 3

# 设置node的link cost
linkCost = np.zeros((ALL_NODE, ALL_NODE), dtype = np.int16)
for i in range(ALL_NODE):
	for j in range(ALL_NODE):
		if(i==j):
			linkCost[i][j] = 1

linkCost[0][1] = 3
linkCost[0][3] = 4 
linkCost[0][4] = 3
linkCost[1][4] = 3
linkCost[1][5] = 2    
linkCost[2][5] = 4
linkCost[2][6] = 2 
linkCost[3][0] = 2
linkCost[3][5] = 3
linkCost[4][0] = 3
linkCost[4][7] = 2
linkCost[4][8] = 3
linkCost[5][1] = 2
linkCost[5][2] = 3
linkCost[5][6] = 4
linkCost[6][2] = 2
linkCost[6][9] = 2
linkCost[7][3] = 3
linkCost[7][4] = 2
linkCost[7][8] = 4
linkCost[8][5] = 3
linkCost[8][7] = 2
linkCost[8][9] = 3
linkCost[9][8] = 4
linkCost[9][6] = 2

# 生成此时刻的各node实际收到的requests：
realRequests = np.zeros(ALL_NODE, dtype = np.int16)
for i in range(10):
	temp = random.randint(20,80)
	realRequests[i] = temp

# 每个node可以使用的资源总和
nodesCanUseCapa = np.zeros(ALL_NODE, dtype = np.int16)
for i in range(ALL_NODE):
	for j in range(ALL_NODE):
		nodesCanUseCapa[i] += initCapacity[i][j]

# 设置此时刻各node实际可以handle的requests 总数；超过capacity的请求被拒绝
handleRequests = np.zeros(ALL_NODE, dtype = np.int16)
for i in range(ALL_NODE):
	if nodesCanUseCapa[i] < realRequests[i]:
		handleRequests[i] = nodesCanUseCapa[i]
	else:
		handleRequests[i] = realRequests[i]

# 统计有多少请求到达edge cloud：
totalRequests = 0
for i in range(ALL_NODE):
	totalRequests += realRequests[i]

# 统计有多少请求被受理：
totalHandles = 0
for i in range(ALL_NODE):
	totalHandles += handleRequests[i]


# print(nodesNum)
# print(linkCost) 
# print(relMatrix)
# print(initCapacity)

# *************************************************************
# 启动10个子进程 模拟各自优化过程； controller等待子进程传回结果，尝试采用shared memory和message queue
# controller传给子进程的参数：
#（1）该node可使用的资源分配
#（2）此时的computer cost和link cost
#（3）该node在此timeslot会有多少request需要处理
#（4）一共有几个nodes可用


updateCapa = np.array(initCapacity)
testCapa = np.zeros(ALL_NODE, dtype = np.int16) #用来测试leftCapa是不是都为0
costCollect = np.zeros(ALL_NODE, dtype = np.int16)
totalCost = 0


for timeSlot in range(ITERATION_NUM):

	# 存储每个shared objects
	capa_nodes = []
	compCost_nodes = []
	linkCost_nodes = []
	requests_nodes = []
	#收集返回的usage 数据：
	usage_nodes = []
	cost_nodes = []

	p = Pool(10)
	manager = Manager()
	for i in range(10):
		capa_pernode = manager.Array('i', updateCapa[i])	
		compCost_pernode = manager.Array('i', compCost[i])
		linkCost_pernode = manager.Array('i', linkCost[i])
		requests_pernode = manager.Value('i', handleRequests[i])
		usage_pernode = manager.Array('i', updateCapa[i])
		cost_pernode= manager.Value('i', costCollect[i])

		capa_nodes.append(capa_pernode)
		compCost_nodes.append(compCost_pernode)
		linkCost_nodes.append(linkCost_pernode)
		requests_nodes.append(requests_pernode)
		usage_nodes.append(usage_pernode)
		cost_nodes.append(cost_pernode)


		p.apply_async(gurobi, (capa_pernode, compCost_pernode, 
			linkCost_pernode, requests_pernode, usage_pernode, cost_pernode))

	p.close()
	p.join()

	for i in range(ALL_NODE):
		totalCost += cost_nodes[i].value
	
	##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	#+++++++++++++++++++ 根据usage 更新下一次的资源分布
	# create 一个临时的array来保存中转的更新信息,每个node给别人的资源有多少别人没用，然后拿它们分配给给资源不够的邻居
	leftCapa = np.zeros(ALL_NODE, dtype = np.int16)

	# 临时更新用的tempCapa
	tempCapa = np.array(updateCapa)
	# 先统计可以减少的资源
	for i in range(ALL_NODE):
		for j in range(ALL_NODE):
			if(usage_nodes[i][j] < updateCapa[i][j] and relMatrix[i][j]!=0):
			# if(usage_nodes[i][j] < initCapacity[i][j] and initCapacity[i][j]!=0 and i!=j):
				tempCapa[i][j] -= 1
				leftCapa[j] += 1
	# 再增加除了node本身以外的，给邻居的资源
	while (np.array_equal(leftCapa, testCapa)!= True):
		for i in range(ALL_NODE):
			for j in range(ALL_NODE):
				if(usage_nodes[i][j] == updateCapa[i][j] and i!=j and leftCapa[j]!=0 and relMatrix[i][j]!=0):
					tempCapa[i][j] += 1
					leftCapa[j] -= 1
		#最后检查是否还有剩余资源给本身：
		for j in range(ALL_NODE):
			if(leftCapa[j]!=0):
				tempCapa[j][j] += 1
				leftCapa[j] -= 1


	# 更新 updateCapa
	if(updateTag == 1):
		updateCapa = np.array(tempCapa)
	#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	# 生成下时刻的各node实际收到的requests：
	realRequests = np.zeros(ALL_NODE, dtype = np.int16)
	for i in range(10):
		temp = random.randint(20,80)
		realRequests[i] = temp

	# 每个node可以使用的资源总和
	nodesCanUseCapa = np.zeros(ALL_NODE, dtype = np.int16)
	for i in range(ALL_NODE):
		for j in range(ALL_NODE):
			nodesCanUseCapa[i] += updateCapa[i][j]

	# 设置下个时刻各node实际可以handle的requests 总数；超过capacity的请求被拒绝
	handleRequests = np.zeros(ALL_NODE, dtype = np.int16)
	for i in range(ALL_NODE):
		if nodesCanUseCapa[i] < realRequests[i]:
			handleRequests[i] = nodesCanUseCapa[i]
		else:
			handleRequests[i] = realRequests[i]

	# 统计有多少请求到达edge cloud：
	for i in range(ALL_NODE):
		totalRequests += realRequests[i]

	# 统计有多少请求被受理：
	for i in range(ALL_NODE):
		totalHandles += handleRequests[i]

	# print(updateCapa)
	# print("")

print(totalCost)
print(totalHandles / totalRequests)

	# print("The updateCapa :")
	# for i in range(ALL_NODE):
	# 	for j in updateCapa[i]:
	# 		print (str(j).ljust(4), end ="")
	# 	print("")



print("")
print("The initCapacity :")
for i in range(ALL_NODE):
	for j in initCapacity[i]:
		print (str(j).ljust(4), end ="")
	print("")
print("")

# print("nodesCanUseCapa: ")
# print(nodesCanUseCapa)

# print("realRequests: ")
# print(realRequests)

# print("handleRequests: ")
# print(handleRequests)


# print("The feedback of usage after one time iteration:")
# for i in range(ALL_NODE):
# 	for j in usage_nodes[i]:
# 		print (str(j).ljust(4), end ="")
# 	print("")
# print("")

print("The updateCapa :")
for i in range(ALL_NODE):
	for j in updateCapa[i]:
		print (str(j).ljust(4), end ="")
	print("")
print("")

# print("")
# print("The initCapacity :")
# for i in range(ALL_NODE):
# 	for j in initCapacity[i]:
# 		print (str(j).ljust(4), end ="")
# 	print("")
# print("")

# print("left capacity:")
# print(leftCapa)

# print('Optimization Complete!!!!!!!!!!!!!!!!!!!!!!!!')




