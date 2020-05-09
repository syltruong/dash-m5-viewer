import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from layouts import layout1, layout2
from layout import about
import callbacks

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        [
            html.Div(
                [
                    html.Div(html.H2(children='Dash M5 Viewer'), className='title'),
                    html.Div(
                        [
                            dcc.Link('About the challenge ', href='/about', className="tab"),
                            dcc.Link('Explore the data ', href='/explore', className="tab"),
                            dcc.Link('Evaluate Forecasting Accuracy ', href='/accuracy', className="tab")
                        ],
                        className='tabs'
                    )
                ],
                className='row'
            ),
        ],
        className='top-banner'
    ),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
            [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/about':
        return about.content()
    elif pathname == '/explore':
        return 'explore the data'
    elif pathname == '/accuracy':
        return 'evaluate forecast accuracy'
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=True)