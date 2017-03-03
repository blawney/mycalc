__author__ = 'brian'

import reaction_factories
import model_solvers
import models

if __name__ == '__main__':
    eqn_file = 'testosterone_model.txt'

    factory = reaction_factories.FileReactionFactory(eqn_file)
    model = models.Model(factory)
    solver1 = model_solvers.ODESolver(model)
    sample_to_column_mapping, solution1, t = solver1.equilibrium_solution()
    print solution1[-1,:]

    solver2 = model_solvers.ODESolverWJacobian(model)
    sample_to_column_mapping, solution2, t = solver2.equilibrium_solution()
    print solution2[-1,:]