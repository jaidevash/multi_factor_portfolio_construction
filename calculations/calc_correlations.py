import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

def calc_primary_coefficients(X, y):
    """
    Gets highest contributing variables using L2 regularization
    """

    print(X.isna().sum().sum())
    print(X.shape)
    print(y.shape)

    model = RidgeCV()
    model.fit(X.values, y.values)

    coefficients = pd.DataFrame({'Feature': X.columns, 'Coefficient': model.coef_})

    print(model.coef_.sum())
    print(model.coef_)

    return coefficients

