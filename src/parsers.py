__author__ = 'brian'

import re

from custom_exceptions import *
from reaction_components import Reaction, Reactant, Product

class ExpressionParser(object):
    """
    A base class to derive from.  Derived children of this class ideally implement methods to parse individual
    reaction 'sources'
    """
    @classmethod
    def parse(cls, item):
        raise NotImplementedError


class StringExpressionParser(ExpressionParser):
    """
    An implementation of ExpressionParser for reading strings and forming
    """
    # some compiled regular expressions for parsing through reactions specified by strings
    direction_symbol_regex = re.compile('<?[-]+>')
    equation_regex = re.compile('[a-zA-Z0-9\+\s\*]+')
    symbol_regex = re.compile('[a-zA-Z][a-zA-Z0-9]*')

    @classmethod
    def _is_bidirectional(cls, s):
        """
        Determines if a reaction is bi-directional based on the symbol between the reactants and products.

        :param s: a string which is formatted according to our conventions

        :return: True or False
        """
        # parse out the directional symbol
        m = re.search(cls.direction_symbol_regex, s)
        if m:
            symbol = m.group(0)
            if (symbol[0] == '<') and (symbol[-1] == '>'):
                return True
            return False
        else:
            raise MalformattedReactionDirectionSymbolException('Check the directional symbol')

    @classmethod
    def check_symbol_name(cls, symbol):
        """
        Checks that a species symbol follows our formatting rules

        :param symbol: a string

        :return: None
        """
        m = re.match(cls.symbol_regex, symbol)
        if m is None or symbol != m.group():
            raise InvalidSymbolName('Symbol %s is not a valid symbol name.' % symbol)

    @classmethod
    def _parse_components(cls, s, element_class):
        """
        Parses a string representing one half of a reaction (e.g. the reactants on the left side) and returns
        a list of species.

        :param s: a string

        :return: a list of reaction_components.ReactionElement instances
        """
        element_dict = {}
        components = [x.strip() for x in s.split('+')]
        for c in components:
            coefficient = 1
            symbol = ''
            v = c.split('*')
            if len(v) == 1:
                symbol = v[0]
                cls.check_symbol_name(symbol)
            elif len(v) == 2:
                try:
                    coefficient = int(v[0])
                    symbol = v[1]
                    cls.check_symbol_name(symbol)
                except ValueError:
                    raise MalformattedReactionException('Equation component %s is not formatted correctly.' % c)
            else:
                raise MalformattedReactionException('Equation component %s is not formatted correctly.' % c)
            if symbol in element_dict:
                element_dict[symbol] += coefficient
            else:
                element_dict[symbol] = coefficient
        elements = []
        for symbol, coef in element_dict.items():
            elements.append(element_class(symbol, coef))
        return elements

    @classmethod
    def _parse_reaction(cls, reaction):
        """
        Parses the two sides (reactants and products) of a reaction string

        :param reaction: a string representation of a reaction in our syntax

        :return: a tuple of list objects.  The first entry is a list of Reactant instances and the second is a list
        of Product instances
        """
        try:
            lhs, rhs = [x.strip() for x in re.split(cls.direction_symbol_regex, reaction)]
            lhs_match = re.match(cls.equation_regex, lhs)
            rhs_match = re.match(cls.equation_regex, rhs)
            if lhs_match and rhs_match:
                if lhs_match.group() != lhs:
                    raise MalformattedReactionException("""
                        Left-hand side of equation %s was not formatted correctly""" % reaction)
                if rhs_match.group() != rhs:
                    raise MalformattedReactionException("""
                        Right-hand side of equation %s was not formatted correctly""" % reaction)
                # at this point we have valid lhs and rhs in terms of character content.  Still need to
                # ensure that the equation makes sense.
                reactants = cls._parse_components(lhs, Reactant)
                products = cls._parse_components(rhs, Product)
                return reactants, products

            else:
                raise MalformattedReactionException("""
                        Equation (%s) was not formatted correctly""" % reaction)
        except ValueError:
            raise MalformattedReactionException("""
                        Could not parse a left and right-hand side.
                        Check the directional symbol.
                        Equation was %s""" % reaction)

    @classmethod
    def parse(cls, expression_str):
        """
        This function parses an expression given in our defined syntax.  This includes the reaction string and the
        rate constants for the forward and reverse directions

        :param expression_str: a formatted string which gives the reaction

        :return: a 5-ple giving 1) a list of Reactant instances, 2) a list of Product instances, 3) a forward rate constant (float), 4) a reverse rate constant (float), and 5) a boolean indicating whether the reaction occurs in both directions.
        """

        # if the line was empty, just return a list of None's.
        if len(expression_str) == 0:
            return [None]*3

        # formatting requires a comma-separated list.  Strip whitespace
        contents = [x.strip() for x in expression_str.split(',')]
        contents = [x for x in contents if len(x) > 0]

        reaction_str = contents[0]

        # if there was only one item, we only have an reaction_str, but no rate constants
        if len(contents) < 2:
            raise MissingRateConstantException("""
                                                No rate constants were specified for
                                                line: %s
                                               """ % expression_str)

        # If the line had two items, then it could be a unidirectional reaction OR an error
        # due to a missing rate constant for the reverse reaction.
        # handle the rate constant logic here and bail out sooner before going through
        # more complex logic of parsing reactants/coefficients
        fwd_k,rev_k = 0.0, 0.0
        is_bidirectional = cls._is_bidirectional(reaction_str)
        if is_bidirectional:
            if len(contents) == 2:
                raise MissingRateConstantException("""
                                                No reverse rate constant was specified for
                                                line: %s
                                               """ % expression_str)
            if len(contents) >= 3:
                try:
                    fwd_k, rev_k = [float(x) for x in contents[1:3]]
                except ValueError as ex:
                    raise RateConstantFormatException('Could not parse the rate constants: %s' % ex.message)
        else:
            try:
                fwd_k = float(contents[1])
            except ValueError as ex:
                    raise RateConstantFormatException('Could not parse the rate constants: %s' % ex.message)
            if len(contents) > 2:
                # in this case, the rate constant was specified for a reverse reaction, but the arrow was only one
                # direction.  This could be a common mistake, so raise an exception
                raise ExtraRateConstantException(
                    """ A rate constant for the reverse reaction was specified.
                    However, the reaction was specified as occurring in a single direction.
                    Please check this.""")
            rev_k = 0.0

        # now parse the actual reaction string
        reactants, products = cls._parse_reaction(reaction_str)

        return reactants, products, fwd_k, rev_k, is_bidirectional
