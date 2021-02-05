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

Presently lender interbank valuation functions are not used or implemented.
"""

