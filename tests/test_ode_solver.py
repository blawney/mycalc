__author__ = 'brian'

import sys
import os
import unittest
import numpy as np
import numpy.testing as npt
sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import model_solvers
import utils
from reaction_components import Reaction, Reactant, Product


class MockedReactionFactory(object):

    def __init__(self):
        pass

    def set_reaction(self, rx):
        self.reactions = rx

    def set_initial_conditions(self, ic):
        self.initial_conditions = ic

    def get_reactions(self):
        return self.reactions

    def get_initial_conditions(self):
        return self.initial_conditions

    def get_simulation_time(self):
        return 1.0


class MockedModel(object):
    """
    This class acts as a fake Model instance- it only needs
    the get_reactions method.

    We add reactions to it as necessary via the add_reactions method.
    That method is not available on the original Model instance, and it's merely
    for convenience here.
    """
    def __init__(self):
        self.initial_condition = {}

    def add_reactions(self, reaction_list):
        self.reactions = reaction_list

    def get_reactions(self):
        return self.reactions

    def set_initial_condition(self, ic):
        self.initial_condition = ic

    def get_initial_conditions(self):
        return self.initial_condition


class TestODESolver(unittest.TestCase):

    def test_rate_law_creation(self):

        """
        equations:
        2*A + B <--0.2,0.5 --> C
        3*C + D --5--> E

        Based on our equations created in the mocked Model, we have 4 rate laws:
        recall that all the forward reactions are treated first, then reverse
        r1 = 0.2*[A]^2[B]
        r2 = 5*[C]^3[D]
        r3 = 0.5*[C]
        r4 = 0*[E] = 0

        Those rate laws will be returned as a list of functions which will be used by iterative ode solver
        If we pass an array of concentrations, we can verify that the code result produced by the code matches
        the hand calculation.
        """

        # equation1:
        rx1 = Reaction(
            [Reactant('A',2), Reactant('B',1)],
            [Product('C',1)],
            0.2,
            0.5
        )

        # equation2:
        rx2 = Reaction(
            [Reactant('C', 3), Reactant('D',1)],
            [Product('E', 1)],
            5,
            0.0
        )
        reactions = [rx1, rx2]

        # to create the ODESolver, we need to pass it a Model instance.  For our purposes here, the Model instance
        # needs to have a get_reactions method which returns a list of Reaction instances
        m = MockedModel()
        m.add_reactions(reactions)
        solver = model_solvers.ODESolver(m)

        # the constructor calls a method which sets up the species_mapping attribute.  We don't want to test that
        # other method, so re-assign the species_mapping attribute here.
        solver.species_mapping = dict(zip(list('ABCDE'), range(5)))

        # set some values on the 'concentration' array
        cc = [2.0, 1.2, 3.0, 1.3, 0.4]

        rate_funcs = solver._calculate_rate_law_funcs(reactions)

        rate_vals = []
        for f in rate_funcs:
            rate_vals.append(f(cc))

        expected_rates = [
            0.2*cc[0]**2*cc[1],
            5*cc[2]**3*cc[3],
            0.5*cc[2],
            0.0
        ]
        npt.assert_allclose(rate_vals, expected_rates)

    def test_species_mapping_func(self):

        # equation1:
        rx1 = Reaction(
            [Reactant('A',2), Reactant('B',1)],
            [Product('C',1)],
            0.2,
            0.5
        )

        # equation2:
        rx2 = Reaction(
            [Reactant('C', 3), Reactant('D',1)],
            [Product('E', 1)],
            5,
            0.0
        )
        reactions = [rx1, rx2]

        # to create the ODESolver, we need to pass it a Model instance.  For our purposes here, the Model instance
        # needs to have a get_reactions method which returns a list of Reaction instances
        m = MockedModel()
        m.add_reactions(reactions)
        solver = model_solvers.ODESolver(m)
        result = solver.species_mapping
        expected = {'A':0, 'B':1, 'C':2, 'D':3, 'E':4}
        self.assertEqual(result, expected)

    def test_stoich_matrix_formed_correctly(self):
        # equation1: 2*A + B <-> C
        rx1 = Reaction(
            [Reactant('A',2), Reactant('B',1)],
            [Product('C',1)],
            0.2,
            0.5
        )
        # equation2: 3*C + D -> E
        rx2 = Reaction(
            [Reactant('C', 3), Reactant('D',1)],
            [Product('E', 1)],
            5,
            0.0
        )
        reactions = [rx1, rx2]

        # to create the ODESolver, we need to pass it a Model instance.  For our purposes here, the Model instance
        # needs to have a get_reactions method which returns a list of Reaction instances
        m = MockedModel()
        m.add_reactions(reactions)
        solver = model_solvers.ODESolver(m)
        result_mtx = solver.N

        expected_result = np.zeros((5,4))
        expected_result[:,0] = np.array([-2,-1,1,0,0])
        expected_result[:,1] = np.array([0,0,-3,-1,1])
        expected_result[:,2] = np.array([2,1,-1,0,0])
        expected_result[:,3] = np.array([0,0,3,1,-1])

        npt.assert_allclose(result_mtx, expected_result)

    def test_initial_conditions_init_to_zero_if_none_specified(self):
        # equation1: 2*A + B <-> C
        rx1 = Reaction(
            [Reactant('A',2), Reactant('B',1)],
            [Product('C',1)],
            0.2,
            0.5
        )
        # equation2: 3*C + D -> E
        rx2 = Reaction(
            [Reactant('C', 3), Reactant('D',1)],
            [Product('E', 1)],
            5,
            0.0
        )
        reactions = [rx1, rx2]

        # to create the ODESolver, we need to pass it a Model instance.  For our purposes here, the Model instance
        # needs to have a get_reactions method which returns a list of Reaction instances
        m = MockedModel()
        m.add_reactions(reactions)
        solver = model_solvers.ODESolver(m)
        ic = solver.initial_conditions
        npt.assert_allclose(ic, np.zeros(5))

    def test_initial_conditions_setting(self):
        # equation1: 2*A + B <-> C
        rx1 = Reaction(
            [Reactant('A',2), Reactant('B',1)],
            [Product('C',1)],
            0.2,
            0.5
        )
        # equation2: 3*C + D -> E
        rx2 = Reaction(
            [Reactant('C', 3), Reactant('D',1)],
            [Product('E', 1)],
            5,
            0.0
        )
        reactions = [rx1, rx2]

        # to create the ODESolver, we need to pass it a Model instance.  For our purposes here, the Model instance
        # needs to have a get_reactions method which returns a list of Reaction instances
        m = MockedModel()
        m.add_reactions(reactions)
        m.set_initial_condition({'A':1.2, 'C':0.2})
        solver = model_solvers.ODESolver(m)
        ic = solver.initial_conditions
        npt.assert_allclose(ic, np.array([1.2,0,0.2,0,0]))


class TestODESolverWJacobian(unittest.TestCase):

    def test_negative_initial_condition_raises_exception(self):
        # equation1:
        rx1 = Reaction(
            [Reactant('A',2), Reactant('B',1)],
            [Product('C',1)],
            0.2,
            0.5
        )

        # equation2:
        rx2 = Reaction(
            [Reactant('C', 3), Reactant('D',1)],
            [Product('E', 1)],
            5,
            0.0
        )
        reactions = [rx1, rx2]

        reaction_factory = MockedReactionFactory()
        reaction_factory.set_reaction(reactions)
        reaction_factory.set_initial_conditions({'A':1.0, 'E':0.2})

        with self.assertRaises(utils.InvalidInitialConditionException):
            model = utils.Model(reaction_factory)
            solver = model_solvers.ODESolverWJacobian(model)
            bad_new_initial_conditions = {'A':-1.0, 'B':2}
            solver.equilibrium_solution(X0=bad_new_initial_conditions)

    def test_resetting_initial_condition_with_invalid_symbol_raises_exception(self):
        # equation1:
        rx1 = Reaction(
            [Reactant('A',2), Reactant('B',1)],
            [Product('C',1)],
            0.2,
            0.5
        )

        # equation2:
        rx2 = Reaction(
            [Reactant('C', 3), Reactant('D',1)],
            [Product('E', 1)],
            5,
            0.0
        )
        reactions = [rx1, rx2]

        reaction_factory = MockedReactionFactory()
        reaction_factory.set_reaction(reactions)
        reaction_factory.set_initial_conditions({'A':1.0, 'E':0.2})

        with self.assertRaises(utils.InitialConditionGivenForMissingElement):
            model = utils.Model(reaction_factory)
            solver = model_solvers.ODESolverWJacobian(model)
            bad_new_initial_conditions = {'A':1.0, 'F':2}
            solver.equilibrium_solution(X0=bad_new_initial_conditions)

    def test_jacobian_value(self):
        # For a simple model where we calculate by hand, compare the hand-calculated (assumed correct!) value to
        # the one calculated by the Solver.
        # equation1: A + 2*B <-> C
        rx1 = Reaction(
            [Reactant('A',1), Reactant('B',2)],
            [Product('C',1)],
            0.2,
            0.5
        )
        # equation2: C + D <-> E
        rx2 = Reaction(
            [Reactant('C', 1), Reactant('D',1)],
            [Product('E', 1)],
            5,
            2.3
        )
        reactions = [rx1, rx2]

        # to create the ODESolver, we need to pass it a Model instance.  For our purposes here, the Model instance
        # needs to have a get_reactions method which returns a list of Reaction instances
        m = MockedModel()
        m.add_reactions(reactions)
        m.set_initial_condition({'A':1.2,
                                 'B':2.5,
                                 'C':0.2,
                                 'D':5.2,
                                 'E':1.3})
        solver = model_solvers.ODESolverWJacobian(m)
        X0 = solver.initial_conditions
        calculated_jacobian = solver._jacobian(X0)

        k = solver.kvals
        expected_jacobian = np.empty((5,5))
        expected_jacobian[0,:] = np.array([-k[0]*X0[1]**2, -2*k[0]*X0[0]*X0[1], k[2], 0, 0])
        expected_jacobian[1,:] = np.array([-2*k[0]*X0[1]**2, -4*k[0]*X0[0]*X0[1], 2*k[2], 0,0])
        expected_jacobian[2,:] = np.array([k[0]*X0[1]**2, 2*k[0]*X0[0]*X0[1], -k[1]*X0[3]-k[2], -k[1]*X0[2], k[3]])
        expected_jacobian[3,:] = np.array([0, 0, -k[1]*X0[3], -k[1]*X0[2], k[3]])
        expected_jacobian[4,:] = np.array([0, 0, k[1]*X0[3], k[1]*X0[2], -k[3]])

        npt.assert_allclose(calculated_jacobian, expected_jacobian)

    def test_dxdt_value(self):
        # For a simple model where we calculate by hand, compare the hand-calculated (assumed correct!) value to
        # the one calculated by the Solver.
        # equation1: A + 2*B <-> C
        rx1 = Reaction(
            [Reactant('A',1), Reactant('B',2)],
            [Product('C',1)],
            0.2,
            0.5
        )
        # equation2: C + D <-> E
        rx2 = Reaction(
            [Reactant('C', 1), Reactant('D',1)],
            [Product('E', 1)],
            5,
            2.3
        )
        reactions = [rx1, rx2]

        # to create the ODESolver, we need to pass it a Model instance.  For our purposes here, the Model instance
        # needs to have a get_reactions method which returns a list of Reaction instances
        m = MockedModel()
        m.add_reactions(reactions)
        m.set_initial_condition({'A':1.2,
                                 'B':2.5,
                                 'C':0.2,
                                 'D':5.2,
                                 'E':1.3})
        solver = model_solvers.ODESolverWJacobian(m)
        X0 = solver.initial_conditions
        calculated_dxdt = solver._dX_dt(X0)

        k = solver.kvals
        expected_dxdt = np.empty(5)
        expected_dxdt[0] = -k[0]*X0[0]*X0[1]**2 + k[2]*X0[2]
        expected_dxdt[1] = -2*k[0]*X0[0]*X0[1]**2 + 2*k[2]*X0[2]
        expected_dxdt[2] = k[0]*X0[0]*X0[1]**2 - k[1]*X0[2]*X0[3] - k[2]*X0[2] + k[3]*X0[4]
        expected_dxdt[3] = -k[1]*X0[2]*X0[3] + k[3]*X0[4]
        expected_dxdt[4] = k[1]*X0[2]*X0[3] - k[3]*X0[4]

        npt.assert_allclose(calculated_dxdt, expected_dxdt)

