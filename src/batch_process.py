import reaction_factories
import model_solvers
import models

import os
import pandas as pd

def process_batch(input_file, eqn_file):

    factory = reaction_factories.FileReactionFactory(eqn_file)
    model = models.Model(factory)
    solver = model_solvers.ODESolverWJacobian(model)

    # get all the species:
    species_set = set()
    for rx in factory.get_reactions():
        species_set = species_set.union(rx.get_all_species())


    df = pd.read_table(input_file)
    col_set = set(df.columns.tolist())
    if len(col_set.difference(species_set)) > 0:
        pass # problem!
    #df['ALB'] = df['ALB'] * 1e9 * (10./65000)

    def process(row, species_set):
        ic = {}
        for s in species_set:
            try:
                ic[s] = row[s]
            except KeyError as ex:
                ic[s] = 0.0
        #ic = {'T': row['TT'], 'SHBG':0.5*row['SHBG'], 'Alb': row['ALB']}
        sample_to_column_mapping, solution, t = solver.equilibrium_solution(X0=ic)
        #target_idx = ['T','AlbT','SHBGT','S1T', 'Tf']
        #total_t = 0
        #for t in target_idx:
        #    idx = sample_to_column_mapping[t]
        #    total_t += solution[-1,idx]
        #total_t += 2*solution[-1, sample_to_column_mapping['SHBGT2']]
        #print '%s, %s' % (row['TT'], total_t)
        #for k,v in sample_to_column_mapping.items():
            #print '%s: %s' % (k,solution[-1,v])
            #print '*'*20

        final_vals = solution[-1,:]
        index = ['']*len(final_vals)
        for sample, col_idx in sample_to_column_mapping.items():
            index[col_idx] = sample
        s = pd.Series(final_vals, index=index)
        #return solution[-1,sample_to_column_mapping['T']]
        return s

    results = df.apply(process, args=(species_set,), axis=1)
    df = pd.concat([df,results], axis=1)
    print df
    print '*'*20
    return df
