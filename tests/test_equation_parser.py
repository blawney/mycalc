__author__ = 'brian'

import sys
import os
sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import utils
from reaction_components import Reactant, Product
import unittest

class TestStringExpressionParser(unittest.TestCase):

    # some tests related to the arrow in the equation
    def test_backwards_arrow_raises_error(self):
        bad_eqn = 'A + B <- C,0.2,0.3'
        with self.assertRaises(utils.MalformattedReactionDirectionSymbolException):
            utils.StringExpressionParser.parse(bad_eqn)

    def test_bad_arrow_raises_error(self):
        bad_eqn = 'A + B > C,0.2,0.3'
        with self.assertRaises(utils.MalformattedReactionDirectionSymbolException):
            utils.StringExpressionParser.parse(bad_eqn)

    def test_unidirectional_with_two_rate_constants_raises_exception(self):
        bad_eqn = 'A + B -> C,0.2,0.3'
        with self.assertRaises(utils.ExtraRateConstantException):
            utils.StringExpressionParser.parse(bad_eqn)

    # some tests related to the rate constants- missing, non-float
    def test_missing_reverse_rate_constant_for_bidirectional_reaction(self):
        bad_eqn = 'A + B <-> C,0.2'
        with self.assertRaises(utils.MissingRateConstantException):
            utils.StringExpressionParser.parse(bad_eqn)
        bad_eqn = 'A + B <-> C,0.2,'
        with self.assertRaises(utils.MissingRateConstantException):
            utils.StringExpressionParser.parse(bad_eqn)

    def test_missing_rate_constant_for_unidirectional_reaction(self):
        bad_eqn = 'A + B -> C'
        with self.assertRaises(utils.MissingRateConstantException):
            utils.StringExpressionParser.parse(bad_eqn)
        bad_eqn = 'A + B -> C,'
        with self.assertRaises(utils.MissingRateConstantException):
            utils.StringExpressionParser.parse(bad_eqn)

    def test_non_numerical_rate_constant_for_unidirectional_reaction(self):
        bad_eqn = 'A + B -> C,a'
        with self.assertRaises(utils.RateConstantFormatException):
            utils.StringExpressionParser.parse(bad_eqn)
        bad_eqn = 'A + B <-> C,0.1,k'
        with self.assertRaises(utils.RateConstantFormatException):
            utils.StringExpressionParser.parse(bad_eqn)
        bad_eqn = 'A + B <-> C,k,0.2'
        with self.assertRaises(utils.RateConstantFormatException):
            utils.StringExpressionParser.parse(bad_eqn)
        bad_eqn = 'A + B <-> C,k,k'
        with self.assertRaises(utils.RateConstantFormatException):
            utils.StringExpressionParser.parse(bad_eqn)

    def test_missing_coefficient_in_reactants(self):
        bad_eqn = 'A + *B <-> C,0.1,0.1'
        with self.assertRaises(utils.MalformattedReactionException):
            utils.StringExpressionParser.parse(bad_eqn)

    def test_bad_symbols_raise_exceptions(self):
        with self.assertRaises(utils.InvalidSymbolName):
            utils.StringExpressionParser.check_symbol_name('2A')
        with self.assertRaises(utils.InvalidSymbolName):
            utils.StringExpressionParser.check_symbol_name('-A')
        with self.assertRaises(utils.InvalidSymbolName):
            utils.StringExpressionParser.check_symbol_name('!A')
        with self.assertRaises(utils.InvalidSymbolName):
            utils.StringExpressionParser.check_symbol_name('A-!')

    def test_bad_symbol_coefficient(self):
        bad_eqn = 'A + 2A*B <-> C,0.1,0.1'
        with self.assertRaises(utils.MalformattedReactionException):
            utils.StringExpressionParser.parse(bad_eqn)

    def test_adds_repeated_symbol_coefficients(self):
        eqn = 'A + 2*A + B + 3*A <-> C,0.1,0.1'
        reactants, products, fwd_k, rev_k, is_bidirectional = utils.StringExpressionParser.parse(eqn)
        for r in reactants:
            if r.symbol == 'A':
                self.assertEqual(r.coefficient, 6)

    def test_single_reactant_equation(self):
        eqn = 'T <-> Tf,0.5,0.5'
        reactants, products, fwd_k, rev_k, is_bidirectional = utils.StringExpressionParser.parse(eqn)
        self.assertEquals(len(reactants),1)
        self.assertEqual(reactants[0], Reactant('T',1))
        self.assertEqual(len(products),1)
        self.assertEqual(products[0], Product('Tf',1))

if __name__ == '__main__':
    unittest.main()