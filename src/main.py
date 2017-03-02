__author__ = 'brian'

from src import utils, model_solvers

if __name__ == '__main__':
    eqn_file = 'testosterone_model.txt'

    factory = utils.FileReactionFactory(eqn_file)
    model = utils.Model(factory)
    solver1 = model_solvers.ODESolver(model)
    sample_to_column_mapping, solution1, t = solver1.equilibrium_solution()
    print solution1[-1,:]

    solver2 = model_solvers.ODESolverWJacobian(model)
    sample_to_column_mapping, solution2, t = solver2.equilibrium_solution()
    print solution2[-1,:]