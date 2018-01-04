#!/usr/bin/python
# -*- coding: utf-8 -*-

# 第一：假设 某个 EC_i 有 9个neighbors, 包含其本身则是10个可分配任务的nodes；
#      本身的node使用index【0】
# 第二：假设 当前有50个requests，等待分配给10个nodes
# 第三：本程序所有index对应：self->node0, neighbor1 ~neighbor9 -> node1~9

from gurobipy import *
import numpy as np
import random

def gurobi(capa, comp, link, reqs, usage):
	# cost limitation
	LIMIT = 100
	# task request number
	NUM_REQUESTS = reqs.value
	# get the number of nodes in the whole cloud
	NUM_NODE = 0
	# node names
	nodes = []
	# the available capacity from self and other neighbors
	capacity = {}
	index = 0
	for i in capa:
		NUM_NODE += 1
		nodes.append('node' + str(index))
		capacity['node'+str(index)] = i
		index += 1
	
	# the computing cost, self is 1, neighbors: 2~5 randomly
	compCost = {}
	index = 0
	for i in comp:
		compCost['node'+str(index)] = i
		index += 1

	# the link cost, self is 1, neighbors: 2~5 randomly
	linkCost = {}
	index = 0
	for i in link:
		linkCost['node'+str(index)] = i
		index += 1

	try:
		# Create model
		m = Model('edgeReqAssign')

		# Model data
		# requests number
		requests = []
		for i in range(NUM_REQUESTS):
			requests.append('req' + str(i))


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
			usage[count] = int(temp)
			count += 1

		# print(usage)
		print('Object: minimum cost => ', m.objVal)
		print('Optimization Time ==>%.5f second' %(m.Runtime))


	except GurobiError:
		print('Error reported!')