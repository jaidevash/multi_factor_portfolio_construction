import numpy as np
import pandas as pd

def calc_portfolio_price(assets_tbl):
    """

    :param assets_tbl:
    :return:
    """

    assets_tbl_pivot = assets_tbl.pivot(index=['portfolio_id', 'date', 'asset_weight'], columns='asset_id', values='asset_price')
    # assets_tbl['weighted_price'] = assets_tbl['asset_weight'] * assets_tbl['asset_price']
    asset_pct_return = assets_tbl_pivot.pct_change().melt(ignore_index=False, var_name='asset_id', value_name='asset_pct_return')
    asset_log_return = np.log(assets_tbl_pivot / assets_tbl_pivot.shift(1)).melt(ignore_index=False, var_name='asset_id', value_name='asset_log_return')

    asset_pct_return = asset_pct_return.set_index('asset_id', append=True)
    asset_log_return = asset_log_return.set_index('asset_id', append=True)

    assets_tbl = pd.concat([asset_pct_return, asset_log_return], ignore_index=False, axis=1).reset_index()

    assets_tbl['weighted_pct_return'] = assets_tbl['asset_weight'] * assets_tbl['asset_pct_return']
    assets_tbl['weighted_log_return'] = assets_tbl['asset_weight'] * assets_tbl['asset_log_return']

    return assets_tbl


def calc_portfolio_returns(assets_tbl):
    """

    :param assets_tbl:
    :return:
    """

    pf_tbl = assets_tbl.groupby(['portfolio_id', 'date'])[['weighted_pct_return', 'weighted_log_return']].sum().reset_index()

    pf_tbl = pf_tbl.rename(columns={'weighted_pct_return' : 'pct_return', 'weighted_log_return': 'log_return'})
    # pf_tbl['pct_return'] = pf_tbl['price'].pct_change()
    # pf_tbl['log_return'] = np.log(pf_tbl['price'] / pf_tbl['price'].shift(1))

    return pf_tbl