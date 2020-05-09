
import dash_core_components as dcc
import dash_html_components as html

from utils.latex import convert_markdown, read_text_from_file

PATH_TO_MD_1 = 'text/about_1.md'
PATH_TO_MD_2 = 'text/about_2.md'
PATH_TO_IMG = 'assets/ontology_transparent.png'

CLASSNAME = 'about-content'

def content() -> html.Div:
    """
    Return Div for "About" tab

    Returns
    -------
    html.Div
        "About" tab content Div
    """

    ret = html.Div(
        html.Div(
            [
                dcc.Markdown(convert_markdown(read_text_from_file(PATH_TO_MD_1))),
                html.Div(
                    html.Img(src=PATH_TO_IMG, style={ 'width': '75%'}),
                    style={'textAlign': 'center'}
                    ),
                dcc.Markdown(convert_markdown(read_text_from_file(PATH_TO_MD_2))),
            ]
        ),
        className=CLASSNAME
        )
    
    return ret