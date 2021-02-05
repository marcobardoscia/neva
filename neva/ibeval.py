"""Valuation functions for interbank assets.

Interbank assets are marked-to-market using interbank valuation functions:

    A_ij * V_ij(E_i, E_j) ,

where E_i, E_j are the equities of bank i and j, and A_ij is the face value of
the interbank asset between them. The interbank valuation functions is
factorised in following way:

    V_ij(E_i, E_j) = ibeval_lender(E_i) * ibeval(E_j) ,

where the second factor is the interbank valuation function, which is meant to
capture the valuation of interbank claims depends on the equity of the
borrower.

References:
    [1] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin,
        G. Caldarelli, S. Battiston. Network Valuation in Financial Systems,
        Mathematical Finance, https://doi.org/10.1111/mafi.12272
"""

import math


def exante_en_blackcox(equity, rho, prob_def):
    """Interbank valuation function for an ex-ante Eisenberg and Noe model in
    which banks can default at any time before maturity.

    For a derivation of this interbank valuation function see Eq. (7) in [1].
    Such valuation function turns out to be a simple generalisation of
    Linear DebtRank, in which the relationship between the probability of
    default and equity is not necessairly linear [2]. A similar non-zero
    exogenous recovery rate `rho` has been added in [3].

    Parameters:
        equity (float): equity
        rho (float): exogenous recovery rate in case of default
        prob_def (float): probability of default evaluated in `equity`

    Returns:
        value taken by the interbank valuation function

    References:
        [1] M. Bardoscia, P. Barucca, A. Brinley Codd, J. Hill.
            Forward-looking solvency contagion, Journal of Economic Dynamics
            and Control, https://doi.org/10.1016/j.jedc.2019.103755
        [2] M. Bardoscia, F. Caccioli, J. I. Perotti, G. Vivaldo,
            G. Caldarelli. Distress propagation in complex networks: the case
            of non-linear DebtRank, PLoS One,
            https://doi.org/10.1371/journal.pone.0163825
        [3] M. Bardoscia, S. Battiston, F. Caccioli, G. Caldarelli.
            Pathways towards instability in financial networks, Nature
            Communications, https://www.nature.com/articles/ncomms14416
    """
    return 1.0 + (rho - 1.0) * prob_def


def rel_loss(equity, equity0):
    """Compute the (clipped) relative equity loss.

    The relative equity loss is the correct probability of default to use for
    `lin_dr`.

    The relative equity loss is computed with respect to the reference value
    `equity0` and is equal to 0, if `equity` > `equity0`; it is equal to
    1 - `equity`/`equity0`, if 0 < `equity` < `equity0`; and it is equal to 1,
    if `equity` < 0.

    Parameters:
        equity (float): equity
        equity0 (float): initial (face value) equity

    Returns:
        relative equity loss
    """
    #return (equity0 - equity) / equity0
    if equity > equity0:
        return 0.0
    if equity > 0.0:
        return 1 - equity/equity0
    else:
        return 1.0


def lin_dr(equity, equity0):
    """Interbank valuation function for Linear DebtRank.

    Linear DebtRank [1] is a shock propagation mechanism that allows to
    account for distress propagation even in absence of defaults. In contrast
    with the DebtRank inception [2] in which shocks are propagated only once,
    here infinite rounds of propagations are taken into account.

    Here it is conveniently expressed in terms of `exante_en_blackcox`.

    Parameters:
        equity (float): equity
        equity0 (float): initial (face value) equity

    Returns:
        value taken by the interbank valuation function

    References:
        [1] M. Bardoscia, S. Battiston, F. Caccioli, G. Caldarelli. DebtRank:
            A Microscopic Foundation for Shock Propagation, PLoS One,
            https://doi.org/10.1371/journal.pone.0130406
        [2] S. Battiston, M. Puliga, R. Kaushik, P. Tasca, G. Caldarelli.
            DebtRank: Too Central to Fail? Financial Networks, the FED and
            Systemic Risk, Scientific Reports,
            https://www.nature.com/articles/srep00541
    """
    prob_def = rel_loss(equity, equity0)
    #return gen_dr(equity, 0.0, prob_def)
    return exante_en_blackcox(equity, 0.0, prob_def)


def exante_en_merton(equity, extasset, liabtot, rho, prob_def,
                     prob_def_shifted, cav_aext):
    """Interbank valuation function for ex-ante Eisenberg and Noe model in
    which banks can default only at maturity.

    This interbank valuation function is derived in [1] with a standard no
    arbitrage argument for the two counterparties taken in isolation. See Eq.
    (13) in [1].

    The additional exogenous recovery rate `rho` is meant to capture the effect
    on the valuation of interbank assets of explicit default costs, as the
    ones due to fire sales to liquidate such assets. See Eq. (12) in [2].

    Parameters:
        equity (float): equity
        extasset (float): external assets
        liabtot (float): total liabilities
        rho (float): exogenous recovery rate in case of default
        prob_def (float): probability of default evaluated in `equity`, see
                          Eq. (18a) in [1]
        prob_def_shifted (float): probability of default evaluated in `equity`
                                  + `liabtot`, see Eq. (18b) in [1]
        cav_aext (float): conditional expected endogenous recovery evaluated in
                          `equity`, see Eq. (18b) in [1]

    Returns:
        value taken by the interbank valuation function

    References:
        [1] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin,
            G. Caldarelli, S. Battiston. Network Valuation in Financial Systems,
            Mathematical Finance, https://doi.org/10.1111/mafi.12272
        [2] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin,
            S. Battiston, G. Caldarelli. Network Valuation in Financial Systems,
            https://arxiv.org/abs/1606.05164v2
    """
    return ( (1 - prob_def)
             + rho * ((1 + (equity - extasset) / liabtot) *
                      (prob_def - prob_def_shifted)
                      + (1 / liabtot) * cav_aext))


def lognormal_pd(equity, extasset, sigma):
    """Compute the probability of default for external assets following a
    Geometric Brownian Motion.

    Such probability of default is the correct probability of default to use
    for the NEVA interbank valuation function with external assets following a
    Geometric Brownian Motion, implemented in `exante_en_merton_gbm`. See 
    Eq. (18a) in [1].

    Parameters:
        equity (float): equity
        extasset (float): external assets
        sigma (float): volatility of the Geometric Browninan Motion

    Returns:
        probability of default

    References:
        [1] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin,
            G. Caldarelli, S. Battiston. Network Valuation in Financial Systems,
            Mathematical Finance, https://doi.org/10.1111/mafi.12272
    """
    if equity >= extasset:
        #print('wow1')
        return 0.0
    else:
        #print('wow2', (sigma**2 / 2 + math.log(1.0 - equity/extasset)) / (math.sqrt(2) * sigma))
        #print('wow2', sigma**2 / 2, math.log(1.0 - equity/extasset), (math.sqrt(2) * sigma))
        return 1/2 * (1 + math.erf((sigma**2 / 2 + math.log(1 - equity/extasset))
                                   / (math.sqrt(2) * sigma)))


def lognormal_cav_aext(equity, extasset, liabtot, sigma):
    """Compute the conditional expected endogenous recovery for external
    assets following a Geometric Brownian Motion.

    Such conditional expected endogenous recovery is the correct conditional
    expected endogenous recovery to use for the NEVA interbank valuation
    function with external assets following a Geometric Brownian Motion,
    implemented in `exante_en_merton_gbm`. See Eq. (18b) in [1].

    Parameters:
        equity (float): equity
        extasset (float): external assets
        liabtot (float): total liabilities
        sigma (float): volatility of the Geometric Browninan Motion

    Returns:
        conditional expected endogenous recovery

    References:
        [1] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin,
            G. Caldarelli, S. Battiston. Network Valuation in Financial Systems,
            Mathematical Finance, https://doi.org/10.1111/mafi.12272
    """
    out = 0.0
    if extasset > equity:
        tmp_sigma_1 = sigma**2 / 2
        tmp_sigma_2 = math.sqrt(2) * sigma
        out += 1/2 * (1 + math.erf((math.log(1 - equity/extasset) - tmp_sigma_1)
                                    / tmp_sigma_2))
        if extasset > equity + liabtot:
            out -= 1/2 * (1 + math.erf((math.log(1 - (equity + liabtot)/extasset) -
                                                tmp_sigma_1)
                                       / tmp_sigma_2))
    return extasset * out


def exante_en_merton_gbm(equity, extasset, liabtot, rho, sigma):
    """Interbank valuation function for ex-ante Eisenberg and Noe model in
    which banks can default only at maturity and in which with external
    assets follow a Geometric Brownian Motion.

    This function is simply `exante_en_merton` specialised for external assets
    following a Geometric Brownian Motion. See Eqs. (15) and (18) in [1].

    Parameters:
        equity (float): equity
        extasset (float): external assets
        liabtot (float): total liabilities
        rho (float): exogenous recovery rate in case of default
        sigma (float): volatility of the Geometric Browninan Motion

    Returns:
        value taken by the interbank valuation function

    References:
        [1] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin,
            G. Caldarelli, S. Battiston. Network Valuation in Financial Systems,
            Mathematical Finance, https://doi.org/10.1111/mafi.12272
    """
    prob_def = lognormal_pd(equity, extasset, sigma)
    prob_def_shifted = lognormal_pd(equity + liabtot, extasset, sigma)
    cav_aext = lognormal_cav_aext(equity, extasset, liabtot, sigma)
    out = exante_en_merton(equity, extasset, liabtot, rho, prob_def,
                           prob_def_shifted, cav_aext)
    if out >= 0.0:
        if out <= 1.0:
            return out
        else:
            print("Warning: valuation function overflow", out)
            return 1.0
    else:
        print("Warning: valuation function underflow", out)
        return 0.0


def lin_cav_aext(equity, liabtot, equity0):
    """Compute the conditional expected endogenous recovery for external
    assets whose shocks have a uniform distribution.

    Such conditional expected endogenous recovery is the correct conditional
    expected endogenous recovery to use for the NEVA interbank valuation
    function with external assets whose shocks have a uniform distribution,
    implemented in `end_lin_dr` and needed to recover Linear DebtRank as a
    particular case of NEVA. See Eq. (20b) in [1].

    Parameters:
        equity (float): equity
        liabtot (float): total liabilities
        equity0 (float): initial (face value) equity

    Returns:
        conditional expected endogenous recovery

    References:
        [1] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin, 
            S. Battiston, G. Caldarelli. Network Valuation in Financial Systems, 
            https://arxiv.org/abs/1606.05164v2

    """
    # pylint: disable=C0103
    a = max(-equity0, -equity -liabtot)
    b = min(-equity, 0.0)
    if b > a:
        return (b**2 - a**2) / (2 * equity0)
    else:
        return 0.0


def end_lin_dr(equity, extasset, liabtot, rho, equity0):
    """Interbank valuation function for Linear DebtRank seen as an ex-ante
    Eisenberg and Noe model in which banks can default only at maturity.

    This interbank valuation function should output the same values as
    `lin_dr`. Linear DebtRank is realized here as a particualr case of NEVA.
    See Proposition 5 and Eq. (20) in [1].

    Parameters:
        equity (float): equity
        extasset (float): external assets
        liabtot (float): total liabilities
        rho (float): exogenous recovery rate in case of default
        equity0 (float): initial (face value) equity

    Returns:
        value taken by the interbank valuation function

    References:
        [1] P. Barucca, M. Bardoscia, F. Caccioli, M. D'Errico, G. Visentin,
            S. Battiston, G. Caldarelli. Network Valuation in Financial Systems,
            https://arxiv.org/abs/1606.05164v2
    """
    prob_def = rel_loss(equity, equity0)
    prob_def_shifted = rel_loss(equity + liabtot, equity0)
    cav_aext = lin_cav_aext(equity, liabtot, equity0)
    return exante_en_merton(equity, extasset, liabtot, rho, prob_def,
                            prob_def_shifted, cav_aext)


def eisenberg_noe(equity, liabtot):
    """Interbank valuation function for Eisenberg and Noe.

    This interbank valuation function allows to recover both the clearing a la
    Eisenberg and Noe [1].

    Parameters:
        equity (float): equity
        liabtot (float): total liabilities

    Returns:
        value taken by the interbank valuation function

    References:
        [1] L. Eisenberg, T. H. Noe. Systemic risk in financial systems,
            Management Science 47(2), 236-249 (2001)
    """
    if equity > 0:
        return 1.0
    else:
        return max((equity + liabtot) / liabtot, 0.0)


def rogers_veraart(equity, extasset, liabtot, alpha, beta):
    """Interbank valuation functions a la Rogers and Veraart.

    This interbank valuation function allows to recover both the clearing a la 
    Rogers and Veraart [1], when used with the default external valuation
    function.

    If the equity is larger than zero, there is no effect of the valution of
    interbank assets; otherwise they are discounted by a factor `beta`. This
    mechanism is meant to capture the effect on the valuation of interbank
    assets of explicit costs of the default of the lender, as the ones due to
    fire sales to liquidate such assets.

    Parameters:
        equity (float): equity
        extasset (float): external assets
        liabtot (float): total liabilties
        alpha (float): between 0 and 1, fraction of external assets recovered
        beta (float): between 0 and 1, fraction of interbank assets recovered

    Returns:
        value taken by the interbank valuation function

    References:
        [1] L. C. G. Rogers, L. A. M. Veraart. Failure and rescue in an
            interbank network, Management Science 59(4), 882-898 (2013)
    """
    if equity > 0:
        return 1.0
    else:
        return ((alpha - beta) * extasset / liabtot
                + beta * max((equity + liabtot) / liabtot, 0.0))


def roukny_battiston(equity, rho):
    """Interbank valuation function for the algorithm in ``Price of 
    Complexity``.
    
    This interbank valuation function allows to recover the mechanism exposed 
    in [1]. It is essentially the Furfine algorithm with an exogenous recovery 
    `rho`.

    Parameters:
        equity (float): equity
        rho (float): exogenous recovery rate in case of default
    
    Returns:
        value taken by the interbank valuation function
    
    References:
        [1] S. Battiston, G. Caldarelli, R. May, T. Roukny, J. E. Stiglitz. 
            The price of complexity in financial networks, PNAS, 
            https://doi.org/10.1073/pnas.1521573113
    """
    if equity > 0:
        return 1.0
    else:
        return rho


def furfine(equity):
    """Interbank valuation function for Furfine.
    
    The Furfine algorithm is also called contagion-on-default, as the 
    consequences of distress are propagated only after a banks defaults. 
    Interbank assets keep their face value, if the equity of the borrower is 
    positive, while they are worth nothing, if the equity of the borrower is 
    negative.

    Parameters:
        equity (float): equity
    
    Returns:
        value taken by the interbank valuation function
    
    References:
        [1] C. H. Furfine. Interbank exposures: quantifying the risk of 
            contagion, Journal of Money, Credit & Banking 35(1), 111-129 
            (2003)
    """
    if equity > 0:
        return 1.0
    else:
        return 0.0


def blackcox_pd(equity, extasset, sigma):
    """Compute the probability of default for external assets following a
    Geometric Brownian Motion and the Black and Cox model.

    Such probability of default is the correct probability of default to use
    for the NEVA interbank valuation function with external assets following a
    Geometric Brownian Motion, implemented in `exante_en_blackcox_gbm`. See
    Eq. (8) in [1] (which is the corresponding survival probability).

    Parameters:
        equity (float): equity
        extasset (float): external assets
        sigma (float): volatility of the Geometric Browninan Motion

    Returns:
        probability of default

    References:
        [1] M. Bardoscia, P. Barucca, A. Brinley Codd, J. Hill.
            Forward-looking solvency contagion, Journal of Economic Dynamics
            and Control, https://doi.org/10.1016/j.jedc.2019.103755
    """
    if equity <= 0.0:
        return 1.0
    if equity >= extasset:
        return 0.0
    else:
        #return 1 + (- 1/2 * (1 + math.erf((-math.log(1 - equity/extasset) - sigma**2/2) /
        #                                  (math.sqrt(2) * sigma)) )
        #            + (extasset/equity)/2 * (1 + math.erf((math.log(1 - equity/extasset) - sigma**2/2) /
        #                                                  (math.sqrt(2) * sigma)) ) )
        return (1/2 * (1 + math.erf((math.log(1 - equity/extasset) + sigma**2/2) /
                                    (math.sqrt(2) * sigma)) ) +
                (extasset/(extasset - equity))/2 * (1 + math.erf((math.log(1 - equity/extasset) - sigma**2/2) /
                                                                 (math.sqrt(2) * sigma)) ) )


def exante_en_blackcox_gbm(equity, extasset, rho, sigma):
    """Interbank valuation function for ex-ante Eisenberg and Noe model in
    which banks can default at any time before maturity and in which external
    assets follow a Geometric Brownian Motion.

    This function is simply `exante_en_blackcox` specialised for external
    assets following a Geometric Brownian Motion. See Eqs. (7) and (8) in [1].

    Parameters:
        equity (float): equity
        extasset (float): external assets
        rho (float): exogenous recovery rate in case of default
        sigma (float): volatility of the Geometric Browninan Motion

    Returns:
        value taken by the interbank valuation function

    References:
        [1] M. Bardoscia, P. Barucca, A. Brinley Codd, J. Hill.
            Forward-looking solvency contagion, Journal of Economic Dynamics
            and Control, https://doi.org/10.1016/j.jedc.2019.103755
    """
    prob_def = blackcox_pd(equity, extasset, sigma)
    #return gen_dr(equity, rho, prob_def)
    return exante_en_blackcox(equity, rho, prob_def)


def exante_furfine_merton_gbm(equity, extasset, rho, sigma):
    """Interbank valuation function for ex-ante Furfine model in
    which banks can default at any time before maturity and in which external
    assets follow a Geometric Brownian Motion.

    This function implements the exogenous Merton model in [1] for external
    assets following a Geometric Brownian Motion, see Eqs. (5) and (A.8) in [1].

    Here it is conveniently expressed in term of `exante_en_blackcox`.

    Parameters:
        equity (float): equity
        extasset (float): external assets
        rho (float): exogenous recovery rate in case of default
        sigma (float): volatility of the Geometric Browninan Motion

    Returns:
        value taken by the interbank valuation function

    References:
        [1] M. Bardoscia, P. Barucca, A. Brinley Codd, J. Hill.
            Forward-looking solvency contagion, Journal of Economic Dynamics
            and Control, https://doi.org/10.1016/j.jedc.2019.103755
"""

    prob_def = lognormal_pd(equity, extasset, sigma)
    return exante_en_blackcox(equity, rho, prob_def)
