__author__ = 'brian'

import utils
import model_solvers

if __name__ == '__main__':
    eqn_file = 'equations.txt'

    factory = utils.FileReactionFactory(eqn_file)
    model = utils.Model(factory)
    solver = model_solvers.ODESolver(model)