import reaction_factories
import model_solvers
import models

import os
import pandas as pd

def process_single(ic, eqn_file):

    factory = reaction_factories.FileReactionFactory(eqn_file)
    model = models.Model(factory)
    solver = model_solvers.ODESolverWJacobian(model)

    sample_to_column_mapping, solution, t = solver.equilibrium_solution(X0=ic)

    final_vals = solution[-1,:]
    index = ['']*len(final_vals)
    for sample, col_idx in sample_to_column_mapping.items():
        index[col_idx] = sample
    return pd.Series(final_vals, index=index, name="final_concentrations")
