"""This module extends the classes `Bank` and `BankingSystem` in the case in 
which external assets can be adjusted such that the fixed-point equity is 
initially consistent with its naive value.
"""

from __future__ import division
from .bank import Bank
from .bankingsystem import BankingSystem
    

class BankAdjust(Bank):
    """Bank whose external assets can be adjusted such that the fixed-point 
    equity is initially consistent with its naive value.
    
    In general, once assets and liabilities (both external and interbank) of a 
    bank are specified, the fixed-point equity will be different from the 
    naive value obtained by subtracting liabilities from assets. However, in a 
    stress test context one might want to adjust external assets such that the 
    fixed-point equity is initially equal to its naive value. The method 
    `fixedpoint_extasset` allows precisely to perform such adjustment. 
    """
    @classmethod
    def from_bank(cls, bnk):
        """Create a bank whose external assets can be adjusted such that the 
        fixed-point equity is initially consistent with its naive value.
        
        Parameters:
            bnk (`Bank`): bank object
        """
        return cls(bnk.extasset, bnk.extliab, bnk.exteval, bnk.ibliabtot, 
                   bnk.ibeval, bnk.ibeval_lender, bnk.equity, bnk.name)
        
    def eval_extasset(self):
        """Return the one-step valuation of external asset.
        
        Similarly to `eval_equity`, external assets are evaluated iteratively, 
        assuming that the value of equity is known. This is especially useful 
        when it is possible to measure the equity, but not the external assets
        and a value of external assets consistent with the measured equity is 
        needed. The valuation of external assets should be performed 
        iteratively until convergence.

        Note:
            The external assets of the bank are returned and not stored in 
            `Bank.extassets` because the map is updated syncronously.
            
        Warning:
            Currently only works without explciit valuation of external assets.
            Also, we are somehow assuming that the valuation function for 
            external assets is monotone.
        """
        #print(self.name, self.ibasset)
        return (self.equity + self.extliab + self.ibliabtot
                - self.ibeval_lender(self.equity) * 
                sum((ibasset*borrower.ibeval(borrower.extasset)
                       for borrower, ibasset in self.ibasset)))
        

class BankingSystemAdjust(BankingSystem):
    """Banking system whose banks have external assets that can be adjusted 
    such that the fixed-point equity is initially consistent with its naive 
    value."""
    @classmethod
    def from_bankingsystem(cls, bnksys):
        """Create a banking system whose banks have external assets that can be 
        adjusted such that the fixed-point equity is initially consistent with 
        its naive value.
        
        Parameters:
            bnksys (`BankingSystem`): banking system object
        """
        banks_adj = [BankAdjust.from_bank(bnk) for bnk in bnksys.banks]     
        return cls._from_bankingsystem(banks_adj, bnksys)
        
    def set_extasset(self, extasset_new):
        """Set the value of external assets for all banks.
        
        Parameters:
            extasset_new (sequence of float): new external assets.
        """
        for idx, bnk in enumerate(self.banks):
            bnk.extasset = extasset_new[idx]
    
    def fixedpoint_extasset(self):
        """Compute the fixed-point external assets using the iterative map.
        
        The map is iterated either until the external assets obtained after two 
        consecutive iterations are close or until the maximum number of 
        iterations is reached. 
        """
        time = 0
        err = self.tol * 10
        while (err > self.tol) and (time < self.maxiter):
            extasset_old = [bnk.extasset for bnk in self.banks]
            extasset_new = [bnk.eval_extasset() for bnk in self.banks]
            err = 2 * sum(((abs(extasset_old[idx] - extasset_new[idx]) /
                            ((abs(extasset_old[idx]) + abs(extasset_new[idx])))
                            if extasset_old[idx] != 0.0 or extasset_new[idx] != 0.0
                            else 0.0
                            for idx in range(self.nbanks))))
            self.set_extasset(extasset_new)
            time += 1
