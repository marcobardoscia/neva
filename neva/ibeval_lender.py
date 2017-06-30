"""Lender interbank valuation functions. 

Interbank assets are marked-to-market using interbank valuation functions:

    A_ij * V_ij(E_i, E_j) ,  

where E_i, E_j are the equities of bank i and j, and A_ij is the face value of 
the interbank asset between them. The interbank valuation functions is 
factorised in following way: 

    V_ij(E_i, E_j) = ibeval_lender(E_i) * ibeval(E_j) ,

where the first factor is the lender interbank valuation function, which is 
meant to capture the valuation of interbank claims depends on the equity of 
the lender. 

Presently lender interbank valuation functions are only used to recover the 
Rogers and Veraart algorythm.

References:
    [1] L. C. G. Rogers, L. A. M. Veraart. Failure and rescue in an 
        interbank network, Management Science 59(4), 882-898 (2013)
"""

from __future__ import division


def rogers_veraart(equity, beta):
    """Lender interbank valuation functions a la Rogers and Veraart.
    
    If the equity is larger than zero, there is no effect of the valution of 
    interbank asstes; otherwise they are discounted by a factor `beta`. This 
    mechanism is meant to capture the effect on the valuation of interbank 
    assets of explicit costs of the default of the lender, as the ones due to 
    fire sales to liquidate such assets. 

    Parameters:
        equity (float): equity
        beta (float): discount factor for interbank assets in case of negative
                      equity

    Returns:
        value taken by the lender interbank valuation function

    References:
        [1] L. C. G. Rogers, L. A. M. Veraart. Failure and rescue in an 
            interbank network, Management Science 59(4), 882-898 (2013)
    """
    if equity > 0:
        return 1.0
    else:
        return beta
