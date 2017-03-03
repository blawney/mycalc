__author__ = 'brian'

import re
import os

from custom_exceptions import *
import parsers
from reaction_components import Reaction, Reactant, Product


class ReactionFactory(object):
    """
    A base class to derive from.  Derived children of ReactionFactory should provide a mechanism to ingest information
    and create Reaction instances to populate a Model.
    """

    def get_reactions(self):
        raise NotImplementedError

    def get_initial_conditions(self):
        raise NotImplementedError

    def get_simulation_time(self):
        raise NotImplementedError


class GUIReactionFactory(ReactionFactory):
    """
    A class for obtaining a model specification via a GUI
    """

    def __init__(self, reaction_strings_dict):
        """
        :param reaction_strings_dict: a dictionary with integer keys mapping to strings, which are formatted in our
         specified reaction syntax. The integer index provides a way to inform GUI users which reaction was improperly
         formatted.

        :return: None
        """
        self.expression_parser = parsers.StringExpressionParser
        self.reaction_strings_dict = reaction_strings_dict
        reactions = []
        for idx, rx in self.reaction_strings_dict.items():
            try:
                reactions.append(self._create_reaction(rx))
            except Exception as ex:
                raise ReactionErrorWithTrackerException(idx, ex.message)
        self._reaction_list = reactions

    def _create_reaction(self, reaction_expression):
        """
        Creates a Reaction object given a formatted reaction string

        :param reaction_expression: a string, formatted in the specified reaction syntax

        :return: a new Reaction instance
        """
        reactants, products, fwd_k, rev_k, is_bidirectional = self.expression_parser.parse(reaction_expression)
        return Reaction(reactants, products, fwd_k, rev_k, is_bidirectional)

    def get_reactions(self):
        """
        Gets a list of the Reaction objects

        :return: a list of Reaction instances
        """
        return self._reaction_list

    def get_initial_conditions(self):
        """
        Get the initial conditions.  Due to the GUI setup,we do not necessarily have this information.  It can be
        specified via the GUI at a later step in the workflow

        :return: None
        """
        return None

    def get_simulation_time(self):
        """
        Get the simulation time.  Due to the GUI setup,we do not necessarily have this information.  It can be
        specified via the GUI at a later step in the workflow

        :return: None
        """
        return None


class FileReactionFactory(ReactionFactory):
    """
    A class for reading reactions from a specially formatted file
    """

    # some delimiters to distinguish the different sections in the file
    REACTION_DELIMITER = '#REACTIONS'
    IC_DELIMITER = '#INITIAL_CONDITIONS'
    TIME_DELIMITER = '#TIME'

    def __init__(self, filepath):
        """
        Creates the FileReactionFactory instance

        :param filepath: a string giving the path to a reaction file

        :return: None
        """
        self._expression_parser = parsers.StringExpressionParser
        if os.path.isfile(filepath):
            self.reaction_file = filepath
            self._read_source()
        else:
            raise FileSourceNotFound('File could not be found at %s' % filepath)

    def _read_source(self):
        """
        This method does the work of reading through the file and parsing out the sections for reactions, initial
        conditions, etc. The actual parsing of reactions is performed by the wrapped ExpressionParser instance

        :return: None
        """
        contents = open(self.reaction_file).read()

        # parse out the reactions:
        reaction_section_pattern = '(?:%s)(.*)(?:%s)' % ((FileReactionFactory.REACTION_DELIMITER,)*2)
        m = re.search(reaction_section_pattern, contents, flags=re.DOTALL)
        if m:
            eqn_list = [x.strip() for x in m.group(1).strip().split('\n')]
            reactions = []
            for eqn in eqn_list:
                if len(eqn) > 0:
                    reactions.append(self._create_reaction(eqn))
            if len(reactions) == 0:
                raise MalformattedReactionFileException('Could not parse any reactions from the input file.')
            self._reaction_list = reactions
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
                        c0 = float(c0)
                        if c0 > 0:
                            initial_conditions[symbol] = c0
                        else:
                            raise InvalidInitialConditionException('Initial condition must be >= 0 (since a concentration)')
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
            self._simulation_time = None

    def _create_reaction(self, reaction_expression):
        """
        Creates a Reaction object given a formatted reaction string

        :param reaction_expression: a string, formatted in the specified reaction syntax

        :return: a new Reaction instance
        """
        reactants, products, fwd_k, rev_k, is_bidirectional = self._expression_parser.parse(reaction_expression)
        return Reaction(reactants, products, fwd_k, rev_k, is_bidirectional)

    def get_reactions(self):
        """
        Get the reactions from this factory

        :return: a list of Reaction instances
        """
        return self._reaction_list

    def get_initial_conditions(self):
        """
        Get the initial conditions from the file

        :return: a one-to-one dictionary of species symbols mapped to floats
        """
        return self._initial_conditions

    def get_simulation_time(self):
        """
        Gets the simulation time specified in the file.  If this was not given in the file, it will end up returning
        None

        :return: float or None
        """
        return self._simulation_time
