"""
generate_unavoidable_set.py

Generate MPS file for the bilevel solver once the unavoidable sets are generated.
"""
import argparse
import time
from instance import ProblemInstance
import os

parser = argparse.ArgumentParser()
parser.add_argument("-g","--grid",type=str, required=True, help="The sudoku grid for which unavoidable sets need to be generated")
parser.add_argument("-n","--num_sets",type=int, required=True, help="The number of unavoidable sets to be generated")
parser.add_argument("-o","--output",type=str, required=True, help="The name of the output. Output will be generated in ./unavoidable_sets/<OUTPUT_NAME>")
args = parser.parse_args()

start = time.time()
print(f'Generating Unavoidable Sets for grid {args.grid}')
if not os.path.exists("./unavoidable_sets"):
    os.mkdir("./unavoidable_sets")
instance = ProblemInstance(f'{args.grid}', 3, 3, 3, 3)
instance.fit(args.grid)
instance.generate_cuts(n_cuts=args.num_sets,data_file=f'./unavoidable_sets/{args.output}.data.csv',
    cut_file=f'./unavoidable_sets/{args.output}.cuts')
print(f'Generation done. Elapsed Time {time.time() - start:.2f} s')
