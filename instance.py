"""
instances.py

Convert a sudoku instance into models
"""
import os.path
import pickle
import sys
import time

import gurobipy as gp
import numpy as np
import pandas as pd
from logging_helper import *
from gurobipy import GRB
import random
from bilevel import BilevelModel



class ProblemInstance:

    def __init__(self,
                 instance_name,
                 sub_matrix_width = 3, 
                 sub_matrix_height = 3, 
                 board_width = 3, 
                 board_height = 3):
        """
        Initiate a model and set some meta parameter of the model. The metaparameters are submatrix and board sizes 
        """
        self.sub_matrix_height = sub_matrix_height
        self.sub_matrix_width = sub_matrix_width
        self.board_height = board_height
        self.board_width = board_width
        self.instance_name = instance_name
        self.n = self.sub_matrix_width * self.board_width
        self.cuts = []
        self.puzzle = []
        self.current_solution = []
        self.board = np.zeros(shape=(self.n, self.n))
        self.hitting_set_lower_bound = 0

    def load_cuts(self, cut_file, n):
        """
        Get a set of unavoidable set cut from a cut file
        """
        with open(cut_file, "rb") as fp:   
            self.cuts = pickle.load(fp)[:n]

    def save_cuts(self, target):
        """
        Write generated unavoidable set cut into a cut file
        """
        with open(target, "wb") as fp:
            pickle.dump(self.cuts, fp)

    def fit(self, puzzle, solve = False):
        """
        Fit a problem into a model     
        """
        if len(puzzle) != self.n*self.n:
            print(f'Puzzle instance have invalid length. Actual: {len(puzzle)}. Should Be: {self.n**2}')
            return
        if(solve): 
            self.puzzle = []
            for i in range(self.n):
                for j in range(self.n):
                    if puzzle[self.n*i+j] != "0":
                        self.puzzle.append((i,j))
            try:
                puzzle = self.solve_puzzle(puzzle)
            except ValueError:
                print(f'Puzzle instance not solvable')
                return
        for i in range(self.n):
            for j in range(self.n):
                self.board[i][j] = int(puzzle[self.n*i+j])

    def solve_puzzle(self, puzzle):
        """
        If the puzzle instance is not yet solved, then this is a utility function to solve the puzzle using gurobi
        """
        model = gp.Model()
        x = model.addVars(self.n,self.n,self.n,vtype = GRB.BINARY, name = "X")
        model.addConstrs((x.sum(i,j,"*") == 1 
                        for i in range(self.n) 
                        for j in range(self.n)),
                        name="S")
        model.addConstrs((x.sum(i,"*",k) == 1 
                        for i in range(self.n) 
                        for k in range(self.n)),
                        name="C")
        model.addConstrs((x.sum("*",j,k) == 1 
                        for j in range(self.n) 
                        for k in range(self.n)),
                        name="R")
        model.addConstrs((gp.quicksum(x[i, j, k] 
                                        for i in range(i0*self.sub_matrix_height, (i0+1)*self.sub_matrix_height) 
                                        for j in range(j0*self.sub_matrix_width, (j0+1)*self.sub_matrix_width)) <= 1 
                                        for k in range(self.n) for i0 in range(self.board_height) 
                                        for j0 in range(self.board_width)), 
                                    name='SM')
        for i in range(self.n):
            for j in range(self.n):
                k = self.n*i+j
                if puzzle[k] != "0":
                    x[i, j, int(puzzle[k])-1].LB = 1
        model.setParam("OutputFlag",0)
        model.optimize()
        if(model.getAttr('Status')==3):
            raise ValueError
        xs = model.getAttr("X",x)
        sol = ""
        for i in range(self.n):
            for j in range(self.n):
                for k in range(self.n):
                    if xs[i,j,k] > 0.5:
                        sol += str(k+1)
        return sol

    def create_problem_instance_files(self, save_directory = None, with_cuts = False, with_lower_bound = False, lower_bound = 0):
        """
        Generate problem instance file after all cuts have been generated 
        """
        model = BilevelModel(self.instance_name)
        # Define Variables 
        x = model.add_lower_level_variables(self.n,self.n,self.n, vtype = GRB.BINARY, name = "X")
        m = model.add_lower_level_variable(vtype = GRB.BINARY, name = "M")
        y = model.add_upper_level_variables(self.n,self.n,vtype = GRB.BINARY, name = "Y")
        # Create lower level problem 
        model.add_lower_level_constraints((x.sum(i,j,"*") + m >= 1 
                                                for i in range(self.n) 
                                                for j in range(self.n)),
                                            name="S")
        model.add_lower_level_constraints((x.sum(i,"*",k)<= 1 
                                                for i in range(self.n) 
                                                for k in range(self.n)),
                                            name="C")
        model.add_lower_level_constraints((x.sum("*",j,k)<= 1 
                                                for j in range(self.n) 
                                                for k in range(self.n)),
                                            name="R")
        model.add_lower_level_constraints((gp.quicksum(x[i, j, k] 
                                                for i in range(i0*self.sub_matrix_height, (i0+1)*self.sub_matrix_height)
                                                for j in range(j0*self.sub_matrix_width, (j0+1)*self.sub_matrix_width)) <= 1 
                                                for k in range(self.n) for i0 in range(self.board_height) 
                                                for j0 in range(self.board_width)),
                                            name='SM')
        model.add_lower_level_constraints((x[i,j,int(self.board[i][j]-1)] >= y[i,j] 
                                                for i in range(self.n) 
                                                for j in range(self.n)),
                                            name="P")
        model.add_lower_level_constraint((gp.quicksum(x[i,j,int(self.board[i][j]-1)] 
                                                for i in range(self.n) 
                                                for j in range(self.n)) <= self.n*self.n-1), 
                                            name="N")
        # Create upper level problem
        model.add_upper_level_constraint(m >= 1, name="B")
        model.set_upper_level_objective(y.sum(), GRB.MINIMIZE)
        model.set_lower_level_objective(m, GRB.MINIMIZE)
        # Add Cuts 
        for i, cut in enumerate(self.cuts):
            model.add_upper_level_constraint(gp.quicksum(y[i,j] for i,j in cut) >= 1,name= f'U{i}')
        model.generate_model_files(os.path.join(save_directory,f'{self.instance_name}.mps'),os.path.join(save_directory,f'{self.instance_name}.aux'))
        print(f'Generated Instances File for instance {self.instance_name}')


    def generate_cuts(self, n_cuts, cut_file, data_file):
        """
        Cut Generation Procedure
        """
        start_time = time.time() # Start time measurement
        max_solve = 3*n_cuts
        cut_model = gp.Model("SudokuCut")
        cut_model.setParam("OutputFlag",0)
        """
        Add Variables
        """
        x = cut_model.addVars(self.n,self.n,self.n,vtype = GRB.BINARY, name = "X")
        p = 4 # Initially search for cuts of size 4
        self.cuts = []
        """
        Start building the model
        """
        cut_model.addConstrs((x.sum(i, j, '*') == 1 for i in range(self.n) for j in range(self.n)), name='S')
        cut_model.addConstrs((x.sum(i, '*', k) == 1 for i in range(self.n) for k in range(self.n)), name='C')
        cut_model.addConstrs((x.sum('*', j, k) == 1 for j in range(self.n) for k in range(self.n)), name='R')
        cut_model.addConstrs((gp.quicksum(x[i, j, k] for i in range(i0*self.sub_matrix_height, (i0+1)*self.sub_matrix_height) for j in range(j0*self.sub_matrix_width, (j0+1)*self.sub_matrix_width)) <= 1 for k in range(self.n) for i0 in range(self.board_height) for j0 in range(self.board_width)), name='SM')
        const = cut_model.addConstr(gp.quicksum(x[i,j,int(self.board[i][j]-1)] for i in range(self.n) for j in range(self.n)) == self.n*self.n-p, name = "P")
        """
        Initiate Variables 
        """ 
        optimization_runtime = 0
        cnt = 0
        fail = 0
        data = []
        for iter in range(max_solve):
            if len(self.cuts) >= n_cuts:
                # If enough cut generated then stop
                break
            if p > self.n**2:
                # If p is over n**2 then all cut have been generated
                break
            # Do the optimization
            cut_model.optimize()
            # Add time to measured time
            optimization_runtime+= cut_model.getAttr("Runtime")
            # Store Data 
            merged = dict()
            merged.update(get_gurobi_model_stats(cut_model))
            merged.update({"cut_size":p})
            data.append(merged)
            # Add iteration count 
            cnt += 1 
            status = cut_model.getAttr('Status')
            if(status == 3):
                # ILP Infreasible
                fail += 1
                cut_model.remove(const) # Remove p constraint
                p += 1 
                const = cut_model.addConstr(gp.quicksum(x[i,j,int(self.board[i][j]-1)] for i in range(self.n) for j in range(self.n)) == self.n*self.n-p, name = "P") # Add new p constant
                continue
            # ILP Feasible, get cut
            cut = []
            xs = cut_model.getAttr('X', x)
            for i in range(self.n):
                for j in range(self.n):
                    if (xs[i,j,int(self.board[i][j]-1)] < 0.5):
                        cut.append((i,j))
            self.cuts.append(cut)
            # Add no good cut
            cut_model.addConstr(gp.quicksum(x[i,j,int(self.board[i][j]-1)] for i,j in cut) >= 1, name = f'C{len(self.cuts)}')
            if(len(self.cuts) % 50 == 0):
                print(f'current set count: {len(self.cuts)}')
        total_runtime = time.time()-start_time
        cut_data = pd.DataFrame(data)
        cut_data.to_csv(data_file,index=False)
        self.save_cuts(cut_file)

    def check_current_solution(self):
        if(self.check_solution_feasibility(self.current_solution)):
            print("Current Solution Is Feasible")
        else:
            print("Current Solution Is Not Feasible")

    def check_solution_feasibility(self, solution):
        """
        Check if the generated sudoku grid have a unique solution 
        """
        another_solution = gp.Model("AnotherSolution")
        x = another_solution.addVars(self.n,self.n,self.n,vtype = GRB.BINARY, name = "X")
        another_solution.addConstrs((x.sum(i, j, '*') == 1 
                                    for i in range(self.n) 
                                    for j in range(self.n)), 
                                name='S')
        another_solution.addConstrs((x.sum(i, '*', k) == 1 
                                    for i in range(self.n) 
                                    for k in range(self.n)), 
                                name='C')
        another_solution.addConstrs((x.sum('*', j, k) == 1 
                                    for j in range(self.n) 
                                    for k in range(self.n)), 
                                name='R')
        another_solution.addConstrs((gp.quicksum(x[i, j, k] 
                                    for i in range(i0*self.sub_matrix_height, (i0+1)*self.sub_matrix_height) 
                                    for j in range(j0*self.sub_matrix_width, (j0+1)*self.sub_matrix_width)) <= 1 
                                    for k in range(self.n) 
                                    for i0 in range(self.board_height) 
                                    for j0 in range(self.board_width)), 
                                name='SM')
        for i,j in solution:
            x[i,j,int(self.board[i][j]-1)].LB = 1
        another_solution.addConstr(gp.quicksum(x[i,j,int(self.board[i][j]-1)] 
                                    for i in range(self.n) 
                                    for j in range(self.n)) <= self.n*self.n-1, 
                                name = "NG")
        another_solution.setParam("OutputFlag",0)
        another_solution.optimize()
        if(another_solution.getAttr('Status')==3):
            return True
        else:
            print("Found Another Solution:")
            a_solution = another_solution.getAttr("X",x)
            for i in range(self.n):
                sol = ''
                for j in range(self.n):
                    for k in range(self.n):
                        if(a_solution[i,j,k] >= 0.5):
                            sol += str(k+1) + ' '
                print(sol)
            return False

    def check_cuts(self):
        """
        Check randomly 100 unavoidable sets if they are correct, that is removing the set from the board  yields a non unique sudoku 
        """
        cuts = random.choices(self.cuts, k=min(100,len(self.cuts)))
        for cut in cuts:
            another_solution = gp.Model("AnotherSolution")
            x = another_solution.addVars(self.n, self.n, self.n, vtype=GRB.BINARY, name="X")
            another_solution.addConstrs((x.sum(i, j, '*') == 1
                                         for i in range(self.n)
                                         for j in range(self.n)),
                                        name='S')
            another_solution.addConstrs((x.sum(i, '*', k) == 1
                                         for i in range(self.n)
                                         for k in range(self.n)),
                                        name='C')
            another_solution.addConstrs((x.sum('*', j, k) == 1
                                         for j in range(self.n)
                                         for k in range(self.n)),
                                        name='R')
            another_solution.addConstrs((gp.quicksum(x[i, j, k]
                                                     for i in range(i0 * self.sub_matrix_height,
                                                                    (i0 + 1) * self.sub_matrix_height)
                                                     for j in range(j0 * self.sub_matrix_width,
                                                                    (j0 + 1) * self.sub_matrix_width)) <= 1
                                         for k in range(self.n)
                                         for i0 in range(self.board_height)
                                         for j0 in range(self.board_width)),
                                        name='SM')
            for i in range(self.n):
                for j in range(self.n):
                    if (i, j) not in cut:
                        x[i, j, int(self.board[i][j] - 1)].LB = 1
            another_solution.addConstr(gp.quicksum(x[i, j, int(self.board[i][j] - 1)]
                                                   for i in range(self.n)
                                                   for j in range(self.n)) <= self.n * self.n - 1,
                                       name="NG")
            another_solution.setParam("OutputFlag", 0)
            another_solution.optimize()
            if (another_solution.getAttr('Status') == 3):
                print("Bad Cut")
                return False
        print("Cut Check Passed")