import numpy as np
import pandas as pd

def calc_portfolio_price(assets_tbl):
    """

    :param assets_tbl:
    :return:
    """

    assets_tbl['weighted_price'] = assets_tbl['asset_weight'] * assets_tbl['asset_price']

    return assets_tbl


def calc_portfolio_returns(assets_tbl):
    """

    :param assets_tbl:
    :return:
    """

    pf_tbl = assets_tbl.groupby(['portfolio_id', 'date'])['weighted_price'].sum().rename('price').reset_index()
    pf_tbl['pct_return'] = pf_tbl['price'].pct_change()
    pf_tbl['log_return'] = np.log(pf_tbl['price'] / pf_tbl['price'].shift(1))

    return pf_tbl