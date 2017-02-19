__author__ = 'brianlawney'


class Reaction(object):
    def __init__(self,
                 reactants,
                 products,
                 fwd_k,
                 rev_k=None):

        self._reactant_list = reactants
        self._product_list = products
        self._fwd_k = fwd_k
        self._rev_k = rev_k

    def get_reactants(self):
        return self._reactant_list

    def get_products(self):
        return self._product_list

    def get_fwd_k(self):
        return self._fwd_k

    def get_rev_k(self):
        return self._rev_k

    def get_all_elements(self):
        """
        A set of the symbols (Strings)
        :return:
        """
        element_set = set()
        for r in self._reactant_list:
            element_set.add(r.symbol)
        for r in self._product_list:
            element_set.add(r.symbol)
        return element_set

    def __str__(self):
        reactant_str = '+'.join([' %s ' %x for x in self.reactant_list])
        product_str = '+'.join([' %s ' %x for x in self.product_list])
        if self.rev_k:
            return '%s <--%s, %s--> %s' % (reactant_str, self.fwd_k, self.rev_k, product_str)
        else:
            return '%s --%s--> %s' % (reactant_str, self.fwd_k, product_str)


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
