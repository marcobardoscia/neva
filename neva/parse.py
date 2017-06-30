"""Parse various inputs that store information on the banking system."""

from __future__ import division
import json
import sys
import csv
import collections
from . import bank
from . import bankingsystem


def parse_json(flex_input):
    """Parse JSON files that store information on the banking system.
    
    The root of the JSON file must be a list. The elements of the lists are 
    single banks, represented as maps:

    [
    {
        "name" : "A",
        "extasset" : 1.0,
        "extliab" : 0.0,
        "ibasset" : {
            "B" : 1.0
        },
        "ibliabtot" : 0.0
    },
    ...
    ]

    where:
        `name` (str): name of the bank
        `extasset` (float): external assets
        `extliab` (float): external liabilities
        `ibasset`: (map of `name` : face value of interbank asset (float))
        `ibliabtot` (float): total interbank liabilities

    Parameters:
        flex_input (file or str): either a file object, or the filename of a  
                                  JSON file, or a valid JSON string
                                  
    Returns:
        `BankingSystem` object
    """
    
    if hasattr(flex_input, 'read'):
        data = json.load(flex_input)
    else:
        try:
            with open(flex_input) as fin:
                data = json.load(fin)
        except IOError:
            data = json.loads(flex_input)

    banks = []
    banks_dict = {}
    for bnk in data:
        banks.append(bank.Bank(extasset=bnk['extasset'], extliab=bnk['extliab'],
                               ibliabtot=bnk['ibliabtot'], name=bnk['name']))
        banks_dict[bnk['name']] = banks[-1]
    for idx, lender in enumerate(data):
        if 'ibasset' in lender:
            tmp = []
            for borrower in lender['ibasset']:
                tmp.append((banks_dict[borrower], lender['ibasset'][borrower]))
            tmp.sort(key=lambda tup: tup[0].name)
            banks[idx].ibasset = tmp

    return bankingsystem.BankingSystem(banks)
    

def parse_csv(in_bs, in_exp, delimiter=','):
    """Parse CSV files that hold information on balance sheets and exposures of 
    the banking system.
    
    The file holding information on the balance sheet is expected to have an 
    header (its first line) with at least the following fields:
        - `bank_name` (str): a unique identifier for banks
        - `external_asset` (float): external assets
        - `external_liabilities (float): external liabilities
    If the file contains additional fields, they will be parsed and returned 
    the dictionary `params`, which will have the structure:
    
    params[bank_name][additional_field] = value
    
    The file holding information on the exposures can be either in the format 
    of an adjacency list or of an adjacency matrix. In the former case the file 
    is expected to have an header (its first line) with the following fields:
        - `lender` (str): unique identifier of the lender
        - `borrower` (str): unique identifier of the borrower
        - `amount` (float): amount of the exposure
    and each subsequent line will represent an exposure and will adhere to the 
    format prescribed by the header. Note that exsposures are not summed, i.e. 
    if more than a line with the same combination of lender and borrower is 
    present only the line that appears as last in the file will be parsed.
    
    In the latter case the file will not have an header, but simply contain 
    in which any new line corresponds to a row and in which columns are 
    separated by `delimiter`. The ordering of both rows and columns must 
    correspond to the order in which banks appear in the file holding 
    information of balance sheets.
    
    Parameters:
        in_bs (file or str): either a file object, or the filename of a CSV 
                             file holding information on balance sheets
        in_exp (file or str): either a file object, or the filename of a CSV 
                              file holding information on exposures
        delimiter (str): delimiter for CSV files
        
    Returns:
        (`BankingSystem` object, `params`)
    """
    
    # picking the right string type depending on the version of Python
    if sys.version_info[0] >= 3:
        string_types = str
    else:
        string_types = basestring
    
    # loading balance sheet data
    if isinstance(in_bs, string_types):
        csvfile_bs = open(in_bs)
    else:
        csvfile_bs = in_bs
    lines = []
    reader = csv.reader(csvfile_bs, delimiter=delimiter)
    for row in reader:
        lines.append(row)
    if isinstance(in_bs, string_types):
        csvfile_bs.close()

    header = lines[0]
    raw_data = lines[1:]
    del lines

    # finding indices of columns
    idx_dict = {}
    for field in header:
        idx_dict[field] = header.index(field)

    # parsing balance sheets
    banks = []
    banks_idx = {}
    for idx, line in enumerate(raw_data):
        banks.append({
            'name' : line[idx_dict['bank_name']],
            'extasset' : float(line[idx_dict['external_asset']]),
            'extliab' : float(line[idx_dict['external_liabilities']])
        })
        banks_idx[line[idx_dict['bank_name']]] = idx
    header.remove('bank_name')
    header.remove('external_asset')
    header.remove('external_liabilities')
    
    # parsing other info
    params = collections.OrderedDict()
    for line in raw_data:
        name = line[idx_dict['bank_name']]
        params[name] = {}
        for field in header:
            params[name][field] = line[idx_dict[field]]

    # loading exposures data
    if isinstance(in_exp, string_types):
        csvfile_exp = open(in_exp)
    else:
        csvfile_exp = in_exp
    lines = []
    reader = csv.reader(csvfile_exp, delimiter=delimiter)
    for row in reader:
        lines.append(row)
    if isinstance(in_exp, string_types):
        csvfile_exp.close()

    # parsing exposures
    # adjacency list mode
    if lines[0][0] == 'lender':
        raw_data = lines[1:]
        for line in raw_data:
            lender, borrower, amount = line
            amount = float(amount)
            idx_l = banks_idx[lender]
            idx_b = banks_idx[borrower]
            if not 'ibasset' in banks[idx_l]:
                banks[idx_l]['ibasset'] = {}
            banks[idx_l]['ibasset'][borrower] = amount
            if not 'ibliabtot' in banks[idx_b]:
                banks[idx_b]['ibliabtot'] = 0.0
            banks[idx_b]['ibliabtot'] += amount
    # adjacency matrix mode
    else:
        for idx_l, row in enumerate(lines):
            for idx_b, element in enumerate(row):
                borrower = banks[idx_b]['name']
                amount = float(element)
                if amount > 0.0:
                    if not 'ibasset' in banks[idx_l]:
                        banks[idx_l]['ibasset'] = {}
                        banks[idx_l]['ibasset'][borrower] = amount
                        if not 'ibliabtot' in banks[idx_b]:
                            banks[idx_b]['ibliabtot'] = 0.0
                        banks[idx_b]['ibliabtot'] += amount
    
    return parse_json(json.dumps(banks)), params
    