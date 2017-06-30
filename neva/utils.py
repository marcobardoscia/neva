"""High(er) level utilities to automate some Neva's common tasks."""

from . import ibeval


def shock_and_solve(b_sys, equity_delta, method, solve_assets=True, **kwargs):
    """Shock the equities of banks and compute the fixed point of equities.
    
    In order to keep balance sheets consistent, shocks in equity correspond to 
    an equal shock in external assets. The fixed point of equities incorporates 
    losses of all rounds. The (intermediate) equities for all rounds are also 
    saved (in `b_sys.history`). If balance sheets imply that losses in the 
    (fixed point) equities appear even without any shock, if is possible to 
    adjust external assets and their volatility to remove such effect.
    
    Parameters:
        b_sys (BankingSystem): banking system to shock
        equity delta (sequence): equity shocks to banks
        method (str): how to compute the fixed point equities, the currently
                      supported options are: `exante_en_blackcox_gbm` for 
                      ex-ante valuation with banks that can default before 
                      maturity and external assets following a Geometric 
                      Brownian Motion; `exante_en_merton_gbm`, as the previous 
                      method with banks that can default only at maturity; 
                      `eisenberg_noe` for the Eisenberg and Noe model
        solve_assets (bool): if `True` external assets and volatilities are 
                             adjusted such that without shocks the fixed point
                             equities are equal to the initial equities
        **kwargs (dict): additional method-specific parameters; e.g. some 
                         methods allow the `recovery_rate` sequence to specify 
                         the (possibly heterogenous) recovery rates of banks 
    """
    
    # dispatching parameters
    if method == 'exante_en_blackcox_gbm' or method == 'exante_en_merton_gbm':
        if 'recovery_rate' in kwargs:
            recovery_rate = kwargs['recovery_rate']
        else:
            recovery_rate = [0 for _ in b_sys]
        
    # solving for extarnal assets and their volatility
    if solve_assets:
        for idx, bnk in enumerate(b_sys):
            if method == 'exante_en_blackcox_gbm':
                bnk.ibeval = (lambda ae, bnk=bnk, rr=recovery_rate[idx]: 
                              ibeval.exante_en_blackcox_gbm(bnk.equity, ae, rr, 
                                                            bnk.sigma_asset))
            elif method == 'exante_en_merton_gbm':
                bnk.ibeval = (lambda ae, bnk=bnk, rr=recovery_rate[idx]: 
                              ibeval.exante_en_merton_gbm(bnk.equity, ae, 
                                                          bnk.ibliabtot, rr, 
                                                          bnk.sigma_asset))
            # this should not have any effect, as the valuation function is
            # constant                                              
            elif method == 'eisenberg_noe':
                bnk.ibeval = (lambda ae, bnk=bnk: 
                              ibeval.eisenberg_noe(bnk.equity, bnk.ibliabtot))
        b_sys.fixedpoint_extasset_sigmaasset()
        
    # shocking external assets of the same "pound" amount of the equity
    for idx, bnk in enumerate(b_sys):
        bnk.equity -= equity_delta[idx]
        #bnk.equity = max(bnk.equity, 0)
        bnk.extasset -= equity_delta[idx]
        #bnk.extasset = max(bnk.extasset, 0)
        
    # finding the equity
    b_sys.set_history(True)
    for idx, bnk in enumerate(b_sys):
        if method == 'exante_en_blackcox_gbm':
            bnk.ibeval = (lambda e, bnk=bnk, rr=recovery_rate[idx]:
                          ibeval.exante_en_blackcox_gbm(e, bnk.extasset, rr, 
                                                        bnk.sigma_asset))
        elif method == 'exante_en_merton_gbm':
            bnk.ibeval = (lambda e, bnk=bnk, rr=recovery_rate[idx]:
                          ibeval.exante_en_merton_gbm(e, bnk.extasset,
                                                      bnk.ibliabtot, rr, 
                                                      bnk.sigma_asset))
        elif method == 'eisenberg_noe':
            bnk.ibeval = lambda e, bnk=bnk: ibeval.eisenberg_noe(e, bnk.ibliabtot)
    b_sys.fixedpoint_equity()
