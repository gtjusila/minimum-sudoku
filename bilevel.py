"""
bilevel.py

A Gurobi Extension For Building Bilevel Model. A bilevel model is defined by an mps file similar to that of an ILP plus an auxillary
file determining which variables and constraints belongs to the lower level program
"""
import gurobipy as gp
from gurobipy import GRB
import os

class BilevelModel:

    def __init__(self, instance_name):
        """
        Create a new bilevel model. Instantiate a gurobi model and additional varibles to store bilevel related information
        """
        self.instance_name = instance_name
        self.model = gp.Model(self.instance_name)
        self.lower_level_constraints_index = []
        self.lower_level_variables_index = []
        self.lower_level_objective_coefficient = []
        self.lower_level_objective_sense = GRB.MINIMIZE

    def add_upper_level_variables(self, *args, **kwargs):
        """
        Add multiple upper level variables, a wrap around gurobi interface add multiple variables
        """
        var = self.model.addVars(*args, **kwargs)
        self.model.update()
        return var

    def add_upper_level_variable(self, *args, **kwargs):
        """
        Add a single upper level variable, a wrap around gurobi interface to add single variable
        """
        var = self.model.addVar(*args, **kwargs)
        self.model.update()
        return var

    def add_lower_level_variables(self, *args, **kwargs):
        """
        Add multiple lower level variables, add them to gurobi model and store bilevel specific information
        """
        count_before = self.model.getAttr("NumVars")
        var = self.model.addVars(*args, **kwargs)
        self.model.update()
        count_after = self.model.getAttr("NumVars")
        for i in range(count_before, count_after):
            self.lower_level_variables_index.append(i)
        return var

    def add_lower_level_variable(self, *args, **kwargs):
        """
        Add a single lower level variables, add it to gurobi model and store bilevel specific information
        """
        count_before = self.model.getAttr("NumVars")
        var = self.model.addVar(*args, **kwargs)
        self.model.update()
        self.lower_level_variables_index.append(count_before)
        return var

    def add_upper_level_constraints(self, *args, **kwargs):
        """
        Add multiple upper level constraints, a wrap around gurobi interface to add multiple constraints
        """
        self.model.addConstrs(*args, **kwargs)

    def add_upper_level_constraint(self, *args, **kwargs):
        """
        Add a single upper level constraint, a wrap around gurobi interface to add a single constraint
        """
        self.model.addConstr(*args, **kwargs)

    def add_lower_level_constraints(self, *args, **kwargs):
        """
        Add a multiple lower level constraints, add it to gurobi model and store bilevel specific information
        """
        count_before = self.model.getAttr("NumConstrs")
        self.model.addConstrs(*args, **kwargs)
        self.model.update()
        count_after = self.model.getAttr("NumConstrs")
        for i in range(count_before, count_after):
            self.lower_level_constraints_index.append(i)

    def add_lower_level_constraint(self, *args, **kwargs):
        """
        Add a single lower level constraints, add it to gurobi model and store bilevel specific information
        """
        count_before = self.model.getAttr("NumConstrs")
        self.model.addConstr(*args, **kwargs)
        self.model.update()
        self.lower_level_constraints_index.append(count_before)

    def set_upper_level_objective(self, *args, **kwargs):
        """
        Set upper level objective
        """
        return self.model.setObjective(*args, **kwargs)

    def set_lower_level_objective(self, constraint, sense):
        """
        Specify lower level objective and save bilevel specific information
        """
        constr = self.model.addConstr(constraint >= 0, name="LLO") # LLO For Lower Level Objective
        variables = self.model.getVars()
        self.model.update()
        for i in self.lower_level_variables_index:
            self.lower_level_objective_coefficient.append(self.model.getCoeff(constr, variables[i]))
        self.lower_level_objective_sense = sense

    def generate_model_files(self, mps_file, aux_file):
        """
        Generate the model mps file along with the auxillary file
        """
        self.model.write(mps_file)
        with open(aux_file, 'w') as f:
            f.write(f'N {len(self.lower_level_variables_index)}\n')
            f.write(f'M {len(self.lower_level_constraints_index)}\n')
            for i in self.lower_level_variables_index:
                f.write(f'LC {i}\n')
            for i in self.lower_level_constraints_index:
                f.write(f'LR {i}\n')
            for i in self.lower_level_objective_coefficient:
                f.write(f'LO {i}\n')
            if self.lower_level_objective_sense == GRB.MAXIMIZE:
                f.write('OS -1')
            else:
                f.write('OS 1')