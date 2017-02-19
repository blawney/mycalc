__author__ = 'brian'

import sys
import os
import unittest
import numpy as np
import numpy.testing as npt
sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import model_solvers
from reaction_components import Reaction, Reactant, Product


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

        rate_funcs = solver.calculate_rate_law_funcs(reactions)

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
        solver.create_stoichiometry_matrix()
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