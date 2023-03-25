"""
logging_helper.py

A utility function to help us get gurobi model stats
"""
def get_gurobi_model_stats(model):
    return {
        "num_vars": model.getAttr('numVars'),
        "num_consts": model.getAttr('numConstrs'),
        "runtime": model.getAttr('Runtime'),
        "work": model.getAttr('work'),
        "simplex_iteration": model.getAttr('IterCount'),
        "node_count": model.getAttr('NodeCount'),
        "open_node_count": model.getAttr('OpenNodeCount'),
        "bar_iter_count": model.getAttr('BarIterCount'),
        "status": model.getAttr('Status')
    }