# -*- coding: utf-8 -*-
"""TSP_OPT.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1F_tLAChGTxQz34T66hdVm_O5glHhCxGZ
"""

#!pip install pyomo
#!apt-get install -y -qq glpk-utils
#!apt-get install -y -qq coinor-cbc

import pyomo.environ as pyo
import numpy as np
import os
import sys
import pandas as pd
import time

def solve_tsp_pyomo(distance_matrix, time_lim):
    n = len(distance_matrix)  # Number of cities

    # Create a Pyomo model
    model = pyo.ConcreteModel()

    # Sets of nodes (cities)
    model.N = pyo.RangeSet(0, n-1)

    # Variables: x[i, j] = 1 if the tour goes directly from city i to city j, 0 otherwise
    model.x = pyo.Var(model.N, model.N, within=pyo.Binary)

    # Subtour elimination variables
    model.u = pyo.Var(model.N, within=pyo.NonNegativeIntegers, bounds=(0, n-1))

    # Objective: Minimize the total travel distance
    model.obj = pyo.Objective(
        expr=sum(distance_matrix[i, j] * model.x[i, j] for i in model.N for j in model.N),
        sense=pyo.minimize
    )

    # Constraints
    def visit_once_rule(model, i):
        return sum(model.x[i, j] for j in model.N if i != j) == 1
    model.visit_once = pyo.Constraint(model.N, rule=visit_once_rule)

    def leave_once_rule(model, j):
        return sum(model.x[i, j] for i in model.N if i != j) == 1
    model.leave_once = pyo.Constraint(model.N, rule=leave_once_rule)

    # Subtour elimination constraints (MTZ formulation)
    def subtour_elimination_rule(model, i, j):
        if i != j and i > 0 and j > 0:
            return model.u[i] - model.u[j] + (n-1) * model.x[i, j] <= n-2
        return pyo.Constraint.Skip

    model.subtour_elimination = pyo.Constraint(model.N, model.N, rule=subtour_elimination_rule)

    # Solve the model
    solver = pyo.SolverFactory('cplex', executable="/Applications/CPLEX_Studio2211/cplex/bin/arm64_osx/cplex")
   
    solver.options['timelimit'] = time_lim  # Time limit in seconds
    result = solver.solve(model, tee=True)

    print(result)
    print("************")
   #print(pyo.value(model.x[3, 2]))

    # Extract the solution
    tour = []
    for i in model.N:
        for j in model.N:
            #print(i,j)
            if i != j and pyo.value(model.x[i, j]) > 0.5:
                tour.append((i, j))

    print(tour)

    # Convert the tour to a sequence of nodes
    sequence = [0]
    while len(sequence) < n:
        for i, j in tour:
            if i == sequence[-1]:
                sequence.append(j)
                break
    print(sequence)
    # Safely print the objective value
    #total_distance = pyo.value(model.obj)
    #print("Total distance:", total_distance)
    #print(pyo.value(model.obj))
    lower_bound = result.problem.lower_bound
    upper_bound = result.problem.upper_bound

    print(f"Lower Bound: {lower_bound}")
    print(f"Upper Bound: {upper_bound}")

    return sequence, upper_bound

# Example usage
# Assuming tsp_matrix is your distance matrix
# sequence, total_distance = solve_tsp_pyomo(tsp_matrix)
# print("Optimal sequence:", sequence)
# print("Total distance:", total_distance)

def read_tsp_file(filename):

    if os.path.exists(filename):
        data = pd.read_csv(filename)
        return data
    else:
        print(f"File {filename} not found.")
        return None

# data file
if len(sys.argv) < 3:
        print("Please provide a filename as an argument.")
        #return
else:
    # Get the input filename
    filename = sys.argv[1]
    time_lim = sys.argv[2]
    
#filename = "TSP_50_002.csv"

tsp_data = read_tsp_file(filename)
tsp_data.drop(columns=['X','Y'], inplace=True)
tsp_distance = tsp_data.to_numpy()

n = tsp_distance.shape[0]

start_time = time.time()
sequence, total_distance = solve_tsp_pyomo(tsp_distance, time_lim)
print("Optimal sequence:", sequence)
print("Total distance:", total_distance)
end_time = time.time()

# output FIle
output_filename = "bks.out"

    # Open the output file and write some info
with open(output_filename, 'a') as output_file:
	output_file.write(f"{filename}\t{total_distance}\t{end_time-start_time}\t{sequence}\n")

print(f"Output written to: {output_filename}")