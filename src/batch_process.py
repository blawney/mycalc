import reaction_factories
import model_solvers
import models

import os
import pandas as pd

class BatchCalculationException(Exception):
    pass


def process_batch(df, eqn_file):
    """
    df is a Pandas DataFrame instance.
    eqn_file is a formatted model file

    It should have column names that match the species given in the model file so we 
    can map the dataframe's values to the initial conditions properly.

    Furthermore, the values in the dataframe should all have the same units-- we make no 
    consideration for the relative units here-- that should all be cleared up prior to 
    calling this function.
    """

    factory = reaction_factories.FileReactionFactory(eqn_file)
    model = models.Model(factory)
    solver = model_solvers.ODESolverWJacobian(model)

    # get all the species given in the model file:
    species_set = set()
    for rx in factory.get_reactions():
        species_set = species_set.union(rx.get_all_species())

    # From a general model file we cannot judge which species are necessary for creating
    # a sensible reaction system.  We also would like to allow more columns than just the
    # data we're operating on, so we want to ignore those columns.  
    col_set = set(df.columns.tolist())
    if len(col_set.intersection(species_set)) == 0:
        raise BatchCalculationException('The input dataframe did not contain any columns headers in common with our reaction system.')

    def process(row, species_set):
        """
        A method for using with apply on the row axis
        sets up the initiial conditions and runs until convergence
        returns a pandas Series with the equilibrium concentrations of all species
        """
        ic = {}
        for s in species_set:
            try:
                ic[s] = row[s]
            except KeyError as ex:
                ic[s] = 0.0

        sample_to_column_mapping, solution, t = solver.equilibrium_solution(X0=ic)

        final_vals = solution[-1,:]
        index = ['']*len(final_vals)
        for sample, col_idx in sample_to_column_mapping.items():
            index[col_idx] = sample
        s = pd.Series(final_vals, index=index)
        return s

    results = df.apply(process, args=(species_set,), axis=1)
    df = pd.concat([df,results], axis=1)
    return df
