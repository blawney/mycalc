__author__ = 'brianlawney'

import numpy as np
from scipy import integrate

class Solver(object):

    def __init__(self):
        raise NotImplementedError


class ODESolver(Solver):
    def __init__(self, model):
        self.model = model
        self.create_species_mapping()
        self.create_stoichiometry_matrix()
        self.rate_funcs = self.calculate_rate_law_funcs(self.model.get_reactions())
        self.setup_initial_conditions()

    def setup_initial_conditions(self):
        ic_from_model = self.model.get_initial_conditions()
        initial_conditions = np.zeros(len(self.species_mapping.keys()))
        for symbol, index in self.species_mapping.items():
            # species_mapping maps the symbol to the index of the concentration array
            if symbol in ic_from_model:
                initial_conditions[index] = ic_from_model[symbol]
            else:
                initial_conditions[index] = 0.0
        self.initial_conditions = initial_conditions


    def create_species_mapping(self):
        species_set = set()
        for rx in self.model.get_reactions():
            species_set = species_set.union(rx.get_all_elements())
        sorted_species = sorted(list(species_set))
        self.species_mapping = dict(zip(sorted_species, range(len(sorted_species))))

    def create_stoichiometry_matrix(self):
        reactions = self.model.get_reactions()
        N1 = np.zeros((len(self.species_mapping.keys()), len(reactions)))
        for j, rx in enumerate(reactions):
            for r in rx.get_reactants():
                N1[self.species_mapping[r.symbol],j] = -1*r.coefficient
            for p in rx.get_products():
                N1[self.species_mapping[p.symbol],j] = p.coefficient
        self.N = np.hstack([N1, -N1])

    def calculate_rate_law_funcs(self, reactions):
        """
        reaction is a Reaction instance
        The idea here is leverage closures to create a list of functions (one for each equation, both fwd and rev)
        Finally, that list of functions is added (via closure mechanism) to a function that takes only the array
         of current concentrations.  From that, it is able to return the array of rate constants (given the current
         state) for each loop of the ode solver.

         Due to the closure bindings
         (discussed here: http://stackoverflow.com/questions/233673/lexical-closures-in-python )
         this ends up being a bit of a mess.
        """
        # create a function for each reaction, both fwd and reverse.  For the single-direction equations, the reverse
        # rate constant is already set to zero, so it just falls out in the final system anyway
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
                rate_const = rx.get_fwd_k() if j==0 else rx.get_rev_k()
                rate_funcs[i+j*len(reactions)] = rate_generator_func(idx_and_coef, rate_const)

        return rate_funcs

    def dX_dt(self, X, t=0):
        rate_vals = np.array([f(X) for f in self.rate_funcs])
        return np.dot(self.N, rate_vals)

    def equilibrium_solution(self):
        tmax = self.model.get_simulation_time()
        print 'solve: tmax=%s' % tmax
        t = np.linspace(0, tmax, 100000)
        X = integrate.odeint(self.dX_dt, self.initial_conditions, t)
        return self.species_mapping, X, t


