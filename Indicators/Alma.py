import numpy as np
import pandas as pd
from math import exp
# from numba import jit
from ta.utils import IndicatorMixin

class ALMAIndicator(IndicatorMixin):
    def __init__(
            self,
            close: pd.Series,
            window,
            fillna: bool = False):
        self._close = close
        self._window = window
        self._offset = 0.85
        self._sigma = 6
        self._fillna = fillna
        self._alma_weights = self.alma_weights(window, self._offset, self._sigma)
        self._run()

    def _run(self):
        if self._window > 1000000:
            self._alma = self.calculate_alma_large(self._close.values, self._alma_weights, self._window)
        else:
            self._alma = self.calculate_alma_small(self._close.values, self._alma_weights, self._window)
    def alma(self) -> pd.Series:
        return pd.Series(self._alma, index=self._close.index, name='alma')

    @staticmethod
    # @jit(nopython=True)
    def calculate_alma_large(prices: np.ndarray, weights: np.ndarray, window: int) -> np.ndarray:
        alma = np.full_like(prices, fill_value=np.nan, dtype=np.float64)
        weights_sum = np.sum(weights)
        for i in range(window - 1, len(prices)):
            weighted_sum = np.sum(weights * prices[i - window + 1:i + 1])
            alma[i] = weighted_sum / weights_sum
        return alma

    def calculate_alma_small(self, prices: np.ndarray, weights: np.ndarray, window: int) -> np.ndarray:
        alma = np.full_like(prices, fill_value=np.nan, dtype=np.float64)
        weights_sum = np.sum(weights)
        for i in range(window - 1, len(prices)):
            weighted_sum = np.sum(weights * prices[i - window + 1:i + 1])
            alma[i] = weighted_sum / weights_sum
        return alma


    @staticmethod
    def alma_weights(window, offset=0.85, sigma=6):
        m = int(offset * (window - 1))
        s = window / sigma
        k_all = np.arange(window)
        weights = np.exp(-((k_all - m) ** 2) / (2 * s ** 2))
        return weights
