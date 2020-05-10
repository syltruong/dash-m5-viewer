import re
from typing import List

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

from app import app, accuracy_evaluator, sales_explorer
from utils.plotting import plot_sunburst, plot_samples
from utils.settings import AGG_FUNCTIONS

def content() -> html.Div:

    tabs = dcc.Tabs(
        id='tabs-explore', 
        value='sample_plots', 
        children=[
            dcc.Tab(label='Plot some samples', value='sample_plots'),
            dcc.Tab(label='USD sales repartition', value='sales_repartition'),
        ], 
        colors={
            "border": "#d6d6d6",
            "primary": "#fc0058",
            "background": "#f9f9f9"
        }
        ) 

    content = html.Div(
        [
            html.Div(
                id='explore:sunburst',
                children=explore_sunburst_tab(),
                style={'display': 'none'}
                ),
            html.Div(
                id='explore:sample_plots',
                children=explore_sample_plots_tab(),
                style={'display': 'none'}
                ),
        ]
    )
        
    ret = html.Div(
        [
            tabs,
            content
        ]
    )
    return ret

def explore_sunburst_tab() -> html.Div:
    
    ret = html.Div(
        [
            html.Div(
                [
                    html.H4('Instructions'),
                    "These pie charts give an idea of repartition of generated sales over the last 28 days.",
                    " They display the same sales data with different hierarchy orders. They can be interacted with."
                ],
                className='instructions'
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                id="explore:sunburst_1",
                                figure={}
                            )
                        ],
                        className='six columns'
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="explore:sunburst_2",
                                figure={}
                            )
                        ],
                        className='six columns'
                    )
                ],
                className='row'
            )
        ]
    )

    return ret


def explore_sample_plots_tab(
    agg_functions: List[str]=AGG_FUNCTIONS
    ) -> html.Div:
    """
    Returns a Div with a Graph and associated controls

    Returns
    -------
    html.Div
        "Explore > Sales Repartition" tab content Div    
    """

    group_by_cols = sales_explorer.id_cols
    filters = sales_explorer.filter_possible_values_dict

    def _filter_by_div():
        ret = html.Div(
            [
                html.Div(
                    [
                        html.H6(f['name']),
                        dcc.Dropdown(
                            options=[
                                {'label': option, 'value': option}
                                for option in f['options']
                            ],
                            value=[],
                            multi=True,
                            id='filter-{}'.format(f['name'])
                        )
                    ]
                )

                for f in filters
            ]
        )

        return ret
        
    def _group_by_div():
        ret = dcc.RadioItems(
            id='group_by',
            options=[
                {'label' : col, 'value' : col} for col in group_by_cols
            ],
            value=group_by_cols[0]
        )

        return ret
        
    def _aggregate_div():
        ret = dcc.RadioItems(
            id='aggregate',
            options=[
                {'label' : col, 'value' : col} for col in agg_functions
            ],
            value=agg_functions[0]
        )

        return ret

    ret = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4('Instructions'),
                            "Use the commands to explore the train-validation dataset"
                        ],
                        className='instructions-div'
                    ),
                    html.Div(
                        [
                            html.H4('Filter by:'),
                            _filter_by_div(),
                        ],
                        className='command-div'
                    ),
                    html.Div(
                        [
                            html.H4('Group by:'),
                            _group_by_div(), 
                        ],
                        className='command-div'
                    ),
                    html.Div(
                        [
                            html.H4('Aggregate:'),
                            _aggregate_div(), 
                        ],
                        className='command-div'
                    )
                ],
                id='explore-controls',
                className='three columns explore-controls-div'
            ),
            html.Div(
                [
                    html.Div(
                        children=[
                            html.Div(
                                className='about-selected-div',
                                children=[
                                    "Total count of time series",
                                    html.Div(
                                        "N/A",
                                        className='about-selected-number-div',
                                        id='total_count'
                                    )
                                ]
                            ),
                            html.Div(
                                className='about-selected-div',
                                children=[
                                    "Count of considered time series",
                                    html.Div(
                                    "N/A",
                                        className='about-selected-number-div',
                                        id='considered_count'
                                    )
                                ]
                            ),
                            html.Div(
                                className='about-selected-div',
                                children=[
                                    "Count of aggregated time series",
                                    html.Div(
                                        "N/A",
                                        className='about-selected-number-div',
                                        id='agg_count'
                                    )
                                ]
                            )
                        ]
                    ),
                    dcc.Loading(
                        dcc.Graph(
                            id="samples_graph",
                            figure={}
                        )
                    )
                ],
                id='explore-graphs',
                className='nine columns'
            ), 
        ],
        className='row'
    )

    return ret


@app.callback([
        Output('explore:sample_plots', 'style'),
        Output('explore:sunburst', 'style'),
        Output('explore:sunburst_1', 'figure'),
        Output('explore:sunburst_2', 'figure')
    ],
    [
        Input('tabs-explore', 'value'),
    ] 
)
def render_explore_content(tab):

    sales_col = 'sales_usd'

    df = accuracy_evaluator.sales_df
    df[sales_col] = accuracy_evaluator.sales_usd_per_id 

    fig_1 = plot_sunburst(
        df,
        col=sales_col,
        path=['state_id','store_id','cat_id','dept_id'],
        color_discrete_sequence=px.colors.qualitative.Pastel
        )

    fig_2 = plot_sunburst(
        df,
        col=sales_col,
        path=['cat_id', 'dept_id', 'state_id', 'store_id'],
        color_discrete_sequence=px.colors.qualitative.Pastel[3:]
        )

    if tab == 'sample_plots': 
        return {'display' : 'block'}, {'display' : 'none'}, fig_1, fig_2
    elif tab == 'sales_repartition':
        return {'display' : 'none'}, {'display' : 'block'},  fig_1, fig_2
    
@app.callback([
        Output('total_count', 'children'),
        Output('considered_count', 'children'),
        Output('agg_count', 'children'),
        Output('samples_graph', 'figure'),
    ],
    [
        Input('group_by', 'value'),
        Input('aggregate', 'value'),
    ] +
    [
        Input('filter-{}'.format(f['name']), 'value')
        for f in sales_explorer.filter_possible_values_dict
    ]
)
def plot(group_by, aggregate, *filter_values):
    
    return plot_samples(
        sales_explorer,
        group_by, 
        aggregate, 
        *filter_values
        )
