__author__ = 'brianlawney'


class Reaction(object):
    """
    This class holds all the components of a reaction- the constitutive species, rate constants, the direction
    of reaction
    """
    def __init__(self,
                 reactants,
                 products,
                 fwd_k,
                 rev_k=None,
                 is_bidirectional=False):
        """

        :param reactants: A list of Reactant instances

        :param products:
        :param fwd_k:
        :param rev_k:
        :param is_bidirectional:
        :return:
        """

        self._reactant_list = reactants
        self._product_list = products
        self._fwd_k = fwd_k
        self._rev_k = rev_k
        self.is_bidirectional = is_bidirectional

    def get_reactants(self):
        return self._reactant_list

    def get_products(self):
        return self._product_list

    def get_fwd_k(self):
        return self._fwd_k

    def get_rev_k(self):
        return self._rev_k

    def is_bidirectional_reaction(self):
        return self.is_bidirectional

    def get_all_species(self):
        """
        A set of the symbols (Strings)
        :return:
        """
        species_set = set()
        for r in self._reactant_list:
            species_set.add(r.symbol)
        for r in self._product_list:
            species_set.add(r.symbol)
        return species_set

    def reactant_str(self):
        return '+'.join([' %s ' %x for x in self._reactant_list])

    def product_str(self):
        return '+'.join([' %s ' %x for x in self._product_list])

    def __str__(self):
        reactant_str = '+'.join([' %s ' %x for x in self._reactant_list])
        product_str = '+'.join([' %s ' %x for x in self._product_list])
        if self._rev_k is not None:
            return '%s <--%s, %s--> %s' % (reactant_str, self._rev_k, self._fwd_k, product_str)
        else:
            return '%s --%s--> %s' % (reactant_str, self._fwd_k, product_str)


class ReactionElement(object):
    def __init__(self,
                 symbol,
                 coefficient,
                 verbose_name=''):
        self.symbol = symbol
        self.coefficient = coefficient
        self.verbose_name = verbose_name

    def __str__(self):
        s = ''
        if self.coefficient > 1:
            s = '%s*' % self.coefficient
        s += self.symbol
        return s

    def __eq__(self, other):
        return (self.symbol == other.symbol) & (self.coefficient == other.coefficient)


class Reactant(ReactionElement):

    def __init__(self, symbol, coefficient, verbose_name=''):
        super(Reactant, self).__init__(symbol, coefficient, verbose_name)


class Product(ReactionElement):

    def __init__(self, symbol, coefficient, verbose_name=''):
        super(Product, self).__init__(symbol, coefficient, verbose_name)
