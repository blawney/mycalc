__author__ = 'brian'

from custom_exceptions import *


class Model(object):
    """
    This class is responsible for maintaining information about the reactions and initial conditions.
    """
    DEFAULT_SIMULATION_TIME = 30.0

    def __init__(self, reaction_factory):
        """
        To instantiate a Model, we must supply a source, which is a derived class of ReactionFactory.
        The reaction factory provides the necessary information to build a Model
        :param reaction_factory: an instance of type ReactionFactory
        :return: None
        """
        self._reactions = []
        self._reaction_factory = reaction_factory
        self._setup()

    def _setup(self):
        """
        Initiates the Model instance by requesting the reactions, initial conditions, and simulation time from the factory
        :return: None
        """
        self._reactions = self._reaction_factory.get_reactions()
        self._determine_all_species()
        ic = self._reaction_factory.get_initial_conditions()

        # if the reaction factory had initial conditions, read them.
        # Otherwise, set all to zero.
        if ic:
            self._initial_conditions = ic
        else:
            self._initial_conditions = dict(zip(self._all_species, [0.0]*len(self._all_species)))
        sim_time = self._reaction_factory.get_simulation_time()
        if sim_time:
            self._simulation_time = sim_time
        else:
            self._simulation_time = Model.DEFAULT_SIMULATION_TIME
        self._check_initial_condition_validity()

    def _check_initial_condition_validity(self):
        """
        Ensures that sensible initial conditions were specified.  Checks that the initial conditions are only given
        for species that are in the set of reactions.  Also checks that they are >0 since we are modeling
        concentrations.  Some of the checks here are possibly redundant,
        :return: None
        """
        if self._initial_conditions:
            for symbol in self._initial_conditions.keys():
                if symbol not in self._all_species:
                    raise InitialConditionGivenForMissingElement('Symbol %s was not in your equations.' % symbol)
                try:
                    c0 = float(self._initial_conditions[symbol])
                    if c0 < 0:
                        raise InvalidInitialConditionException('Initial condition error- cannot be < 0')
                except ValueError:
                    raise InvalidInitialConditionException('Could not parse initial condition as a number.')

    def _determine_all_species(self):
        """
        Reads through all the reactions to determine a exhaustive set of the constituent species
        :return: None
        """
        all_symbols = set()
        for rx in self._reactions:
            all_symbols = all_symbols.union(set(rx.get_all_species()))
        self._all_species = all_symbols

    def set_initial_conditions(self, ic):
        """
        Allows reset of the initial conditions
        :param ic: a one-to-one dictionary of species (keys) mapping to initial concentrations (floats)
        :return: None
        """
        self._initial_conditions = ic
        self._check_initial_condition_validity()

    def set_simulation_time(self, t):
        """
        Allows set/reset of the simulation time
        :param t: A float, greater than zero
        :return: None
        """
        try:
            t = float(t)
            if t > 0:
                self._simulation_time = t
            else:
                raise InvalidSimulationTimeException('Simulation time must be a positive number')
        except ValueError:
            raise InvalidSimulationTimeException('Could not interpret the simulation time as a number.')

    def get_all_species(self):
        """
        Returns all the species in the model
        :return: A set of strings which give the species' symbols
        """
        return self._all_species

    def get_reactions(self):
        """
        Returns all the reactions in this Model instance
        :return: A list of Reaction instances
        """
        return self._reactions

    def get_initial_conditions(self):
        """
        Get the initial conditions set on the current Model instance
        :return: A dictionary (one-to-one) of species symbol (string) mapping to initial concentration (float)
        """
        return self._initial_conditions

    def get_simulation_time(self):
        """
        Get the current length of the simulation (in seconds)
        :return: A float, giving the simulation length in seconds
        """
        return self._simulation_time

    def __str__(self):
        """
        The string representation of the Model class
        :return: a string
        """
        s = ''
        for rx in self._reactions:
            s += '%s\n' % rx
        s += 'Initial conditions: %s' % self._initial_conditions
        s += '\n%s' % self._simulation_time
        return s