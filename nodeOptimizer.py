#!/usr/bin/python
# -*- coding: utf-8 -*-

# 第一：假设 某个 EC_i 有 9个neighbors, 包含其本身则是10个可分配任务的nodes；
#      本身的node使用index【0】
# 第二：假设 当前有50个requests，等待分配给10个nodes
# 第三：本程序所有index对应：self->node0, neighbor1 ~neighbor9 -> node1~9

from gurobipy import *
import numpy as np
import random

LIMIT = 6
NUM_REQUESTS = 50
NUM_NODE = 10
ALL_NODE = 10
NODETAG = 0 #标记这是哪个node
# create a matrix to save the result of final assignment of requests
# x_ij 表示 node_i 使用了来自于node_j的多少资源
usage = np.zeros((ALL_NODE,ALL_NODE), dtype = np.int16)

try:
	# Create model
	m = Model('edgeReqAssign')

	# Model data
	# requests number
	requests = []
	for i in range(NUM_REQUESTS):
		requests.append('req' + str(i))

	# nodes
	nodes = []
	for i in range(10):
		nodes.append('node' + str(i))
	# the available capacity of neighbors, sum=30+4*9=66 > 50 自身只有30可以用，其他的邻居协助
	capacity = {
		'node0': 30,
		'node1': 4,
		'node2': 4,
		'node3': 4,
		'node4': 4,
		'node5': 4,
		'node6': 4,
		'node7': 4,
		'node8': 4,
		'node9': 4
	}
	# the computing cost, self is 1, neighbors: 2~5 randomly
	compCost = {
		'node0': 1,
		'node1': 2,
		'node2': 3,
		'node3': 4,
		'node4': 5,
		'node5': 2,
		'node6': 3,
		'node7': 3,
		'node8': 5,
		'node9': 2
	}
	# the link cost, self is 1, neighbors: 2~5 randomly
	linkCost = {
		'node0': 1,
		'node1': 3,
		'node2': 2,
		'node3': 4,
		'node4': 4,
		'node5': 3,
		'node6': 2,
		'node7': 3,
		'node8': 4,
		'node9': 5
	}
	# create variables
	choices = m.addVars(requests, nodes, vtype = GRB.BINARY, name = 'choices' )
	totalCost = 0
	for i, j in choices:
		totalCost = totalCost + choices[i,j] * (compCost[j] + linkCost[j])

	# set objective
	m.setObjective(totalCost, GRB.MINIMIZE)
	
	# set constrains
	# 每个request只能分配给一个node
	for i in requests:
		temp = 0
		for j in nodes:
			temp = temp + choices[i,j]
		m.addConstr(temp == 1, i)

	# 每个node被分配到任务不能超出capacity
	for j in nodes:
		temp = 0
		for i in requests:
			temp = temp + choices[i,j]
		m.addConstr(temp <= capacity[j])

	# 每个request关于cost（latency）的限制
	for i, j in choices:
		temp = 0
		temp = choices[i,j] * (compCost[j] + linkCost[j])
		m.addConstr(temp <= LIMIT)


	# optimization
	m.optimize()

	#print result
	varResult = m.getVars()
	index = 0
	print("       ", end="")
	for i in nodes:
		print(i.ljust(7), end="")
	print("")
	for i in range(NUM_REQUESTS):
		print ('req' + str(i).ljust(2), end="    ")
		for j in range(NUM_NODE):
			print(int(abs(varResult[index].x)), end = "      ")
			index += 1
		print("")

	count = 0
	for j in nodes:
		temp = 0
		for i in requests:
			temp += choices.select(i,j)[0].x
		usage[NODETAG][count] = int(temp)
		count += 1

	print(usage)
	print('Object: minimum cost => ', m.objVal)
	print('Optimization Time ==>%.5f second' %(m.Runtime))


except GurobiError:
	print('Error reported!')