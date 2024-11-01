"""
Contains calculation approaches for all factors
"""

class Factor():

    def __init__(self, factor_type=None):

        self.factor_type = factor_type

    def __str__(self):
        return self.factor_type




class Beta(Factor):
    ...

