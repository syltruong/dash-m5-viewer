from typing import List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.explore import SalesExplorer

def plot_sunburst(
    df: pd.DataFrame,
    col: str,
    path: List[str]=['state_id', 'store_id', 'cat_id', 'dept_id'],
    color_discrete_sequence: List[str]=px.colors.qualitative.Prism
) -> go.Figure:
    """
    Expected columns:
    - 'state_id'
    - 'store_id'
    - 'cat_id'
    - 'dept_id'
    - col
    """
    
    fig = px.sunburst(
        df, 
        path=path, 
        values=col,
        color_discrete_sequence=color_discrete_sequence
        )
    
    fig.update_layout(
        title='USD sales repartition',
        height=1000
    )

    return fig

def plot_samples(
    sales_explorer: SalesExplorer,
    groupby_col: str,
    agg_function: str,
    *filter_values: str
):

    id_count, id_count_after_filtering, n_agg_time_series, df = sales_explorer.sales_filter_groupby_agg(
        filter_values=filter_values,
        groupby_col=groupby_col,
        agg_function=agg_function,
        merge_date=True
    )

    sampling_frequency_col = 'sampling_frequency'

    df = sales_explorer.resample_datetime(
        df,
        id_cols=[groupby_col],
        sampling_frequency_col=sampling_frequency_col
    )

    try:
        fig = px.line(
                df,
                x=sales_explorer.DEFAULT_DATE_COL,
                y=sales_explorer.DEFAULT_SALES_COL,
                color=groupby_col,
                facet_row=sampling_frequency_col,
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
    except KeyError:
        # {color, facet_row} arg is raising exception when len(df)==0
        fig = px.line(
            df,
            x='date',
            y='sales',
        )

    fig.update_layout(
        autosize=False,
        height=1000,
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
        ),
        title='Sample sales at different sampling frequencies (Daily, Weekly, Monthly)'
    )

    return id_count, id_count_after_filtering, n_agg_time_series, fig






    