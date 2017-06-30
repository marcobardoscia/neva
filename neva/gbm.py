"""This module extends the classes `Bank` and `BankingSystem` in the case in 
which external assets follow a Geometric Brownian Motion.
"""

from __future__ import division
import math
from .adjust import BankAdjust, BankingSystemAdjust


def sigma_asset_simple(equity, extasset, sigma_equity):
    """Compute the volatility of external assets, assuming that both equity and
    external assets follow a geometric Brownian motion. 

    Parameters:
        equity (float): equity
        extasset (float): external assets
        sigma_equity (float): volatility of the equity

    Returns:
        volatility of the external assets

    Warning:
        Currently only works without explcit valuation of external assets.    
    """
    return equity / extasset * sigma_equity
    

class BankGBM(BankAdjust):
    """Bank whose external assets follow a Geometric Brownian Motion.
        
    Attributes:
        sigma_asset (float): volatility of external assets
    """
    def __init__(self, bnk, sigma_asset=0):
        """Create a bank with external assets that follow a Geometric Brownian 
        Motion.
        
        Parameters:
            bnk (`Bank`): bank object
            sigma_asset (float): volatility of external assets
        """
        super(BankGBM, self).__init__(bnk.extasset, bnk.extliab, bnk.exteval, 
                                      bnk.ibliabtot, bnk.ibeval, 
                                      bnk.ibeval_lender, 
                                      bnk.equity, bnk.name)
        self.sigma_asset = sigma_asset


class BankGBMse(BankGBM):
    """Bank whose external assets follow a Geometric Brownian Motion and whose
    volatility of external assets is estimated through the volatility of its 
    equity.
    
    Attributes:
        sigma_equity (float): volatility of equity
        saeval (fun(...)): volatility of external assets as an explicit 
                           function of equity, extasset, sigma_equity 
    """
    def __init__(self, bnk, sigma_equity=0, saeval=sigma_asset_simple):
        """Create a bank with external assets that follow a Geometric Brownian 
        Motion using the volatility of the equity.
        
        Parameters:
            bnk (`Bank`): bank object
            sigma_equity (float): volatility of equity
            saeval (fun(...)): volatility of external assets as an explicit 
                               function of equity, extasset, sigma_equity 
        """
        sigma_asset = saeval(bnk.equity, bnk.extasset, sigma_equity)
        super(BankGBMse, self).__init__(bnk, sigma_asset)
        self.sigma_equity = sigma_equity
        self.saeval = saeval
    
    def eval_sigma_asset(self):
        """Return the one-step valuation of the volatility of external assets.
        """
        return self.saeval(self.equity, self.extasset, self.sigma_equity)
    

class BankingSystemGBM(BankingSystemAdjust):
    """Banking system whose banks have external assets that follow a Geometric 
    Brownian Motion."""
    @classmethod
    def with_sigma_asset(cls, bnksys, sigma_asset=[]):
        """"Create a banking system whose banks have external assets that follow
        a Geometric Brownian Motion by providing the volatilities of external 
        assets.
        
        Parameters:
            bnksys (`BankingSystemAdjust`): banking system object
            sigma_asset (sequence of float): volatilities of external assets
        """
        if not sigma_asset:
            sigma_asset = [0 for bnk in bnksys.banks]
        banks_gbm = [BankGBM(bnk, sigma_asset=sa) 
                     for bnk, sa in zip(bnksys.banks, sigma_asset)]
        return cls._from_bankingsystem(banks_gbm, bnksys)
                    
    def set_sigma_asset(self, sigma_asset_new):
        """Set the value of the volatility on assets for all banks.
        
        Parameters:
            sigma_equity_new (sequence of float): new volatility on assets.
        """
        for idx, bnk in enumerate(self.banks):
            bnk.sigma_asset = sigma_asset_new[idx]


class BankingSystemGBMse(BankingSystemGBM):
    """Banking system whose banks have external assets that follow a Geometric 
    Brownian Motion and whose volatility of external assets is estimated 
    through the volatility of their equities."""
    @classmethod
    def with_sigma_equity(cls, bnksys, sigma_equity=[], saeval_list=[]):
        """"Create a banking system whose banks have external assets that follow
        a Geometric Brownian Motion by providing the volatilities of equities.
        
        Parameters:
            bnksys (`BankingSystemGBM`): banking system object
            sigma_equity (sequence of float): volatilities of equities
            saeval_list (sequence of fun(...)): volatilities of external assets 
                                                as explicit functions of equity, 
                                                extasset, sigma_equity
        """
        if not sigma_equity:
            sigma_equity = [0 for bnk in bnksys.banks]
        if not saeval_list:
            saeval_list = [sigma_asset_simple for bnk in bnksys.banks]
        banks_gbm = [BankGBMse(bnk, sigma_equity=sa, saeval=saeval) 
                     for bnk, sa, saeval in zip(bnksys.banks, sigma_equity, saeval_list)]
        return cls._from_bankingsystem(banks_gbm, bnksys)
    
    def set_sigma_equity(self, sigma_equity_new):
        """Set the value of the volatility on equity for all banks.
        
        Parameters:
            sigma_equity_new (sequence of float): new volatility on equity.
        """
        for idx, bnk in enumerate(self.banks):
            bnk.sigma_equity = sigma_equity_new[idx]

    def fixedpoint_extasset_sigmaasset(self):
        """Compute the fixed-point for external assets and their volatility 
        jointly using the iterative map.
        
        The map is iterated either until both the external assets and their 
        volatility obtained after two consecutive iterations are close or until
        the maximum number of iterations is reached. 
        """
        time = 0
        err = self.tol * 10
        while (err > self.tol) and (time < self.maxiter):
            # old external assets and volatility on external assets
            extasset_old = [bnk.extasset for bnk in self.banks]
            sigma_asset_old = [bnk.sigma_asset for bnk in self.banks]
            # computing new stuff
            extasset_new = [bnk.eval_extasset() for bnk in self.banks]
            sigma_asset_new = [bnk.eval_sigma_asset() for bnk in self.banks]            
            self.set_extasset(extasset_new)
            self.set_sigma_asset(sigma_asset_new)
            # errors
            err_a = 2 * sum(((abs(extasset_old[idx] - extasset_new[idx]) /
                              ((abs(extasset_old[idx]) + abs(extasset_new[idx])))
                              if extasset_old[idx] != 0.0 or extasset_new[idx] != 0.0
                              else 0.0
                              for idx in range(self.nbanks))))
            err_s = 2 * sum(((abs(sigma_asset_old[idx] - sigma_asset_new[idx]) /
                              ((abs(sigma_asset_old[idx]) + abs(sigma_asset_new[idx])))
                              if sigma_asset_old[idx] != 0.0 or sigma_asset_new[idx] != 0.0
                              else 0.0
                              for idx in range(self.nbanks))))
            err = math.sqrt(err_a**2 + err_s**2)
            time += 1
