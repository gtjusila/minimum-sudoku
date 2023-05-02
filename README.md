# How Many Clues To Give? A Bilevel Formulation For The Minimum Sudoku Clue Problem (Code)

## Prerequisites
 - [Gurobi](https://www.gurobi.com/documentation/9.5/quickstart_windows/cs_anaconda_and_grb_conda_.html) Installation with Python Interface
 - Pandas and Numpy
 - A [bilevel solver](https://msinnl.github.io/pages/bilevel.html) 

## Overview

The code consist of two main scripts:
 - `generate_unavoidable_set.py` which generate unavoidable sets for a given sudoku grid
 - `generate_mps_file.py` which take a sudoku grid and a set of unavoidable set and returns an mps file and an aux file to be given as input to the bilevel solver.

Furthermore, the instances we use for our paper is located in the folder **instances**. We also provide a list of 17 clues sudoku puzzles collected by Gordon Royle and A collection of non 17 clues sudoku puzzle with difficulty rating of more than 11 collected by the Enjoy Sudoku Players forum.

## Example Usage

We provide a step by step instruction to recreate the result of one of our exeriment instance. 

The instance is 
`793645281
158792436
642183795
537418629
961327548
284956173
375864912
416239857
829571364`  (Instance #0)

 1. First, we generate 5000 unavoidable sets
  
  `python generate_unavoidable_set.py -g 793645281158792436642183795537418629961327548284956173375864912416239857829571364 -n 5000 -o instancezero`

  This will generate two files in a newly created folder `unavoidable_sets` named `instancezero.cuts` and `instancezero.data.csv`. The former is a file containing information about the 5000 unavoidable set we created and the later contains statistics of the generation process.

 2. Now we generate the mps and aux file for the bilevel solver

 `python generate_mps_file.py -g 793645281158792436642183795537418629961327548284956173375864912416239857829571364 -n 3000 -o instancezero -c instancezero`

 This will first search the file `unavoidable_sets/instancezero.cuts` load the unavoidable set then generate the bilevel mps and aux file in the folder `mps_files` as 
`instancezero.mps` and `instancezero.aux`. The first 3000 unavoidable sets will be used as determined by the `-n` parameter

3. The generated MPS and aux file can be used as input to you bilevel solver of choice. We use the following [bilevel solver](https://msinnl.github.io/pages/bilevel.html) with setting 2.

## Computational Results

1. `unavoidable_sets_generation` contains solver data for the unavoidable set generation experiments.
2. `unavoidable_sets` contains actual `.cuts` file that we use for the bilevel models.
3. `9by9.csv` contains the solver data from the bilevel solving experiments.

## Source

1. https://msinnl.github.io/pages/bilevel.html
2. https://github.com/t-dillon/tdoku/tree/master/benchmarks for instances.
