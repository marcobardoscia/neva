"""Collection of banks constituing a banking system.
"""

from __future__ import division
import collections
from .bank import Bank


class BankingSystem(object):
    """Collection of banks.
    
    This container allows to perform operations that require access to data of
    all banks, such as checking the consistency of interbank assets and 
    liabilities and, more importantly, to compute the equity as a fixed-point 
    of an iterative map.

    Individual banks can be accessed either using `Bank`s objects: 

    >>> import bank
    >>> bank_a = bank.Bank(name='A')
    >>> bank_b = bank.Bank(name='B')
    >>> import bankingsystem
    >>> b_system = bankingsystem.BankingSystem([bank_a, bank_b])
    >>> b_system.banks[bank_a].name
    'A' 

    or by using indices. Banks are ordered as in the sequence passed to the
    `BankingSystem` constructor.

    >>> b_system[1].name
    'B'

    Finally banks can be accessed by name:
    
    >>> b_system.banksbyname[bank_b.name].name
    'B'

    `BankingSystem` also allows order-preserving iteration over banks:

    >>> for bank in b_system:
    >>>     print(bank.name)
    >>> 'A'
    >>> 'B' 

    Attributes:
        banks (OrderedDict of `Bank` : `Bank`): access to `Bank`s by `Bank`
        banksbyid (OrderedDict of int : `Bank`): access to `Bank`s by index
        banksbyname (OrderedDict of str : `Bank`): access to `Bank`s by `Bank.name`                      
        nbanks (int): number of banks
        tol (float): error tolerance for the convergence of the iterative map
        maxiter (int): maximum number of iterations of the iterative map 
        history (list): each element of the list is a list the equities of all 
                        banks, from the starting point until convergence
    """
    def __init__(self, banks, tol=0.001, maxiter=100, save_history=False):
        """Create a banking system.
        
        Parameters:
            banks (sequence): banks to be included in the banking system
            tol (float): error tolerance for the convergence of the iterative 
                         map
            maxiter (int): maximum number of iterations of the iterative map 
            save_history (bool): if `True` saves all the equities from the 
                                 starting point until convergence
        """
        if not isinstance(banks, (list, tuple)):
            raise TypeError
        for item in banks:
            if not isinstance(item, Bank):
                raise TypeError
        self.banks = collections.OrderedDict()
        self.banksbyid = collections.OrderedDict()
        self.banksbyname = collections.OrderedDict()
        for bidx, bnk in enumerate(banks):
            self.banks[bnk] = bnk
            self.banksbyid[bidx] = bnk
            self.banksbyname[bnk.name] = bnk
        self.set_equity(self.get_naiveequity())
        self.nbanks = len(banks)
        self.tol = tol
        self.maxiter = maxiter
        self.set_history(save_history)
        
    @classmethod
    def _from_bankingsystem(cls, banks, bnksys):
        """Creates a banking system using banks from a list of banks and using
        parameters from another banking system.
        
        Parameters:
            banks (sequence of `Bank`): sequence of banks
            bnksys (`BankingSystem`): banking system object
        Note:
            Low-level method used by the derived classes of `BankingSystem`, 
            do not call it explicitly.
        """
        # recreating ibassets for new banks
        for new_lender in banks:
            old_lender = bnksys.banksbyname[new_lender.name]
            for old_borrower, amount in old_lender.ibasset:
                for new_borrower in banks:
                    if new_borrower.name == old_borrower.name:
                        new_lender.ibasset.append( (new_borrower, amount) )
        # new banking system
        return cls(banks, bnksys.tol, bnksys.maxiter, bnksys.save_history)

    def __getitem__(self, idx):
        """Return banks accessed via index.
        
        Parameters:
            idx (int): index of the bank.
        """
        return self.banksbyid[idx]

    def __iter__(self):
        """Return iterator over banks."""
        return iter(self.banks)

    def validate_ibasset(self):
        """Check that interbank assets and liabilities are consistent.
        
        For each bank the value of its total interbank liabilities must be 
        equal to the sum of all interbank assets corresponding to loans issued
        by all the other banks towards the bank under consideration.
        """
        ibliabtot = collections.OrderedDict()
        for bnk in self.banks:
            ibliabtot[bnk] = 0.0
        for lender in self.banks:
            for borrower, ibasset in lender.ibasset:
                ibliabtot[borrower] += ibasset
        ibliabtot_check = [bnk.ibliabtot for bnk in self.banks]
        # this should be an `isclose`
        return list(ibliabtot.values()) == ibliabtot_check

    def get_equity(self):
        """Return the equity for all banks."""
        return [bnk.equity for bnk in self.banks]

    def get_naiveequity(self):
        """Return the face value of equity for all banks."""
        return [bnk.get_naiveequity() for bnk in self.banks]

    def set_equity(self, equity_new):
        """Set the value of equity for all banks.
        
        Parameters:
            equity_new (sequence of float): new equities.
        """
        for idx, bnk in enumerate(self.banks):
            bnk.equity = equity_new[idx]

    def fixedpoint_equity(self):
        """Compute the fixed-point equities using the iterative the map.
        
        The map is iterated either until the equities obtained ofter two 
        consecutive iterations are close or until the a maximum number of 
        iteration is reached. Equities of all banks are updated step by step.
        """
        time = 0
        err = self.tol * 10
        while (err > self.tol) and (time < self.maxiter):
            equity_old = self.get_equity()
            if self.save_history and time == 0:
                self.history.append(equity_old)
            equity_new = [bnk.eval_equity() for bnk in self.banks]
            err = 2 * sum(((abs(equity_old[idx] - equity_new[idx]) /
                            ((abs(equity_old[idx]) + abs(equity_new[idx])))
                            if equity_old[idx] != 0.0 or equity_new[idx] != 0.0
                            else 0.0
                            for idx in range(self.nbanks))))
            self.set_equity(equity_new)
            time += 1
            if self.save_history:
                self.history.append(equity_new)

    def set_history(self, save_history):
        """Reset the saved history of equity.
        
        Parameters:
        save_history (bool): if `True` resets the history of equities, if 
                             `False` deletes it
        """
        if save_history:
            self.save_history = True
            self.history = []
        else:
            self.save_history = False
            if hasattr(self, 'history'):
                del self.history
            
    def get_ibasset_matrix(self):
        """Return the matrix of interbank assets."""
        exposures = [[0 for x in range(self.nbanks)] for y in range(self.nbanks)]
        for idx_l, lender in enumerate(self.banks):
            if hasattr(lender, 'ibasset'):
                for borrower, amount in lender.ibasset:
                    idx_b = list(self.banks).index(borrower)
                    exposures[idx_l][idx_b] = amount
        return exposures
        