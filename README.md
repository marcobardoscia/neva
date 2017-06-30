# Neva: Network Valuation in financial systems
This package is an implementation of the Neva framework introduced in [1]. 
Neva allows to perform the valuation of equities of banks that hold 
cross-holding of debt. Several known contagion algorithms (e.g. Furfine, 
Eisenberg and Noe, and Linear DebtRank) are special cases of Neva. 

The package has been used to run the simulations in [2].

## Advice
Users of the package should read (at least) the documentation in the following 
modules:
- [`bank.py`](neva/bank.py): for a general overview of the model
- [`ibeval.py`](neva/ibeval.py): for an introduction to valuation functions
- [`parse.py`](neva/parse.py): for the format of input data

## Data
Input data can be in several formats. The simplest possibility is to provide 
two files, one holding the information on banks' balance sheets and one 
containing the exposures. Exposures can be given either as a list or as a 
table. For examples, see [`balance_sheets.csv`](data/balance_sheets.csv), 
[`exposures_list.csv`](data/exposures_list.csv), and 
[`exposures_table.csv`](data/exposures_table.csv).

It is also possible to provide all data in a single JSON file, see 
[`parse.py`](neva/parse.py) for a full specification.

## Simplest example
In the simplest example we will run the Eisenberg and Noe algorithm without 
any shocks to equities.

```python
import neva

# parsing data
bsys, params = neva.parse_csv('balance_sheets.csv', 'exposures_table.csv')

# running Eisenberg and Noe (without any shock to equities)
equity_shock = [0.0 for _ in bsys]
neva.shock_and_solve(bsys, equity_shock, method='eisenberg_noe',
                                         solve_assets=False)

# reading final equities
equity_final = bsys.history[-1]

# computing payment vectors
pay_vec = [bnk.ibliabtot if bnk.equity >= 0 else
           max(bnk.equity + bnk.ibliabtot, 0.0) for bnk in bsys]
```

## A more complex example
Here we run an analysis simalr to that run in [2].

```python
import neva

# parsing data
bsys, params = neva.parse_csv('balance_sheets.csv', 'exposures_table.csv')

# Geometric Browianian Motion on external assets, whose volatility is
# estimated via the volatility of equities.
sigma_equity = [float(params[bnk]['sigma_equity']) for bnk in params]
bsys = neva.BankingSystemGBMse.with_sigma_equity(bsys, sigma_equity)
    
# storing initial equity
equity_start = bsys.get_equity()

# shocks to initial equity: 50%
equity_delta = equity_start[:]
equity_delta = [e * 0.5 for e in equity_start]

# running ex-ante Black and Cox, as in [2] 
# with recovery rate equal to 60%
recovery_rate = [0.6 for _ in bsys] 
neva.shock_and_solve(bsys, equity_delta, 'exante_en_blackcox_gbm', 
                     solve_assets=False, recovery_rate=recovery_rate)

# reading equities after one round and after all rounds   
equity_direct = bsys.history[1]
equity_final = bsys.history[-1]
```

## Compatibility
We will target the latest release of Python 3 and, as long as possible, 
Python 2.7. Only built-in packages are required.

## References
[1] Paolo Barucca, Marco Bardoscia, Fabio Caccioli, Marco D'Errico, Gabriele 
    Visentin, Stefano Battiston, and Guido Caldarelli. Network Valuation in 
    Financial Systems (2016). Available at 
    [SSRN](https://ssrn.com/abstract=2795583).

[2] Marco Bardoscia, Paolo Barucca, Adam Brinley Codd, John Hill. The decline 
    of solvency contagion risk (2017). 
    [Bank of England Staff Working Paper No. 662](http://www.bankofengland.co.uk/research/Pages/workingpapers/2017/swp662.aspx).