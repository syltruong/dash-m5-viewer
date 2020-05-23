import datetime
import json
import re
from typing import List

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import numpy as np
import pandas as pd

from app import app, accuracy_evaluator
from utils.plotting import (
    plot_evaluate_first_col,
    plot_evaluate_second_col,
    plot_evaluate_third_col
)
from utils.io import parse_contents

UPLOAD_BUTTON_TEXT = [
    'Drag and Drop or ',
    html.A('Select a File'),
    ' (Max File Size 10MB)'
] 

def content() -> html.Div:

    ret = [
        instructions(),
        file_upload_area(),
        hidden_uploaded_data_area(), 
        score_display_area(),
        upload_error_message(),
        report_display_area()
    ]

    return ret

def instructions() -> html.Div:

    ret = html.Div(
        [
            html.H4('Instructions'),
            "Visualize errors on the 'Accuracy' competition.",
            "The validation period corresponds to the last 28 days of the training set.",
            "To begin, upload your predictions over that horizon, in the format specified by the competition."  
        ],
        className='instructions'
    )

    return ret


def file_upload_area() -> html.Div:

    ret = html.Div(
        dcc.Upload(
            id='evaluate:upload',
            children=UPLOAD_BUTTON_TEXT,
            multiple=False,
            max_size=10e+6, # 10MB,
        ),
        className='file-upload-button-div'
    )

    return ret

def hidden_uploaded_data_area() -> html.Div:

    ret = html.Div(
        children=[
            html.Div(
                children=[
                    dash_table.DataTable(
                        id='evaluate:predictions'
                        )
                    ],
                hidden=True
            ),
                
            html.Div(
                children=[
                    dash_table.DataTable(
                        id='evaluate:results'
                        )
                    ],
                hidden=True
            ),
            html.Div(
                id='evaluate:residuals',
                hidden=True
            ),
        ],
        hidden=True
    )

    return ret

def score_display_area() -> html.Div:

    ret = html.Div([
        html.H6('WRMSSE:'),
        html.Div(
            'N/A',
            id='evaluate:score',
            className='about-selected-number-div'
        )
        ],
        className='score-div'
        )

    return ret

def upload_error_message() -> html.Div:

    ret = html.Div(
        "There was an issue processing your file. Check the format and schema.",
        style={
            'display' : 'hidden'
        },
        id='explore:upload_error_message'
    )

    return ret

def report_display_area() -> html.Div:

    first_column = html.Div(
        children=[
            html.Div(
                "Click on aggregation levels in graphs to see results with more granularity",
                style={
                    'padding' : '10px'
                }
            ),
            dcc.Graph(
                id="evaluate:wrmsse_pie",
                figure={} #empty_figure()
            ),
            dcc.Graph(
                id="evaluate:rmsse_bar",
                figure={} #empty_figure()
            ),
            dcc.Graph(
                id="evaluate:sales_per_agg_bar",
                figure={} #empty_figure()
            ),
            html.Pre(                
                hidden=True,
                id='evaluate:selected_agg_level'
            )
        ],
        id="evaluate:report_first_col"
    )

    second_column = html.Div(
        children=[
            dcc.Graph(
                id="evaluate:residuals",
                figure={} #empty_figure()
            ),
            dcc.Graph(
                id="evaluate:bars_agg_level", # to change
                figure={} #empty_figure()
            ),
        ],
        id="evaluate:report_second_col"
    )

    third_column = html.Div(
        children=[
            dcc.Graph(
                id="evaluate:sample_plots",
                figure={} #empty_figure()
            )
        ],
        id="evaluate:report_third_col"
    )

    ret = html.Div(
        children=[
            html.Div([dcc.Loading(col)], className='four columns')
            for col in [first_column, second_column, third_column]
        ],
        className='row',
        id='evaluate:report',
        style={'display':'none'}
    )

    return ret


@app.callback([
        Output('evaluate:upload', 'children'),
        Output('evaluate:predictions', 'data'),
        Output('evaluate:report', 'style'),
    ],
    [
        Input('evaluate:upload', 'contents')
    ],
    [
        State('evaluate:upload', 'filename'),
        State('evaluate:upload', 'last_modified'),
    ]
)
def receive_prediction_file(content, filename, last_modified):
    empty_response = (UPLOAD_BUTTON_TEXT, [], {'display' : 'none'})
    
    if content is not None:

        try:        
            df = parse_contents(content)
        except Exception as e:
            return empty_response
        upload_button_children = UPLOAD_BUTTON_TEXT + [
            f' - Uploaded {filename} (last modified: {datetime.datetime.fromtimestamp(last_modified)})'
            ]

        data = df.to_dict('records')

        return upload_button_children, data, {'display' : 'block'}
    
    return empty_response


@app.callback([
        Output('evaluate:score', 'children'),
        Output('evaluate:results', 'data'),
        Output('evaluate:residuals', 'children'),
        Output('explore:upload_error_message', 'style')
    ],
    [
        Input('evaluate:predictions', 'data')
    ]
)
def eval_predictions(data):
    if data is not None and len(data) > 0:
        predictions_df = pd.DataFrame.from_records(data)

        try:
            wrmsse, residuals, results = accuracy_evaluator.evaluate_detailed(
                predictions_df
            )
        except Exception:
            return 'N/A', [], [], {'display' : 'block'}

        return wrmsse, results.to_dict('records'), json.dumps(residuals.tolist()), {'display' : 'none'}
    
    return 'N/A', [], [], {'display' : 'none'}


@app.callback([
        Output('evaluate:wrmsse_pie', 'figure'),
        Output('evaluate:rmsse_bar', 'figure'),
        Output('evaluate:sales_per_agg_bar', 'figure'),
    ],
    [
        Input('evaluate:results', 'data')
    ]
)
def render_fa_first_col(data):
    if data is not None and len(data) > 0:
        results_df = pd.DataFrame.from_records(data)

        return plot_evaluate_first_col(results_df)
    
    return {}, {}, {}


@app.callback([
        Output('evaluate:selected_agg_level', 'children')
    ],
    [
        Input('evaluate:wrmsse_pie', 'clickData'),
        Input('evaluate:rmsse_bar', 'clickData'),
        Input('evaluate:sales_per_agg_bar', 'clickData'),
    ]
)
def relayout_clicked_agg_level(clickData1, clickData2, clickData3):
    ctx = dash.callback_context

    if not ctx.triggered:
        return (None,)

    agg_level = ctx.triggered[0]['value']['points'][0]['label']
    
    return (agg_level,)


@app.callback([
        Output('evaluate:residuals', 'figure'),
        Output('evaluate:bars_agg_level', 'figure'),
        Output('evaluate:report_second_col', 'style'),
    ],
    [
        Input('evaluate:selected_agg_level', 'children'),
    ],
    [
        State('evaluate:results', 'data'),
        State('evaluate:residuals', 'children')
    ]
)
def render_fa_second_col(agg_level, results_data, residuals_json):
    if (agg_level is not None and len(agg_level) > 0):

        #
        # 1. get objects
        #

        results_df = pd.DataFrame.from_records(results_data)
        
        residuals_nd = np.array(
            json.loads(residuals_json)
            )

        #
        # 2. filter
        #

        results_df = results_df.loc[results_df["agg_level"]==agg_level]

        agg_level_ids = accuracy_evaluator.agg_level_ids
        index = agg_level_ids.loc[agg_level_ids["agg_level"]==agg_level]\
            .reset_index()['index'].values

        residuals = residuals_nd[index, :].reshape(-1) # filtered residuals

        return plot_evaluate_second_col(agg_level, results_df, residuals) + ({'display': 'block'}, )
    
    return {}, {}, {'display': 'none'}


@app.callback([
        Output('evaluate:sample_plots', 'figure'),
        Output('evaluate:report_third_col', 'style'),
    ],
    [
        Input('evaluate:selected_agg_level', 'children'),
    ],
    [
        State('evaluate:results', 'data'),
        State('evaluate:predictions', 'data')
    ]
)
def render_fa_third_col(agg_level, results_data, predictions_data):

    if (agg_level is not None and len(agg_level) > 0):

        #
        # 1. get objects
        #

        results_df = pd.DataFrame.from_records(results_data)
        
        predictions_df = pd.DataFrame.from_records(predictions_data) 
        groundtruth_df = accuracy_evaluator.groundtruth_df
        lookback_df = accuracy_evaluator.lookback_df

        predictions_values, groundtruth_values, lookback_values = [
            accuracy_evaluator.get_rolled_up_values(df) 
                for df in [predictions_df, groundtruth_df, lookback_df]
                ]

        #
        # 2. filter
        #

        agg_level_ids_df = accuracy_evaluator.agg_level_ids

        # to keep
        results_df = results_df.loc[results_df["agg_level"]==agg_level].nlargest(n=10, columns=['wrmsse']).reset_index(drop=True)

        agg_level_ids_to_plot = results_df['agg_level_id']        
        index = agg_level_ids_df.loc[agg_level_ids_df["agg_level_id"].isin(agg_level_ids_to_plot)]\
            .reset_index()['index'].values

        # to keep
        predictions_values, groundtruth_values, lookback_values = [
            values[index, :] for values in [predictions_values, groundtruth_values, lookback_values]
        ]

        #
        # 3. reshape and melt in one dataframe
        #

        d_cols_lookback = [col for col in lookback_df.columns if re.match(r'd_[0-9]+', col)]
        d_cols_groundtruth = [col for col in groundtruth_df.columns if re.match(r'd_[0-9]+', col)]  
        d_cols_predictions = d_cols_groundtruth
        
        dfs = []

        for values, d_cols, label in zip(
            [lookback_values, predictions_values, groundtruth_values],
            [d_cols_lookback, d_cols_predictions, d_cols_groundtruth],
            ['lookback', 'prediction', 'groundtruth'] # hardcoded
        ):

            df = pd.DataFrame(
                values,
                columns=d_cols
            )

            df['label'] = label

            df = pd.concat(
                [
                    results_df,
                    df
                ],
                axis=1,
            )

            df = pd.melt(
                df,
                id_vars=list(results_df.columns) + ['label'],
                value_vars=d_cols,
                var_name='d',
                value_name='sales'
            )

            dfs.append(df)
        
        to_plot_df = pd.concat(dfs, axis=0, ignore_index=True)

        fig = plot_evaluate_third_col(agg_level, to_plot_df)
        return (fig, {'display': 'block'})
    
    return {}, {'display': 'none'}