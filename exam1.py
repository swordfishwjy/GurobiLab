#!/usr/bin/python

# jianyu Wnag

from gurobipy import *

try:
	# create model
	m = Model("mip1")

	# create varialble
	x = m.addVar(vtype = GRB.BINARY, name = "x")
	y = m.addVar(vtype = GRB.BINARY, name = "y")
	z = m.addVar(vtype = GRB.BINARY, name = "z")

	# simple method to build a objective
	m.setObjective(x + y + 2*z, GRB.MAXIMIZE)
	# complex method to build a objective
	# obj = LinExpr()
	# obj += x
	# obj += y
	# obj += 2*z
	# m.setObjective(obj, GRB.MAXIMIZE)

	#constrains
	m.addConstr(x + 2*y +3*z <=4, "c0")
	m.addConstr(x + y >= 1, "c1")

	m.optimize()

	for v in m.getVars():
		print(v.varName, v.x)
	print('Obj: ', m.objVal)

except GurobitError:
	print('Error reported!')