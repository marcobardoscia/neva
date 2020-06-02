"""Valuation functions for external assets.

External assets are marked-to-market using external valuation functions:

    A_i^e * V_i^e(E_i) ,

where E_i is the equity of bank i, A_i^e is the face value of external assets 
of bank i, and V_i^e (E_i) is the external valuation function. Here the 
definition of the external valuation function is slightly different: 

    A_i^e * V_i^e(E_i) = exteval(E_i | A_i^e, L_i^e) ,

where L_i^e are the external liabilities of bank i.

References:
    [1] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin, 
        G. Caldarelli, S. Battiston. Network Valuation in Financial Systems, 
        Mathematical Finance, https://doi.org/10.1111/mafi.12272
"""

from __future__ import division
from .ibeval import lognormal_pd, blackcox_pd


def default_cost(equity, extasset, extliab, alpha):
    """Valuation function for external assets including default costs.

    If the equity is larger than zero, external assets are taken at their face
    value; otherwise they are both discounted by a factor `alpha`. External
    liabilities are always taken at face value.

    Parameters:
        equity (float): equity
        extasset (float): external assets
        extliab (float): external liabilities
        alpha (float): discount factor for external assets in case of negative
                       equity

    Returns:
        value taken by the external valuation function
    """
    if equity > 0:
        return extasset - extliab
    else:
        return alpha * extasset - extliab


def exante_en(equity, extasset, extliab, alpha, prob_def):
    """Valuation function for external assets for the ex-ante Eisenberg and Noe 
    model in the case in which there are non-zero default costs.

    The valuation of external assets is the expected value on a bimodal 
    distribution whose to two states correspond to default and no default. In 
    fact the output is:

        `extasset` * [ (1 - `prob_def`(`equity`)) + 
                       + `alpha` * `prob_def`(`equity`) ] - `extliab`
    
    Parameters:
        equity (float): equity
        extasset (float): external assets
        extliab (float): external liabilities
        alpha (float): discount factor for external assets in case of default
        prob_def (float): probability of default evaluated in `equity`

    Returns:
        value taken by the external valuation function
    """
    return extasset * (1 + (alpha - 1) * prob_def) - extliab


def exante_en_merton_gbm(equity, extasset, extliab, alpha, sigma):
    """Valuation function for external assets for the ex-ante Eisenberg and Noe 
    model in the case in which there are non-zero default costs, external 
    assets follow Geometric Brownian Motion and banks can default only at the 
    maturity.
    
    Parameters:
        equity (float): equity
        extasset (float): external assets
        extliab (float): external liabilities
        alpha (float): discount factor for external assets in case of default
        sigma (float): volatility of the Geometric Browninan Motion
    
    Returns:
        value taken by the external valuation function
    """
    prob_def = lognormal_pd(equity, extasset, sigma)
    return exante_en(equity, extasset, extliab, alpha, prob_def)
    

def exante_en_blackcox_gbm(equity, extasset, extliab, alpha, sigma):
    """Valuation function for external assets for the ex-ante Eisenberg and Noe 
    model in the case in which there are non-zero default costs, external 
    assets follow Geometric Brownian Motion and banks can default before the 
    maturity.
    
    Parameters:
        equity (float): equity
        extasset (float): external assets
        extliab (float): external liabilities
        alpha (float): discount factor for external assets in case of default
        sigma (float): volatility of the Geometric Browninan Motion
    
    Returns:
        value taken by the external valuation function
    """
    prob_def = blackcox_pd(equity, extasset, sigma)
    return exante_en(equity, extasset, extliab, alpha, prob_def)
