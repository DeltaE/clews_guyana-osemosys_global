"""Components shared across tabs"""

from dash import Dash, dcc, html
from typing import List
from osemosys_global.dashboard.components import ids
import osemosys_global.dashboard.constants as const
    
def plot_type_dropdown(**kwargs) -> html.Div:
    
    if "style" in kwargs:
        style = kwargs["style"]
    else:
        style = {}
    
    return html.Div(
        children=[
            html.H3("Plot Type"),
            dcc.Dropdown(
                id=ids.PLOT_TYPE_DROPDOWN,
                options=["Bar", "Line", "Area"],
                value=const._PLOT_TYPE,
                clearable=False
            )
        ],
        style=style
    )