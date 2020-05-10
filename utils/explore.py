import re
from typing import List

import pandas as pd

class SalesExplorer(object):

    def __init__(
        self, 
        sales_df: pd.DataFrame,
        calendar_df: pd.DataFrame
    ):
        """
        Initiate the SalesExplorer with all provided data 
        Pre-computes
            row identifier columns
            filter columns and value choices

        Parameters
        ----------
        sales_df : pd.DataFrame
            Sales dataframe
        """

        self.DEFAULT_DATE_COL = 'date'
        self.DEFAULT_SALES_COL = 'sales'
        self.DEFAULT_D_COL = 'd'

        self.MAX_N_GRAPH_TRACES = 15

        self.sales_df = sales_df
        self.calendar_df = calendar_df

        # row identifier columns
        self.id_cols = [col for col in self.sales_df.columns if not re.match(r'd_[0-9]+', col)] 

        # value columns
        self.d_cols = [col for col in self.sales_df.columns if re.match(r'd_[0-9]+', col)]  

        # number of unique values per identifier column
        self.cols_nunique = {col : self.sales_df[col].nunique() for col in self.id_cols}

        # columns suitable for row filtering
        MAX_NUNIQUE_PER_FILTER_COL = 20
        self.filter_possible_values_dict = [
            dict(
                name=col,
                options=self.sales_df[col].unique()
            )
            for col in self.id_cols 
            if self.sales_df[col].nunique() < MAX_NUNIQUE_PER_FILTER_COL
        ]
    
    def sales_filter_groupby_agg(
        self,
        filter_values : List[List[str]],
        groupby_col : str,
        agg_function : str,
        var_name : str=None,
        value_name : str=None,
        merge_date : bool=True 
    ) -> pd.DataFrame:
        """
        Return sales in tidy format
        after filtering, grouping and aggregation
        
        Parameters
        ----------
        filter_values : List[List[str]]
            List of permitted values per identifier column, 
            in the order of self.filter_possible_values_dict
        groupby_col : str
            id column to perform grouping on. Must be in self.id_cols
        agg_function : str
            aggregation operation to perform
        var_name : str
            pd.melt var_name parameter, by default 'd'
        value_name : str
            pd.melt value_name parameter, by default 'sales'
        merge_date : bool
            choice to merge a datetime column

        Returns
        -------
        pd.DataFrame
            filtered and aggregated sales in tidy format
        """  

        if not var_name:
            var_name = self.DEFAULT_D_COL
        
        if not value_name:
            value_name = self.DEFAULT_SALES_COL

        id_count = len(self.sales_df)
        #
        # 1. Filter
        #

        filters = zip(
            [f['name'] for f in self.filter_possible_values_dict],
            filter_values 
        )

        filters = [
            dict(
                col=elt[0],
                values=elt[1]
            )
            for elt in filters if len(elt[1]) > 0
        ]

        sales_df = self.sales_df.copy()

        for f in filters:
            try:
                sales_df = sales_df.set_index(f['col']).loc[f['values']].reset_index()
            except KeyError:
                sales_df = sales_df.iloc[[]]
                break

        id_count_after_filtering = len(sales_df)

        #
        # 2. Melt sales_df into tidy format
        #

        sales_df = sales_df[self.d_cols + [groupby_col]]

        n_agg_time_series = sales_df[groupby_col].nunique()

        if n_agg_time_series > self.MAX_N_GRAPH_TRACES:
            
            n_samples = min(len(sales_df), self.MAX_N_GRAPH_TRACES)
            
            samples = sales_df[groupby_col].sample(n_samples)
            cols_to_keep = self.d_cols + [groupby_col]
            sales_df = sales_df.set_index([groupby_col]).loc[samples].reset_index()

        sales_df = sales_df.melt(
            id_vars=[groupby_col],
            value_vars=self.d_cols,
            var_name=var_name,
            value_name=value_name
        )

        #
        # 3. Aggregate
        #

        sales_df = sales_df\
            .groupby([groupby_col, var_name])[value_name]\
            .agg(agg_function)\
            .reset_index()
        
        #
        # 4. Merge date
        #

        if merge_date:

            sales_df = pd.merge(
                sales_df,
                self.calendar_df[['d', 'date']],
                left_on=var_name,
                right_on='d',
                validate='m:1'
            )

        return id_count, id_count_after_filtering, n_agg_time_series, sales_df
    

    def resample_datetime(
        self,
        df: pd.DataFrame,
        id_cols: List[str],
        date_col: str=None,
        value_col: str=None,
        sampling_frequency_col: str='sampling_frequency',
        agg_function: str='sum'
    ) -> pd.DataFrame:
        """
        Resamples time for a dataframe in tidy format

        Parameters
        ----------
        df: pd.DataFrame
            input time series dataframe in tidy format
        date_col : str
            column with datetime values to resample, must be in df
        value_col : str
            column with values of interest, must be in df
        id_cols : List[str]
            group by columns, must be in df
        sampling_frequency_col : str
            target column, indicates sampling frequency in output dataframe
        agg_function : str
            aggregation policy, set to sum by default

        Returns
        -------
        pd.DataFrame
            resamples values in tidy format
        """ 

        if not date_col:
            date_col = self.DEFAULT_DATE_COL
        
        if not value_col:
            value_col = self.DEFAULT_SALES_COL


        SAMPLING_FREQUENCIES = [
            dict(name='Daily', col='date_day', pd_freq_alias='D'),
            dict(name='Weekly', col='date_week', pd_freq_alias='W'),
            dict(name='Monthly', col='date_month', pd_freq_alias='M')
        ]

        ret = pd.DataFrame()

        for sf in SAMPLING_FREQUENCIES:

            df[sf['col']] = df[date_col].dt.to_period(sf['pd_freq_alias']).dt.to_timestamp(how='E')
            
            groupby_cols = id_cols + [sf['col']]
            tmp = df.groupby(groupby_cols)[value_col].agg(agg_function).reset_index()
            tmp = tmp.rename(columns={sf['col'] : 'date'})
            tmp[sampling_frequency_col] = sf['name']

            ret = pd.concat(
                [
                    ret,
                    tmp
                ],
                axis=0
            )
            
        return ret
