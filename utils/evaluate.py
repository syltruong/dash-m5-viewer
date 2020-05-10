import re
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from utils.settings import (
    AGGREGATION_LEVEL_NAMES,
    AGGREGATION_LEVELS,
    N_VALIDATION_DAYS
)

def get_rollup_matrix(
    sales_df: pd.DataFrame,
    ) -> csr_matrix:
    """
    Return a sparse matrix of shape `(n_aggregated_time_series, len(sales_df))`.
    The sparse matrix is made of empty values and ones.
    A value is not null if the associated `id` in `sales_df` is considered is the associated time series
    
    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales dataframe

    Returns
    -------
    int
        Number of aggregation levels
    List[str]
        Sales DataFrame ids
    List[str] #TODO change type to List[str] in the code
        Aggregated time series ids
    csr_matrix
        Rollup utils matrix
    """
       
    def _aggregate_ids(df, agg_level):
        """
        Get the pd.Series of ids reflecting aggregation level
        """
        ids = None

        for col in agg_level:
            if ids is None:
                ids = df[col]
            else:
                ids = ids + ":" + df[col]
        
        return ids

    sales_df["all"] = "all"

    dummies_list = [
        _aggregate_ids(sales_df, agg_level)
        for agg_level in AGGREGATION_LEVELS
        ]
    
    # List of dummy dataframes:
    dummies_df_list = [
        pd.get_dummies(cats, drop_first=False, dtype=np.int8).T 
        for cats in dummies_list
        ]
    
    # Concat dummy dataframes in one go:
    ## Level is constructed for free.
    roll_mat_df = pd.concat(
        dummies_df_list, 
        keys=AGGREGATION_LEVEL_NAMES,
        names=['agg_level', 'agg_level_id']
        )

    n_agg_levels = len(dummies_list)
    ids = sales_df['id'].values
    agg_level_ids = roll_mat_df.index.to_frame().reset_index(drop=True)
    roll_mat_csr = csr_matrix(roll_mat_df.values)

    return n_agg_levels, ids, agg_level_ids, roll_mat_csr

def get_scaling_factors(
    sales_df: pd.DataFrame,
    rollup_matrix: csr_matrix,
    n_validation_days : int=N_VALIDATION_DAYS
    ) -> np.array:
    """
    Return scaling factors for each aggregated time series.
    The scaling factors are the MSE for a lag-1 forecast in the train period

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales dataframe
    rollup_matrix : scipy.sparse.csr_matrix
        Rollup matrix, see `utils.evaluation.get_rollup_matrix`
    n_validation_days : int
        Number of validation days to remove from the end of the time series

    Returns
    -------
    np.array
        scaling factors for each of the aggregated time series
    """

    d_cols = [col for col in sales_df.columns if re.match(r'd_[0-9]+', col)]
    d_cols = sorted(
        d_cols, 
        key=lambda elt : int(elt.rsplit('_', 1)[-1]),
        reverse=False
        )[:-n_validation_days]
    n_days = len(d_cols)

    sales_values = sales_df[d_cols].values
    sales_values_agg = rollup_matrix * sales_values

    # find sales start index for each aggregation
    start_index_per_ts = np.argmax(sales_values_agg>0, axis=1)

    # replace days less than min day number with np.nan
    # important, so that the diff from 0 to the first non-zero value is not counted
    # in np.nansum
    shape_sales_values_agg = sales_values_agg.shape
    flag = np.dot(
        np.diag(1/(start_index_per_ts+1)),
        np.tile(
            np.arange(1, sales_values_agg.shape[1] + 1),
            (sales_values_agg.shape[0],1)
            )
        ) < 1
    sales_values_agg = np.where(flag, np.nan, sales_values_agg)

    scaling_factors = np.nansum(
        np.diff(sales_values_agg, axis=1)**2,
        axis=1
        ) / (n_days - 1 - start_index_per_ts)
    
    return scaling_factors

def get_sales_usd_weights(
    sales_df : pd.DataFrame,
    sell_prices_df : pd.DataFrame,
    calendar_df : pd.DataFrame,
    rollup_matrix : csr_matrix,
    n_validation_days : int=N_VALIDATION_DAYS
) -> Tuple:
    """
    Return weight factor for each aggregated time series.
    Each weight is proportional to the cumulative USD sales of the corresponding aggregated sales,
    over the training period

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales dataframe
    sell_prices_df : pd.DataFrame
        Sell prices dataframe
    calendar_df : pd.DataFrame
        Calendar dataframe
    rollup_matrix : scipy.sparse.csr_matrix
        Rollup matrix, see `utils.evaluation.get_rollup_matrix`
    n_validation_days : int
        Number of validation days to remove from the end of the time series

    Returns
    -------
    np.array
        cumulative USD sales for each id, as specified by `sales_df`
    np.array
        cumulative USD sales for each of the aggregated time series
    np.array
        weight factors for each of the aggregated time series
    """

    #
    # 1. merge sales table with calendar table
    #

    d_cols = [col for col in sales_df.columns if re.match(r'd_[0-9]+', col)]
    d_cols = sorted(
        d_cols, 
        key=lambda elt : int(elt.rsplit('_', 1)[-1]),
        reverse=False
        )[-n_validation_days:]

    sales_melt_df = pd.melt(
        sales_df,
        id_vars=['id', 'item_id', 'store_id'],
        value_vars=d_cols,
        var_name='d',
        value_name='sales'
    )

    sales_melt_df = pd.merge(
        sales_melt_df,
        calendar_df[['wm_yr_wk', 'd']],
        on='d',
        validate='m:1'
    )

    #
    # 2. merge sales table with sell prices table
    #

    sales_melt_df = sales_melt_df.merge(
        sell_prices_df,
        on=['store_id', 'item_id', 'wm_yr_wk'],
        validate='m:1'
    )

    #
    # 3. compute daily sales per id
    #

    sales_melt_df['sales_usd'] = sales_melt_df['sales'] * sales_melt_df['sell_price']

    # Calculate the total sales in USD for each id:
    total_sales_usd_per_id = sales_melt_df. \
        groupby(['id'], sort=False)['sales_usd']. \
        apply(np.sum).values
    
    # Roll up total sales by ids to higher levels:
    total_sales_usd_per_agg_level_id = rollup_matrix * total_sales_usd_per_id.reshape(-1)

    return total_sales_usd_per_id, total_sales_usd_per_agg_level_id, total_sales_usd_per_agg_level_id / total_sales_usd_per_agg_level_id[0]

class AccuracyEvaluator(object):

    def __init__(
        self, 
        sales_df: pd.DataFrame,
        sell_prices_df: pd.DataFrame, 
        calendar_df: pd.DataFrame, 
        n_validation_days: int = N_VALIDATION_DAYS):
        """
        Initiate the AccuracyEvaluator with all provided data and validation number of days.
        Pre-computes
            the rollup matrix
            Lag1 MSE scale factors
            USD sales weight factors
            groundtruth values on the validation time range
            lookback values close to the cut-off train/validation date

        Parameters
        ----------
        sales_df : pd.DataFrame
            Sales dataframe
        sell_prices_df : pd.DataFrame
            Sell prices dataframe
        calendar_df : pd.DataFrame
            Calendar dataframe
        n_validation_days : int
            Number of validation days to remove from the end of the time series
        """

        self.sales_df = sales_df

        self.n_validation_days = n_validation_days
            
        self.n_agg_levels, self.ids, self.agg_level_ids, self.rollup_matrix = get_rollup_matrix(
            sales_df
            )
            
        self.scaling_factors = get_scaling_factors(
            sales_df, 
            self.rollup_matrix,
            n_validation_days=self.n_validation_days
            )

        self.sales_usd_per_id, self.sales_usd, self.sales_usd_weights = get_sales_usd_weights(
            sales_df,
            sell_prices_df,
            calendar_df,
            self.rollup_matrix,
            n_validation_days=self.n_validation_days
            )
            
        d_cols = [col for col in sales_df.columns if re.match(r'd_[0-9]+', col)]
        d_cols = sorted(
            d_cols, 
            key=lambda elt : int(elt.rsplit('_', 1)[-1]),
            reverse=False) 
        
        self.groundtruth_df = sales_df.set_index(['id'])[d_cols[-self.n_validation_days:]].reset_index()
        self.lookback_df = sales_df.set_index(['id'])[d_cols[-3*self.n_validation_days:-self.n_validation_days]].reset_index()

    def get_rolled_up_values(
        self,
        df : pd.DataFrame
    ) -> np.array:
        """
        Given time series values for each id in the sales DataFrame,
        compute their sum aggregations according to the M5 competition's rules

        Parameters
        ----------
        df : pd.DataFrame
            Expected column
                id
        
        Returns
        -------
        np.array
            sum-aggregated values
        """
        values = df.set_index(['id']).loc[self.ids].values

        rolled_up_values = self.rollup_matrix * values

        return rolled_up_values

    def evaluate(
        self,
        predictions_df : pd.DataFrame,
        groundtruth_df : pd.DataFrame=None
    ) -> float:
        """
        Given predictions and groundtruth, compute the WRMSSE

        Parameters
        ----------
        predictions_df : pd.DataFrame
            Predictions for each `id`, in wide format (shape [n_ids, n_prediction_dates])
            Expected column
                id
        predictions_df : pd.DataFrame
            Groundtruth for each `id`, in wide format (shape [n_ids, n_prediction_dates])
            Expected column
                id
         
        Returns
        -------
        float
            WRMSSE
        """

        if groundtruth_df is None:
            groundtruth_df = self.groundtruth_df

        pred_values = predictions_df.set_index(['id']).loc[self.ids].values
        gt_values = groundtruth_df.set_index(['id']).loc[self.ids].values

        pred_values = self.rollup_matrix * pred_values
        gt_values = self.rollup_matrix * gt_values

        mse_per_agg_level_id = np.mean(
            (pred_values - gt_values)**2,
            axis=1
            ).reshape(-1)

        rmsse_per_agg_level_id= np.sqrt(
            mse_per_agg_level_id / self.scaling_factors
            )
            
        wrmsse = np.sum(
            rmsse_per_agg_level_id* self.sales_usd_weights
        ) / self.n_agg_levels

        return wrmsse
        
    def evaluate_detailed(
        self,
        predictions_df: pd.DataFrame,
        groundtruth_df: pd.DataFrame=None
    ) -> Tuple:
        """
        Given predictions and groundtruth, compute the WRMSSE and return evaluation details

        Parameters
        ----------
        predictions_df : pd.DataFrame
            Predictions for each `id`, in wide format (shape [n_ids, n_prediction_dates])
            Expected column
                id
        predictions_df : pd.DataFrame
            Groundtruth for each `id`, in wide format (shape [n_ids, n_prediction_dates])
            Expected column
                id
         
        Returns
        -------
        float
            WRMSSE
        np.array
            residuals for each aggregated time series (for each `agg_level_id` in `self.agg_level_ids`)
        pd.DataFrame
            full results per `agg_level_id`
                "rmsse"
                "sales_usd"
                "sales_usd_weight"
                "wrmsse"
        """
        if groundtruth_df is None:
            groundtruth_df = self.groundtruth_df

        pred_values = self.get_rolled_up_values(predictions_df)
        gt_values = self.get_rolled_up_values(groundtruth_df)

        residuals_per_agg_level_id = pred_values - gt_values

        mse_per_agg_level_id = np.mean(
            (residuals_per_agg_level_id)**2,
            axis=1
            ).reshape(-1)

        rmsse_per_agg_level_id= np.sqrt(
            mse_per_agg_level_id / self.scaling_factors
            )
            
        results_per_agg_df = self.agg_level_ids.copy()
        results_per_agg_df['rmsse'] = rmsse_per_agg_level_id
        results_per_agg_df['sales_usd'] = self.sales_usd
        results_per_agg_df['sales_usd_weight'] = self.sales_usd_weights / self.n_agg_levels
        results_per_agg_df['wrmsse'] = results_per_agg_df['sales_usd_weight'] * results_per_agg_df['rmsse']

        wrmsse = results_per_agg_df['wrmsse'].sum()

        return wrmsse, residuals_per_agg_level_id, results_per_agg_df 
        