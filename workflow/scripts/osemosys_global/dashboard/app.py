"""Main app module. 

Both the layout of the app and callbacks for the app are nested in this file. 
Due to using tabs, with callbacks, seperating the setup, layout creation, and 
callbacks to seperate modules isnt possible. 

See this thread for more information on how the dashboard is structured
https://community.plotly.com/t/dash-graphs-and-callbacks-multiple-tabs-and-modules/58216
"""

from pathlib import Path
from typing import Dict, List
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import i18n 
from osemosys_global.dashboard.components import ids
import osemosys_global.dashboard.components.shared as shared
import osemosys_global.dashboard.components.options_tab as options_tab
import osemosys_global.dashboard.components.map_tab as map_tab
import osemosys_global.dashboard.components.input_data_tab as input_data_tab
import osemosys_global.dashboard.components.result_data_tab as result_data_tab
import osemosys_global.dashboard.constants as const
from osemosys_global.utils import read_csv
from osemosys_global.dashboard.utils import (
    geolocate_nodes, 
    geolocate_lines, 
    get_regions,
    plot_data,
    get_unique_fuels,
    get_unique_techs,
    create_dropdown_options
)
from osemosys_global.OPG_configuration import ConfigPaths

#############################################################################
## APP SETUP
#############################################################################

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

config = ConfigPaths()
LOCALE = "en"
i18n.set("locale",LOCALE)
i18n.load_path.append(Path(config.py_file_dir, "dashboard", "locale"))

# read in data
INPUT_DATA = read_csv(config.scenario_data_dir)
RESULT_DATA = read_csv(config.scenario_results_dir)

# get node/line geolocations
cost_line_expansion_file = Path(config.input_data_dir, "Costs Line expansion.xlsx")
softlink_file = Path(config.input_data_dir, "PLEXOS_World_MESSAGEix_GLOBIOM_Softlink.xlsx")

NODES_DEMAND_CENTER = geolocate_nodes(cost_line_expansion_file, centroid=False)
LINES_DEMAND_CENTER = geolocate_lines(cost_line_expansion_file, NODES_DEMAND_CENTER)

NODES_CENTROID = geolocate_nodes(softlink_file, centroid=True)
LINES_CENTROID = geolocate_lines(cost_line_expansion_file, NODES_CENTROID)

# Shared initializtion values
ALL_REGIONS = get_regions(INPUT_DATA, countries_only=False)
ALL_COUNTRIES = get_regions(INPUT_DATA, countries_only=True)
ALL_YEARS = INPUT_DATA["YEAR"]["VALUE"].to_list()

# create app
app = Dash(external_stylesheets=external_stylesheets)
app.title = i18n.t("OSeMOSYS Global Dashboard")
app.config['suppress_callback_exceptions'] = True # for synching across tabs

#############################################################################
## MAIN APP LAYOUT
#############################################################################

app.layout = html.Div(
    className="app-div",
    children=[
        
        # Store items on the options page for use in other tabs 
        dcc.Store(id=ids.CACHE_REGION_DROPDOWN, data=ALL_REGIONS),
        dcc.Store(id=ids.CACHE_PLOT_THEME_DROPDOWN, data=const._PLOT_THEME),
        dcc.Store(id=ids.CACHE_REGION_COUNTRY_RADIO_BUTTON, data=const._GEOGRAPHIC_SCOPE),
        
        # App header 
        html.H1(app.title),
        html.Hr(),
        dcc.Tabs(
            id=ids.TAB_CONTAINER,
            value=ids.TAB_MAP,
            children=[
                dcc.Tab(
                    label="Options",
                    value=ids.TAB_OPTIONS
                ),
                dcc.Tab(
                    label="Geographic Overview",
                    value=ids.TAB_MAP
                ),
                dcc.Tab(
                    label="Input Data",
                    value=ids.TAB_INPUTS
                ),
                dcc.Tab(
                    label="Results",
                    value=ids.TAB_OUTPUTS
                ),
            ]
        ),
        html.Div(id=ids.TAB_CONTENT)
    ])

#############################################################################
## TAB CACHING CALLBACKS
#############################################################################

@app.callback(
    Output(ids.CACHE_REGION_DROPDOWN, 'data'),
    Input(ids.REGION_DROPDOWN, 'value'),
    State(ids.TAB_CONTAINER, 'value')
)
def store_region_dropdown_cache(region_dropdown, tab):
    return region_dropdown
 
@app.callback(
    Output(ids.CACHE_PLOT_THEME_DROPDOWN, 'data'),
    Input(ids.PLOT_THEME_DROPDOWN, 'value'),
    State(ids.TAB_CONTAINER, 'value')
)
def store_plot_theme_dropdown_cache(plot_theme, tab):
    return plot_theme

@app.callback(
    Output(ids.CACHE_REGION_COUNTRY_RADIO_BUTTON, 'data'),
    Input(ids.REGION_COUNTRY_RADIO_BUTTON, 'value'),
    State(ids.TAB_CONTAINER, 'value')
)
def store_region_country_radio_button_cache(scope, tab):
    return scope

#############################################################################
## TAB CALLBACKS 
#############################################################################

@app.callback(
    Output(ids.TAB_CONTENT, "children"),
    Input(ids.TAB_CONTAINER, "value"),
)
def render_tab_content(tab):
    if tab == ids.TAB_OPTIONS:
        return html.Div(
            className="options-container",
                children=[
                    html.H2("Plotting Options"),
                    options_tab.plot_theme(),
                    options_tab.plotting_level(),
                    html.Hr(),
                    html.H2("Geographic Scope"),
                    options_tab.country_dropdown(countries=ALL_COUNTRIES),
                    options_tab.region_dropdown(regions=ALL_REGIONS),
                ]
        )
    if tab == ids.TAB_MAP:
        style = {'width': '33%', 'display': 'inline-block', "vertical-align":"top"}
        return html.Div(
            className="map-container",
            children=[
                map_tab.node_locations(style=style),
                map_tab.transmission_lines(style=style),
                map_tab.map_theme(style=style),
                map_tab.map_size(style={"margin-top": "25px"}),
                plot_map_callback(),
            ]
        )
    elif tab == ids.TAB_INPUTS:
        style = {'width': '33%', 'display': 'inline-block'}
        return html.Div(
            className="input-data-container",
            children=[
                input_data_tab.parameter_dropdown(style=style),
                input_data_tab.tech_dropdown(
                    input_data=INPUT_DATA, 
                    parameter=const._INPUT_DATA_CHOICE, 
                    geographic_scope=const._GEOGRAPHIC_SCOPE, 
                    style=style
                ),
                shared.plot_type_dropdown(style=style),
                plot_input_data_callback(),
                input_data_tab.year_selector(years=ALL_YEARS),
                input_data_tab.year_slider(years=ALL_YEARS),
            ]
        )
    elif tab == ids.TAB_OUTPUTS:
        style = {'width': '33%', 'display': 'inline-block'}
        return html.Div(
            className="result-data-container",
            children=[
                result_data_tab.variable_dropdown(style=style),
                result_data_tab.tech_dropdown(
                    input_data=RESULT_DATA, 
                    parameter=const._RESULT_DATA_CHOICE, 
                    geographic_scope=const._GEOGRAPHIC_SCOPE, 
                    style=style
                ),
                shared.plot_type_dropdown(style=style),
                plot_result_data_callback(),
                result_data_tab.year_selector(years=ALL_YEARS),
                result_data_tab.year_slider(years=ALL_YEARS),
            ]
        )

#############################################################################
## OPTIONS TAB CALLBACKS 
#############################################################################

@app.callback(
    Output(ids.REGION_DROPDOWN, "value"),
    Output(ids.REGION_DROPDOWN, "options"),
    Input(ids.SELECT_ALL_REGIONS_BUTTON, "n_clicks"),
    Input(ids.COUNTRY_DROPDOWN, "value"),
)
def select_regions(_: int, countries : list[str],) -> list[str]:
    available_regions = [region for region in ALL_REGIONS if region[:3] in countries]
    return available_regions, available_regions

@app.callback(
    Output(ids.COUNTRY_DROPDOWN, "value"),
    Input(ids.SELECT_ALL_COUNTRIES_BUTTON, "n_clicks"),
)
def select_all_countries(_: int) -> list[str]:
    return ALL_COUNTRIES

#############################################################################
## MAP TAB CALLBACKS 
#############################################################################

@app.callback(
    Output(ids.MAP, "children"),
    Input(ids.CACHE_REGION_DROPDOWN, "data"),
    Input(ids.MAP_SIZE_SLIDER, "value"),
    Input(ids.NODE_TRANSMISSION_RADIO_BUTTON, "value"),
    Input(ids.MAP_THEME_DROPDOWN, "value"),
    Input(ids.NODE_LOCATION_RADIO_BUTTON, "value")
)
def plot_map_callback(
    regions: list[str] = ALL_REGIONS,
    size: int = const._MAP_ELEMENTS_SIZE,
    show_lines: str = const._TRANSMISSION_LINE, 
    map_theme: str = const._MAP_THEME,
    node_location: str = const._NODE_LOCATION,
) -> html.Div:
    
    if node_location == "Centroid":
        nodes = NODES_CENTROID
        lines = LINES_CENTROID
    else:
        nodes = NODES_DEMAND_CENTER
        lines = LINES_DEMAND_CENTER
    
    return map_tab.plot_map(regions, size, show_lines, map_theme, nodes, lines)

#############################################################################
## INPUT DATA TAB CALLBACKS 
#############################################################################

@app.callback(
    Output(ids.INPUT_DATA_CHART, "children"),
    inputs=dict(
        regions=Input(ids.CACHE_REGION_DROPDOWN, "data"),
        plot_theme=Input(ids.CACHE_PLOT_THEME_DROPDOWN, "data"),
        geographic_scope=Input(ids.CACHE_REGION_COUNTRY_RADIO_BUTTON, "data"),
        years=Input(ids.INPUT_YEAR_SLIDER, "value"),
        year=Input(ids.INPUT_YEAR_SELECTOR, "value"),
        plot_type=Input(ids.PLOT_TYPE_DROPDOWN, "value"),
        parameter=Input(ids.INPUT_DATA_DROPDOWN, "value"),
        tech_fuel=Input(ids.INPUT_DATA_TECH_DROPDOWN, "value")
    )
)
def plot_input_data_callback(
    countries: list[str] = ALL_COUNTRIES,
    regions: list[str] = ALL_REGIONS,
    plot_theme: str = const._PLOT_THEME,
    geographic_scope: str = const._GEOGRAPHIC_SCOPE,
    years: list[int] = ALL_YEARS, 
    year: int = ALL_YEARS[0],
    plot_type: str = const._PLOT_TYPE,
    parameter: str = "SpecifiedAnnualDemand",
    tech_fuel: str = "ELC",
) -> html.Div:
    """Generic function for plotting input data"""
    
    # Determine if year dependent data 
    if const.PARAM_CONFIG[parameter]["xaxis"] == "YEAR":
        years = years
    else:
        years = [year]
    
    return plot_data(
        data_store=INPUT_DATA,
        countries=countries,
        regions=regions,
        plot_theme=plot_theme,
        geographic_scope=geographic_scope,
        years=years,
        plot_type=plot_type,
        parameter=parameter,
        tech_fuel_filter=tech_fuel,
        config=const.PARAM_CONFIG,
        div_id=ids.INPUT_DATA_CHART
    )
    
@app.callback(
    Output(ids.INPUT_DATA_TECH_DROPDOWN, "options"),
    Output(ids.INPUT_DATA_TECH_DROPDOWN, "value"),
    Input(ids.INPUT_DATA_DROPDOWN, "value"),
    Input(ids.CACHE_REGION_COUNTRY_RADIO_BUTTON, "data")
)
def tech_filter_dropdown_options_callback(parameter: str, geographic_scope: str) -> html.Div:
    if const.PARAM_CONFIG[parameter]["groupby"] == "TECHNOLOGY":
        options = get_unique_techs(INPUT_DATA[parameter])
    else:
        options = get_unique_fuels(INPUT_DATA[parameter])
        
    dropdown_options = create_dropdown_options(options)
    
    if geographic_scope == "System":
        dropdown_options.insert(0, {"label":"All", "value":"all"})

    return dropdown_options, dropdown_options[0]["value"]

@app.callback(
    Output(ids.INPUT_YEAR_SLIDER, "style"),
    Output(ids.INPUT_YEAR_SELECTOR, "style"),
    Input(ids.INPUT_DATA_DROPDOWN, "value")
)
def input_slider_visibility(parameter:str):
    if const.PARAM_CONFIG[parameter]["xaxis"] == "YEAR":
        return {"display": "block"}, {"display": "none"}
    else:
        return {"display": "none"}, {"display": "block"}

#############################################################################
## RESULT DATA TAB CALLBACKS 
#############################################################################

@app.callback(
    Output(ids.RESULT_DATA_CHART, "children"),
    inputs=dict(
        regions=Input(ids.CACHE_REGION_DROPDOWN, "data"),
        plot_theme=Input(ids.CACHE_PLOT_THEME_DROPDOWN, "data"),
        geographic_scope=Input(ids.CACHE_REGION_COUNTRY_RADIO_BUTTON, "data"),
        years=Input(ids.RESULT_YEAR_SLIDER, "value"),
        year=Input(ids.RESULT_YEAR_SELECTOR, "value"),
        plot_type=Input(ids.PLOT_TYPE_DROPDOWN, "value"),
        parameter=Input(ids.RESULT_DATA_DROPDOWN, "value"),
        tech_fuel=Input(ids.RESULT_DATA_TECH_DROPDOWN, "value")
    )
)
def plot_result_data_callback(
    countries: list[str] = ALL_COUNTRIES,
    regions: list[str] = ALL_REGIONS,
    plot_theme: str = const._PLOT_THEME,
    geographic_scope: str = const._GEOGRAPHIC_SCOPE,
    years: list[int] = ALL_YEARS, 
    year: int = ALL_YEARS[0],
    plot_type: str = const._PLOT_TYPE,
    parameter: str = "AnnualTechnologyEmission",
    tech_fuel: str = "all",
) -> html.Div:
    """Generic function for plotting input data"""
    
    # Determine if year dependent data 
    if const.RESULT_CONFIG[parameter]["xaxis"] == "YEAR":
        years = years
    else:
        years = [year]
    
    return plot_data(
        data_store=RESULT_DATA,
        countries=countries,
        regions=regions,
        plot_theme=plot_theme,
        geographic_scope=geographic_scope,
        years=years,
        plot_type=plot_type,
        parameter=parameter,
        tech_fuel_filter=tech_fuel,
        config=const.RESULT_CONFIG,
        div_id=ids.RESULT_DATA_CHART
    )

@app.callback(
    Output(ids.RESULT_DATA_TECH_DROPDOWN, "options"),
    Output(ids.RESULT_DATA_TECH_DROPDOWN, "value"),
    Input(ids.RESULT_DATA_DROPDOWN, "value"),
    Input(ids.CACHE_REGION_COUNTRY_RADIO_BUTTON, "data")
)
def tech_filter_dropdown_options_callback(variable: str, geographic_scope: str) -> html.Div:
    if const.RESULT_CONFIG[variable]["groupby"] == "TECHNOLOGY":
        options = get_unique_techs(RESULT_DATA[variable])
    else:
        options = get_unique_fuels(RESULT_DATA[variable])
        
    dropdown_options = create_dropdown_options(options)
    
    if geographic_scope == "System":
        dropdown_options.insert(0, {"label":"All", "value":"all"})

    return dropdown_options, dropdown_options[0]["value"]

@app.callback(
    Output(ids.RESULT_YEAR_SLIDER, "style"),
    Output(ids.RESULT_YEAR_SELECTOR, "style"),
    Input(ids.RESULT_DATA_DROPDOWN, "value")
)
def input_slider_visibility(parameter:str):
    if const.RESULT_CONFIG[parameter]["xaxis"] == "YEAR":
        return {"display": "block"}, {"display": "none"}
    else:
        return {"display": "none"}, {"display": "block"}

if __name__ == '__main__':
    app.run(debug=True)

