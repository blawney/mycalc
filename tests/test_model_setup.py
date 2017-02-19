__author__ = 'brian'


import sys
import os
sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import utils
from reaction_components import Reaction, Reactant, Product
import unittest


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


class TestModel(unittest.TestCase):
    def test_initial_condition_specified_for_nonexistent_element(self):
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
        reaction_factory.set_initial_conditions({'A':1.0, 'F':0.2})

        with self.assertRaises(utils.InitialConditionGivenForMissingElement):
            model = utils.Model(reaction_factory)