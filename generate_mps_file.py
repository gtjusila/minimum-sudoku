"""
generate_mps_file.py

Generate MPS file for the bilevel solver once the unavoidable sets are generated.
"""
import argparse
import time
from instance import ProblemInstance
import os

parser = argparse.ArgumentParser()
parser.add_argument("-g","--grid",type=str, required=True, help="The sudoku grid for which the mps file needs to be generated")
parser.add_argument("-n","--num_sets",type=int, required=True, help="The number of unavoidable sets to be used")
parser.add_argument("-c","--cut_file",type=str, required=True, help="The name of the cut file which contain the unavoidable set. The script will use ./unavoidable_sets/<CUT_FILE>.cuts")
parser.add_argument("-o","--output",type=str, required=True, help="The name of the output. Output will be generated in ./mps_files")
args = parser.parse_args()

print(f'Generating Instance File for grid {args.grid}')
if not os.path.exists("./mps_files"):
    os.mkdir("./mps_files")
instance = ProblemInstance(f'{args.output}', 3, 3, 3, 3)
instance.fit(args.grid)
instance.load_cuts(f'./unavoidable_sets/{args.cut_file}.cuts',args.num_sets)
instance.check_cuts()
instance.create_problem_instance_files('./mps_files',with_cuts=True)