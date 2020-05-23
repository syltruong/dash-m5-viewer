from typing import List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.explore import SalesExplorer
from utils.settings import (
    AGGREGATION_LEVELS_COLOR_DISCRETE_MAP,
    AGG_LEVEL_COL,
    AGG_LEVEL_ID_COL,
    WRMSSE_COL,
    RMSSE_COL,
    SALES_USD_COL,
    COL_HEIGHT
)

def empty_figure(text='') -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        {
            "xaxis": {
                "visible": False
            },
            "yaxis": {
                "visible": False
            },
            "annotations": [
                {
                    "text": text,
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 21
                    }
                }
            ],
        }
    )

    if len(text)==0:
        fig.update_layout(
            {
                "paper_bgcolor" : 'rgba(0,0,0,0)',
                "plot_bgcolor" : 'rgba(0,0,0,0)',
            }
        )
        
    return fig

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

def plot_evaluate_first_col(results_df: pd.DataFrame) -> List[go.Figure]:
    """
    Returns all plots for the first column of forecast accuracy tab
    """

    color_discrete_map = AGGREGATION_LEVELS_COLOR_DISCRETE_MAP 
    
    tmp = results_df.groupby([AGG_LEVEL_COL]).\
        agg({WRMSSE_COL : 'sum', RMSSE_COL : 'mean', SALES_USD_COL : 'mean'}).\
            reset_index().sort_values(WRMSSE_COL, ascending=False)
    #
    # WRMSSE pie chart
    #
    fig1 = px.pie(
        tmp,
        values=WRMSSE_COL,
        names=AGG_LEVEL_COL,
        color=AGG_LEVEL_COL,
        color_discrete_map=color_discrete_map
    )
    fig1.update_layout(
        {
            "paper_bgcolor" : 'rgba(0,0,0,0)',
            "plot_bgcolor" : 'rgba(0,0,0,0)',
        }
    )

    #
    # RMSSE bar chart
    #
    fig2 = px.bar(
        tmp,
        y=RMSSE_COL,
        x=AGG_LEVEL_COL,
        color=AGG_LEVEL_COL,
        color_discrete_map=color_discrete_map
    )

    #
    # Sales usd weight pie chart
    #
    fig3 = px.bar(
        tmp,
        y=SALES_USD_COL,
        x=AGG_LEVEL_COL,
        color=AGG_LEVEL_COL,
        color_discrete_map=color_discrete_map,

    )
    fig3.update_layout(yaxis_type="log")

    titles = [
        "WRMSSE contribution of each aggregation level",
        "Mean RMSSE of series in each aggregation level",
        "Mean USD sales per series in each aggregation level (logy scale)"
    ]
        
    n_figures = 3

    for fig, title in zip([fig1, fig2, fig3], titles):
        fig.update_layout(
            height=COL_HEIGHT / n_figures,
            title=title
        )

    return fig1, fig2, fig3


def plot_evaluate_second_col(
    agg_level: str, 
    results_df: str,
    residuals: np.ndarray
    ) -> List[go.Figure]:

    color = AGGREGATION_LEVELS_COLOR_DISCRETE_MAP[agg_level]

    fig1 = {}
    fig2 = {}

    n_figures = 3
    max_n_agg_level_id = 30 # hardcode

    #
    # fig1
    #
    fig1 = go.Figure(
        data=[go.Histogram(x=residuals, marker=dict(color=color))],
            
    )

    fig1.update_layout(
        height=COL_HEIGHT / n_figures,
        title=f"Residual distribution for all series in agg level `{agg_level}`",
        xaxis_title="y_pred - y_true",
    )

    #
    # fig2
    #

    if results_df[AGG_LEVEL_ID_COL].nunique()<=max_n_agg_level_id:
        
        tmp = results_df[[AGG_LEVEL_ID_COL, WRMSSE_COL, SALES_USD_COL]]\
            .sort_values(SALES_USD_COL, ascending=False)

        fig2 = make_subplots(
            rows=2,
            cols=1,
            specs=[
                [{'type':'xy'}],
                [{'type':'xy'}]
            ],
            subplot_titles=[
                "Sales USD",
                "WRMSSE (ordered by sales USD)",
            ]
        )

        fig2.add_trace(
            go.Bar(
                x=tmp[AGG_LEVEL_ID_COL],
                y=tmp[SALES_USD_COL],
                name="Sales USD"
            ),
            1,1
        )

        fig2.add_trace(
            go.Bar(
                x=tmp[AGG_LEVEL_ID_COL],
                y=tmp[SALES_USD_COL],
                name="WRMSSE"
            ),
            2,1
        )

        fig2.update_traces(
            marker_color=color
            )

        fig2.update_layout(
            {
                "paper_bgcolor" : 'rgba(0,0,0,0)'
            }
        )

    else:
        fig2 = empty_figure("Too many series to be displayed")

    fig2.update_layout(
        height= 2*COL_HEIGHT / n_figures,
        title=f"Error and Sales USD repartition in agg level"
    )

    return fig1, fig2

        