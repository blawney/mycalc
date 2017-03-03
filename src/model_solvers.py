__author__ = 'brianlawney'

import numpy as np
from scipy import integrate


class Solver(object):
    """
    A base class for general solvers we might create to solve for the equilibrium state.

    Contains methods that are likely to be useful to derived classes.

    Instantiate a derived class, not this one.
    """

    def __init__(self):
        raise NotImplementedError

    def _create_species_mapping(self):
        """
        Creates a dictionary that maps the species (symbols) to an integer index.  That index is used to
        locate the species in the matrix algebra.

        At the end of the calculations, we will typically have an array of floats, and the dictionary this creates
        is necessary to map the time evolutions to a particular species

        :return: None
        """
        species_set = set()
        for rx in self.model.get_reactions():
            species_set = species_set.union(rx.get_all_species())
        sorted_species = sorted(list(species_set))
        self.species_mapping = dict(zip(sorted_species, range(len(sorted_species))))

    def _setup_initial_conditions(self):
        """
        Creates a numPy array which contains the initial conditions.  The initial concentrations of the species are
        located in the array via the species-to-index map that was created in Solver._create_species_mapping
        :return: None
        """

        ic_from_model = self.model.get_initial_conditions()
        initial_conditions = np.zeros(len(self.species_mapping.keys()))
        for symbol, index in self.species_mapping.items():
            # species_mapping maps the symbol to the index of the concentration array
            if symbol in ic_from_model:
                initial_conditions[index] = ic_from_model[symbol]
            else:
                initial_conditions[index] = 0.0
        self.initial_conditions = initial_conditions

    def equilibrium_solution(self):
        raise NotImplementedError


class ODESolver(Solver):
    """
    This solver was the first implementation and did not explicitly calculate a Jacobian

    Assumes that the rate constants and initial conditions are fixed, so this class is not suitable for use in
    performing curve-fitting operations (e.g. fitting rate constants).
    """

    def __init__(self, model):
        self.model = model
        self._create_species_mapping()
        self._create_stoichiometry_matrix()
        self.rate_funcs = self._calculate_rate_law_funcs(self.model.get_reactions())
        self._setup_initial_conditions()

    def _create_stoichiometry_matrix(self):
        """
        This creates the stoichiometry (N) matrix and sets it as an attribute.
        Iterates through the reactions and fills in the matrix entries as appropriate

        :return:
        """
        reactions = self.model.get_reactions()
        N1 = np.zeros((len(self.species_mapping.keys()), len(reactions)))
        for j, rx in enumerate(reactions):
            for r in rx.get_reactants():
                N1[self.species_mapping[r.symbol], j] = -1*r.coefficient
            for p in rx.get_products():
                N1[self.species_mapping[p.symbol], j] = p.coefficient
        self.N = np.hstack([N1, -N1])

    def _calculate_rate_law_funcs(self, reactions):
        """
        This method sets up a list of functions which is used to calculate the time rate-of-change of the concentrations
        in the system of coupled differential equations.

        The idea here is leverage closures to create a list of functions (one for each equation, both forward and rev)
        up front.  Since no rate constants change in this model, these functions are created only once.
        For the single-direction equations, the reverse rate constant is already set to zero and falls out

        Due to the closure bindings
        (discussed here: http://stackoverflow.com/questions/233673/lexical-closures-in-python )
        this ends up looking a bit more involved.
        :param reactions: A list of reaction_components.Reaction objects
        :return: A list of functions (callables) which are used in calculating the time rate-of-change of the
        concentrations
        """

        # a list to hold the functions
        rate_funcs = 2*len(reactions)*[None]

        for i, rx in enumerate(reactions):

            # this keeps track of the index (where the species 'lives' in the array of concentrations) and
            # the coefficient, which becomes the exponent due to law of mass action.
            def rate_generator_func(species_idx_and_coef_map, k):
                def f(X):
                    rate = k
                    for idx, power in species_idx_and_coef_map.items():
                        rate *= X[idx]**power
                    return rate
                return f

            for j, element_list in enumerate([rx.get_reactants(), rx.get_products()]):
                idx_and_coef = {}
                for r in element_list:
                    index = self.species_mapping[r.symbol]
                    idx_and_coef[index] = r.coefficient
                rate_const = rx.get_fwd_k() if j == 0 else rx.get_rev_k()
                rate_funcs[i+j*len(reactions)] = rate_generator_func(idx_and_coef, rate_const)

        return rate_funcs

    def _dX_dt(self, X, t=0):
        """
        Computes the time rate-of-change of the concentration array.  To be used by an iterative solver such as
        scipy.integrate.odeint

        :param X: a numPy array of the current concentrations (floats)
        :param t: a float representing time.  Generally not used since we have autonomous equations
        :return: a numPy array giving the current time rate of change of the concentrations.
        """
        rate_vals = np.array([f(X) for f in self.rate_funcs])
        return np.dot(self.N, rate_vals)

    def equilibrium_solution(self):
        """
        Runs the integration to determine the equilibrium state
        :return: a 3-tuple consisting of the species-to-index map, a numPy array giving the evolution of each species
        in the columns, and an array of the time steps.
        """
        tmax = self.model.get_simulation_time()
        t = np.linspace(0, tmax, 100000)
        X = integrate.odeint(self._dX_dt, self.initial_conditions, t)
        return self.species_mapping, X, t


class ODESolverWJacobian(Solver):

    def __init__(self, model):

        self.model = model
        self._create_species_mapping()
        self._get_rate_constants()
        self._create_coefficient_arrays()
        self._setup_initial_conditions()

    def _get_rate_constants(self):
        """
        Extract the rate constants from the model specification and build an array of rate constants.
        Note the placement of the rate constants to match the derivation--
        If there are J reactions, then the total array has length 2J.  The forward rate constant of reaction q goes
        in kvals[q] and the reverse reaction rate constant goes in kvals[q+J]

        :return: None
        """

        all_reactions = self.model.get_reactions()

        # set the member attribute J- the number of reactions
        self.J = len(all_reactions)

        self.kvals = np.zeros(2*self.J)
        for i, rx in enumerate(all_reactions):
            self.kvals[i] = rx.get_fwd_k()
            self.kvals[i+self.J] = rx.get_rev_k()

    def _create_coefficient_arrays(self):
        """
        Creates the alpha and gamma matrices (M x J) given in the derivation of the model system.
        Also sets the member attribute Z, which is the difference gamma-alpha
        :return: None
        """

        # The number of species and the number of equations
        self.M = len(self.species_mapping.keys())

        # alpha and gamma refer to the documentation nomenclature
        # both (M x J) matrices describing the stoichiometric coefficients
        self.alpha = np.zeros((self.M, self.J))
        self.gamma = np.zeros((self.M, self.J))

        for q, rx in enumerate(self.model.get_reactions()):
            for reactant in rx.get_reactants():
                self.alpha[self.species_mapping[reactant.symbol], q] = reactant.coefficient
            for product in rx.get_products():
                self.gamma[self.species_mapping[product.symbol], q] = product.coefficient
        # the sum of -alpha and gamma ends up being something we use a lot, so calculate the difference up front:
        self.Z = self.gamma - self.alpha

    def _dX_dt(self, X, t=None, k=None):
        """
        Computes the time rate-of-change of the concentration array.  To be used by an iterative solver such as
        scipy.integrate.odeint

        :param X: a numPy array of the current concentrations (floats)
        :param t: a float representing time.  Generally not used since we have autonomous equations
        :param k: a numPy array of rate constants (floats)
        :return: a numPy array giving the current time rate of change of the concentrations.
        """

        theta = np.prod(X[np.newaxis,:]**(self.alpha.T), axis=1)
        phi = np.prod(X[np.newaxis,:]**(self.gamma.T), axis=1)

        if k is None:
            k = self.kvals

        # a J-length array
        c_vector = k[:self.J]*theta - k[self.J:]*phi

        return np.dot(self.Z, c_vector)

    def _jacobian(self, X, t=None, k=None):
        """
        Computes the Jacobian given the current state vector and rate constants.  This method is not used directly,
        but by the iterative solvers such as scipy.integrate.odeint

        :param X: A numPy array of the current concentrations (floats)
        :param t: A float representing time.  Generally not used
        :param k: A numPy array of rate constants (floats)
        :return: A square numPy matrix which is the Jacobian

        """

        # this section takes care of calculating the (J x M) matrices for the product terms in our Jacobian formula.
        theta_exponent_array = []
        phi_exponent_array = []

        # Here, progressively build a list of numPy matrices where a single column is zero'd out.
        # This helps to gracefully deal with the i=/=s condition in the product terms.
        for i in range(self.M):
            alpha_edit = np.copy(self.alpha.T)
            gamma_edit = np.copy(self.gamma.T)
            alpha_edit[:, i] = 0
            gamma_edit[:, i] = 0
            theta_exponent_array.append(alpha_edit)
            phi_exponent_array.append(gamma_edit)

        # make the lists into 3-D numPy arrays.  Dimension is (M,J,M)
        theta_exponent_array = np.array(theta_exponent_array)
        phi_exponent_array = np.array(phi_exponent_array)

        # Broadcasting the exponent- gives the actual product terms given in the formula.  Results are (J x M) matrices
        theta = np.prod(X**theta_exponent_array, axis=2).T
        phi = np.prod(X**phi_exponent_array, axis=2).T

        # Creates (J x M) matrices for the terms created from the differentiation (hence the -1)
        chi_l = X**(self.alpha.T-1)
        chi_r = X**(self.gamma.T-1)

        if k is None:
            k = self.kvals

        # Perform element-wise multiplication of all the terms
        V = k[:self.J, np.newaxis] * (self.alpha.T) * chi_l * theta -\
            k[self.J:, np.newaxis] * (self.gamma.T) * chi_r * phi
        return np.dot(self.Z, V)

    def equilibrium_solution(self, X0=None, k=None):
        """
        Runs the integration to determine the equilibrium state

        :param X0: (optional) A dictionary mapping the symbols to the initial concentrations
        :param k: (optional) An array of rate constants.
        :return: a 3-tuple consisting of the species-to-index map, a numPy array giving the evolution of each species
        in the columns, and an array of the time steps.

        Note that it's important that the array of rate constants is ordered in our convention.  Printing the
        model object is one way to check the order of the reactions so that the rate constants can be arranged
        in the proper order.
        """
        if X0 is not None:
            # if another set of initial conditions (different from that specified in the model file)
            # is given, we ensure they're valid by using the method models.Model.set_initial_conditions
            # then we reset our initial conditions in the solver.  This ensures that 1) approriate initial conditions
            self.model.set_initial_conditions(X0)
            self._setup_initial_conditions()

        tmax = self.model.get_simulation_time()
        t = np.linspace(0, tmax, 100000)
        X = integrate.odeint(self._dX_dt, self.initial_conditions, t, args=(k,), Dfun=self._jacobian)
        return self.species_mapping, X, t
