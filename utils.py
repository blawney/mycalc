__author__ = 'brianlawney'
import os
import re
from reaction_components import Reaction, Reactant, Product


class FileSourceNotFound(Exception):
    pass


class NoReactionParser(Exception):
    pass


class MissingRateConstantException(Exception):
    pass


class RateConstantFormatException(Exception):
    pass


class ExtraRateConstantException(Exception):
    pass


class MalformattedReactionDirectionSymbolException(Exception):
    pass


class MalformattedReactionException(Exception):
    pass


class InvalidSymbolName(Exception):
    pass


class MalformattedReactionFileException(Exception):
    pass


class MissingInitialConditionsException(Exception):
    pass


class InvalidSimulationTimeException(Exception):
    pass


class InitialConditionGivenForMissingElement(Exception):
    pass


class ReactionErrorWithTrackerException(Exception):
    def __init__(self, error_index, detailed_message):
        self.error_index = error_index
        self.detailed_message = detailed_message


class Model(object):
    """
    Model should hold a ReactionParser object (abstract the handling of the source of reaction definitions
    Should also hold a list of Reactions
    """
    def __init__(self, reaction_factory):
        self._reactions = []
        self._reaction_factory = reaction_factory
        self.setup()

    def setup(self):
        self._reactions = self._reaction_factory.get_reactions()
        self.determine_all_elements()
        ic = self._reaction_factory.get_initial_conditions()
        if ic:
            self._initial_conditions = ic
        else:
            self._initial_conditions = dict(zip(self.all_elements, [0.0]*len(self.all_elements)))
        sim_time = self._reaction_factory.get_simulation_time()
        if sim_time:
            self._simulation_time = sim_time
        else:
            self._simulation_time = 0.0
        self.check_validity()

    def check_validity(self):
        # check that initial conditions are specified for species that are given in the equations
        if self._initial_conditions:
            for symbol in self._initial_conditions.keys():
                if symbol not in self.all_elements:
                    raise InitialConditionGivenForMissingElement('Symbol %s was not in your equations.' % symbol)

    def determine_all_elements(self):
        all_symbols = set()
        for rx in self._reactions:
            all_symbols = all_symbols.union(set(rx.get_all_elements()))
        self.all_elements = all_symbols

    def set_initial_conditions(self, ic):
        self._initial_conditions = ic
        self.check_validity()

    def set_simulation_time(self, t):
        try:
            t = float(t)
            if t > 0:
                self._simulation_time = t
            else:
                raise InvalidSimulationTimeException('Simulation time must be a positive number')
        except ValueError:
            raise InvalidSimulationTimeException('Could not interpret the simulation time as a number.')

    def get_all_elements(self):
        return self.all_elements

    def get_reactions(self):
        return self._reactions

    def get_initial_conditions(self):
        return self._initial_conditions

    def get_simulation_time(self):
        return self._simulation_time

    def __str__(self):
        s = ''
        for rx in self._reactions:
            s += '%s\n' % rx
        s += 'Initial conditions: %s' % self._initial_conditions
        s += '\n%s' % self._simulation_time
        return s


class ReactionFactory(object):

    def get_reactions(self):
        raise NotImplementedError


class GUIReactionFactory(ReactionFactory):

    def __init__(self, reaction_strings_dict):
        self.expression_parser = StringExpressionParser
        self.reaction_strings_dict = reaction_strings_dict
        reactions = []
        for idx, rx in self.reaction_strings_dict.items():
            try:
                reactions.append(self.create_reaction(rx))
            except Exception as ex:
                raise ReactionErrorWithTrackerException(idx, ex.message)
        self.reaction_list = reactions

    def create_reaction(self, reaction_expression):
        reactants, products, fwd_k, rev_k, is_bidirectional = self.expression_parser.parse(reaction_expression)
        return Reaction(reactants, products, fwd_k, rev_k, is_bidirectional)

    def get_reactions(self):
        return self.reaction_list

    def get_initial_conditions(self):
        return None

    def get_simulation_time(self):
        return None



class FileReactionFactory(ReactionFactory):

    REACTION_DELIMITER = '#REACTIONS'
    IC_DELIMITER = '#INITIAL_CONDITIONS'
    TIME_DELIMITER = '#TIME'

    def __init__(self, filepath):
        self.expression_parser = StringExpressionParser
        if os.path.isfile(filepath):
            self.reaction_file = filepath
            self.read_source()
        else:
            raise FileSourceNotFound('File could not be found at %s' % filepath)

    def read_source(self):
        contents = open(self.reaction_file).read()

        # parse out the reactions:
        reaction_section_pattern = '(?:%s)(.*)(?:%s)' % ((FileReactionFactory.REACTION_DELIMITER,)*2)
        m = re.search(reaction_section_pattern, contents, flags=re.DOTALL)
        if m:
            eqn_list = [x.strip() for x in m.group(1).strip().split('\n')]
            reactions = []
            for eqn in eqn_list:
                if len(eqn) > 0:
                    reactions.append(self.create_reaction(eqn))
            if len(reactions) == 0:
                raise MalformattedReactionFileException('Could not parse any reactions from the input file.')
            self.reaction_list = reactions
        else:
            raise MalformattedReactionFileException('Could not parse any reactions from the file. Check that.')

        # parse out the initial conditions:
        ic_section_pattern = '(?:%s)(.*)(?:%s)' % ((FileReactionFactory.IC_DELIMITER,)*2)
        m = re.search(ic_section_pattern, contents, flags=re.DOTALL)
        if m:
            ic_list = [x.strip() for x in m.group(1).strip().split('\n')]
            initial_conditions = {}
            for ic in ic_list:
                if len(ic) > 0:
                    try:
                        symbol, c0 = [x.strip() for x in ic.split('=')]
                        initial_conditions[symbol] = float(c0)
                    except ValueError as ex:
                        raise MalformattedReactionFileException("""
                            The initial condition for symbol %s is not valid""" %  symbol)
            if len(initial_conditions.keys()) > 0:
                self._initial_conditions = initial_conditions
            else:
                raise MissingInitialConditionsException("""
                    Could not parse any initial conditions from the file. Check that.""")
        else:
            raise MissingInitialConditionsException("""
                    Could not parse any initial conditions from the file. Check that.""")

        # parse out the simulation time length (optional parameter)
        time_section_pattern = '(?:%s)(.*)(?:%s)' % ((FileReactionFactory.TIME_DELIMITER,)*2)
        m = re.search(time_section_pattern, contents, flags=re.DOTALL)
        if m:
            try:
                t = float(m.group(1).strip())
                if t > 0:
                    self._simulation_time = t
                else:
                    raise InvalidSimulationTimeException('The simulation time must be a positive number.')
            except ValueError:
                raise InvalidSimulationTimeException('The simulation time was not a valid number.')
        else:
            self._simulation_time = 15.0
            #TODO: parameterize this above.


    def create_reaction(self, reaction_expression):
        reactants, products, fwd_k, rev_k, is_bidirectional = self.expression_parser.parse(reaction_expression)
        return Reaction(reactants, products, fwd_k, rev_k, is_bidirectional)

    def get_reactions(self):
        return self.reaction_list

    def get_initial_conditions(self):
        print 'calling for ICs'
        return self._initial_conditions

    def get_simulation_time(self):
        return self._simulation_time


class ExpressionParser(object):
    pass


class StringExpressionParser(ExpressionParser):

    direction_symbol_regex = re.compile('<?[-]+>')
    equation_regex = re.compile('[a-zA-Z0-9\+\s\*]+')
    symbol_regex = re.compile('[a-zA-Z][a-zA-Z0-9]*')

    @classmethod
    def _is_bidirectional(cls, s):
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
        m = re.match(cls.symbol_regex, symbol)
        if m is None or symbol != m.group():
            raise InvalidSymbolName('Symbol %s is not a valid symbol name.' % symbol)

    @classmethod
    def _parse_components(cls, s, element_class):
        """
        s is a string representing a 'side' of an equation
        :param s:
        :return:
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
    def _parse_equation(cls, equation):
        try:
            lhs, rhs = [x.strip() for x in re.split(cls.direction_symbol_regex, equation)]
            lhs_match = re.match(cls.equation_regex, lhs)
            rhs_match = re.match(cls.equation_regex, rhs)
            if lhs_match and rhs_match:
                if (lhs_match.group() != lhs):
                    raise MalformattedReactionException("""
                        Left-hand side of equation %s was not formatted correctly""" % equation)
                if (rhs_match.group() != rhs):
                    raise MalformattedReactionException("""
                        Right-hand side of equation %s was not formatted correctly""" % equation)
                # at this point we have valid lhs and rhs in terms of character content.  Still need to
                # ensure that the equation makes sense.
                reactants = cls._parse_components(lhs, Reactant)
                products = cls._parse_components(rhs, Product)
                return reactants, products

            else:
                raise MalformattedReactionException("""
                        Equation (%s) was not formatted correctly""" % equation)
        except ValueError:
            raise MalformattedReactionException("""
                        Could not parse a left and right-hand side.
                        Check the directional symbol.
                        Equation was %s""" % equation)

    @classmethod
    def parse(cls, expression_str):

        # if the line was empty, just return a list of None's.
        if len(expression_str) == 0:
            return [None]*3

        # formatting requires a comma-separated list.  Strip whitespace
        contents = [x.strip() for x in expression_str.split(',')]
        contents = [x for x in contents if len(x) > 0]

        equation = contents[0]

        # if there was only one item, we only have an equation, but no rate constants
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
        is_bidirectional = cls._is_bidirectional(equation)
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

        reactants, products = cls._parse_equation(equation)

        return reactants, products, fwd_k, rev_k, is_bidirectional


