import pandas as pd
import itertools
import os
from pathlib import Path
from typing import Dict
from OPG_configuration import ConfigFile, ConfigPaths
from visualisation.utils import transform_ts, powerplant_filter
from visualisation.constants import DAYS_PER_MONTH, MONTH_NAMES
pd.set_option('mode.chained_assignment', None)


def main():
    '''Creates summaries of results'''

    config_paths = ConfigPaths()
    scenario_result_summaries_dir = config_paths.scenario_result_summaries_dir

    # Check for output directory
    try:
        os.makedirs(scenario_result_summaries_dir)
    except FileExistsError:
        pass
    
    input_data = read_data(config_paths.scenario_data_dir)
    result_data = read_data(config_paths.scenario_results_dir)
    save_dir = config_paths.scenario_result_summaries_dir

    # SUMMARISE RESULTS
    headline_metrics(input_data, result_data, save_dir)
    capacity_summary(input_data, result_data, save_dir)
    generation_summary(input_data, result_data, save_dir)
    generation_by_node_summary(input_data, result_data, save_dir)
    trade_flows(input_data, result_data, save_dir)


def renewables_filter(df):
    '''Function to filter and keep only renewable
    technologies'''
    renewables = ['BIO', 'CSP', 'GEO', 'HYD', 'SPV', 'WAS', 'WAV', 'WON', 'WOF']
    df = df[~df.TECHNOLOGY.str.contains('TRN')]
    df = df.loc[(df.TECHNOLOGY.str.startswith('PWR')) &
                (df.TECHNOLOGY.str[3:6].isin(renewables))
                ]
    return df


def fossil_filter(df):
    '''Function to filter and keep only fossil fuel
    technologies'''
    fossil_fuels = ['COA', 'COG', 'OCG', 'CCG', 'PET', 'OIL', 'OTH']
    df = df[~df.TECHNOLOGY.str.contains('TRN')]
    df = df.loc[(df.TECHNOLOGY.str.startswith('PWR')) &
                (df.TECHNOLOGY.str[3:6].isin(fossil_fuels))
                ]
    return df


def headline_metrics(input_data: Dict[str,pd.DataFrame], result_data: Dict[str,pd.DataFrame], save_dir: str):
    '''Function to summarise metrics for:
       1. Total emissions
       2. Average RE share
       3. Average cost of electricity generation
       4. Total system cost
       5. Average fossil fuel share
       
    Arguments:
        input_data: Dict[str,pd.DataFrame]
            Internal datastore for input data
        result_data: Dict[str,pd.DataFrame]
            Internal datastore for results
        save_dir: str
            Location to save table
       '''

    # GET RESULTS

    df_metrics = pd.DataFrame(columns=['Metric', 'Unit', 'Value'])
    df_metrics['Metric'] = ['Emissions',
                            'RE Share',
                            'Total System Cost',
                            'Cost of electricity',
                            'Fossil fuel share']
    df_metrics['Unit'] = ['Million tonnes of CO2-eq.',
                          '%',
                          'Billion $',
                          '$/MWh',
                          '%']

    # Emissions
    df_emissions = result_data["AnnualEmissions"]
    emissions_total = df_emissions.VALUE.sum()
    df_metrics.loc[df_metrics['Metric'].str.startswith('Emissions'),
                   'Value'] = emissions_total.round(0)

    # Shares of RE and Fossil fuels
    df_shares = result_data["ProductionByTechnologyAnnual"]
    df_shares = df_shares[~df_shares.TECHNOLOGY.str.contains('TRN')]
    gen_total = df_shares.loc[df_shares.TECHNOLOGY.str.startswith('PWR'),
                              'VALUE'].sum()

    # RE Share
    df_re_share = renewables_filter(df_shares)
    re_total = df_re_share.VALUE.sum()
    re_share = re_total / gen_total
    df_metrics.loc[df_metrics['Metric'].str.startswith('RE Share'),
                   'Value'] = (re_share*100).round(0)

    # Fossil Fuel Share
    df_ff_share = fossil_filter(df_shares)
    ff_total = df_ff_share.VALUE.sum()
    ff_share = ff_total / gen_total
    df_metrics.loc[df_metrics['Metric'].str.startswith('Fossil fuel share'),
                   'Value'] = (ff_share*100).round(0)

    # Total System Cost
    df_system_cost = result_data["TotalDiscountedCost"]
    system_cost_total = df_system_cost.VALUE.sum()
    df_metrics.loc[df_metrics['Metric'].str.startswith('Total System Cost'),
                   'Value'] = (system_cost_total/1000).round(0)

    # Cost of electricity generation
    df_demand = result_data["Demand"]
    demand_total = df_demand.VALUE.sum()  # Total demand in TWh
    df_metrics.loc[df_metrics['Metric'].str.startswith('Cost of electricity'),
                   'Value'] = (system_cost_total/(demand_total*0.2778)).round(0)

    return df_metrics.to_csv(os.path.join(save_dir,'Metrics.csv'),index=None)

def capacity_summary(input_data: Dict[str,pd.DataFrame], result_data: Dict[str,pd.DataFrame], save_dir: str):
    """Capacity Summary Metrics 
    
    Arguments:
        input_data: Dict[str,pd.DataFrame]
            Internal datastore for input data
        result_data: Dict[str,pd.DataFrame]
            Internal datastore for results
        save_dir: str
            Location to save table
    """

    # Capacities
    df_capacities = result_data["TotalCapacityAnnual"]

    df_capacities['NODE'] = (df_capacities['TECHNOLOGY'].str[6:9] +
                             '-' +
                             df_capacities['TECHNOLOGY'].str[9:11])
    df_capacities = powerplant_filter(df_capacities, country=None)
    df_capacities = df_capacities.groupby(['NODE', 'LABEL', 'YEAR'],
                                          as_index=False)['VALUE'].sum()
    df_capacities = df_capacities.sort_values(by=['YEAR',
                                                  'NODE',
                                                  'LABEL'])
    df_capacities['VALUE'] = df_capacities['VALUE'].round(2)

    return df_capacities.to_csv(os.path.join(save_dir,'Capacities.csv'),index=None)


def generation_summary(input_data: Dict[str,pd.DataFrame], result_data: Dict[str,pd.DataFrame], save_dir: str):
    """Generation Summary Metrics 
    
    Arguments:
        input_data: Dict[str,pd.DataFrame]
            Internal datastore for input data
        result_data: Dict[str,pd.DataFrame]
            Internal datastore for results
        save_dir: str
            Location to save table
    """

    # Generation
    df_generation = result_data["ProductionByTechnology"]
    df_generation = powerplant_filter(df_generation, country=None)
    df_generation = transform_ts(input_data, df_generation)
    df_generation = pd.melt(df_generation,
                            id_vars=['MONTH', 'HOUR', 'YEAR'],
                            value_vars=[x for x in df_generation.columns
                                        if x not in ['MONTH', 'HOUR', 'YEAR']],
                            value_name='VALUE')
    df_generation['VALUE'] = df_generation['VALUE'].round(2)
    df_generation = df_generation[['YEAR', 'MONTH', 'HOUR', 'LABEL', 'VALUE']]

    return df_generation.to_csv(os.path.join(save_dir,'Generation.csv'),index=None)


def generation_by_node_summary(input_data: Dict[str,pd.DataFrame], result_data: Dict[str,pd.DataFrame], save_dir: str):
    """Generation Summary Metrics by Node
    
    Arguments:
        input_data: Dict[str,pd.DataFrame]
            Internal datastore for input data
        result_data: Dict[str,pd.DataFrame]
            Internal datastore for results
        save_dir: str
            Location to save table
    """
    config = ConfigFile('config')

    # Generation
    df_gen_by_node = result_data["ProductionByTechnology"]
    # GET TECHS TO PLOT
    generation = list(df_gen_by_node.TECHNOLOGY.unique())
    df_gen_by_node['NODE'] = (df_gen_by_node['TECHNOLOGY'].str[6:11])
    df_gen_by_node = powerplant_filter(df_gen_by_node, country=None)

    # GET TIMESLICE DEFINITION

    seasons_raw = config.get('seasons')
    seasonsData = []

    for s, months in seasons_raw.items():
        for month in months:
            seasonsData.append([month, s]) 
    seasons_df = pd.DataFrame(seasonsData, 
                              columns=['month', 'season'])
    seasons_df = seasons_df.sort_values(by=['month']).reset_index(drop=True)
    dayparts_raw = config.get('dayparts')
    daypartData = []
    for dp, hr in dayparts_raw.items():
        daypartData.append([dp, hr[0], hr[1]])
    dayparts_df = pd.DataFrame(daypartData,
                               columns=['daypart', 'start_hour', 'end_hour'])
    timeshift = config.get('timeshift')
    dayparts_df['start_hour'] = dayparts_df['start_hour'].map(lambda x: apply_timeshift(x, timeshift))
    dayparts_df['end_hour'] = dayparts_df['end_hour'].map(lambda x: apply_timeshift(x, timeshift))

    month_names = MONTH_NAMES
    days_per_month = DAYS_PER_MONTH

    seasons_df['month_name'] = seasons_df['month'].map(month_names)
    seasons_df['days'] = seasons_df['month_name'].map(days_per_month)
    seasons_df_grouped = seasons_df.groupby(['season'],
                                            as_index=False)['days'].sum()
    days_dict = dict(zip(list(seasons_df_grouped['season']),
                         list(seasons_df_grouped['days'])
                         )
                     )
    seasons_df['days'] = seasons_df['season'].map(days_dict)

    years = config.get_years()

    seasons_dict = dict(zip(list(seasons_df['month']),
                            list(seasons_df['season'])
                            )
                        )

    dayparts_dict = {i: [j, k]
                     for i, j, k
                     in zip(list(dayparts_df['daypart']),
                            list(dayparts_df['start_hour']),
                            list(dayparts_df['end_hour'])
                            )
                     }

    hours_dict = {i: abs(k-j)
                  for i, j, k
                  in zip(list(dayparts_df['daypart']),
                         list(dayparts_df['start_hour']),
                         list(dayparts_df['end_hour'])
                         )
                  }

    months = list(seasons_dict)
    hours = list(range(1, 25))

    # APPLY TRANSFORMATION
    df_ts_template = pd.DataFrame(list(itertools.product(generation,
                                                         months,
                                                         hours,
                                                         years)
                                       ),
                                  columns=['TECHNOLOGY',
                                           'MONTH',
                                           'HOUR',
                                           'YEAR']
                                  )

    df_ts_template = df_ts_template.sort_values(by=['TECHNOLOGY', 'YEAR'])
    df_ts_template['SEASON'] = df_ts_template['MONTH'].map(seasons_dict)
    df_ts_template['DAYS'] = df_ts_template['SEASON'].map(days_dict)
    df_ts_template['YEAR'] = df_ts_template['YEAR'].astype(int)
    df_ts_template = powerplant_filter(df_ts_template)

    for daypart in dayparts_dict:
        if dayparts_dict[daypart][0] > dayparts_dict[daypart][1]: # loops over 24hrs
            df_ts_template.loc[(df_ts_template['HOUR'] >= dayparts_dict[daypart][0]) |
                          (df_ts_template['HOUR'] < dayparts_dict[daypart][1]),
                          'DAYPART'] = daypart
        else:
            df_ts_template.loc[(df_ts_template['HOUR'] >= dayparts_dict[daypart][0]) &
                               (df_ts_template['HOUR'] < dayparts_dict[daypart][1]),
                               'DAYPART'] = daypart

    df_ts_template = df_ts_template.drop_duplicates()

    df_gen_by_node['SEASON'] = df_gen_by_node['TIMESLICE'].str[0:2]
    df_gen_by_node['DAYPART'] = df_gen_by_node['TIMESLICE'].str[2:]
    df_gen_by_node['YEAR'] = df_gen_by_node['YEAR'].astype(int)
    df_gen_by_node.drop(['REGION', 'TIMESLICE'],
                        axis=1,
                        inplace=True)

    df_gen_by_node = pd.merge(df_gen_by_node,
                              df_ts_template,
                              how='left',
                              on=['LABEL', 'SEASON', 'DAYPART', 'YEAR']).dropna()
    df_gen_by_node['HOUR_COUNT'] = df_gen_by_node['DAYPART'].map(hours_dict)
    df_gen_by_node['VALUE'] = (df_gen_by_node['VALUE'].mul(1e6))/(df_gen_by_node['DAYS']*df_gen_by_node['HOUR_COUNT'].mul(3600))

    df_gen_by_node = df_gen_by_node.pivot_table(index=['MONTH', 'HOUR', 'YEAR', 'NODE'],
                                              columns='LABEL',
                                              values='VALUE',
                                              aggfunc='sum').reset_index().fillna(0)

    df_gen_by_node['MONTH'] = pd.Categorical(df_gen_by_node['MONTH'],
                                            categories=months,
                                            ordered=True)
    df_gen_by_node = df_gen_by_node.sort_values(by=['MONTH', 'HOUR'])
    '''
    df_generation = pd.melt(df_generation,
                            id_vars=['MONTH', 'HOUR', 'YEAR', 'NODE'],
                            value_vars=[x for x in df_generation.columns
                                        if x not in ['MONTH', 'HOUR', 'YEAR', 'NODE']],
                            value_name='VALUE')
    '''
    cols_round = [x for x in df_gen_by_node.columns
                  if x not in ['MONTH', 'HOUR', 'YEAR', 'NODE']]
    df_gen_by_node[cols_round] = df_gen_by_node[cols_round].round(2)

    return df_gen_by_node.to_csv(os.path.join(save_dir,'Generation_By_Node.csv'),index=None)

def trade_flows(input_data: Dict[str,pd.DataFrame], result_data: Dict[str,pd.DataFrame], save_dir: str):
    """Trade flow Summary Metrics
    
    Arguments:
        input_data: Dict[str,pd.DataFrame]
            Internal datastore for input data
        result_data: Dict[str,pd.DataFrame]
            Internal datastore for results
        save_dir: str
            Location to save table
    """

    config = ConfigFile('config')

    # GET TECHS TO PLOT

    df_gen = input_data["TECHNOLOGY"]
    df_gen = df_gen[df_gen.VALUE.str.startswith('TRN')]
    interconnections = list(df_gen.VALUE.unique())

    if len(interconnections) > 0:
        # GET TIMESLICE DEFINITION

        seasons_raw = config.get('seasons')
        seasonsData = []

        for s, months in seasons_raw.items():
            for month in months:
                seasonsData.append([month, s]) 
        seasons_df = pd.DataFrame(seasonsData, 
                                columns=['month', 'season'])
        seasons_df = seasons_df.sort_values(by=['month']).reset_index(drop=True)
        dayparts_raw = config.get('dayparts')
        daypartData = []
        for dp, hr in dayparts_raw.items():
            daypartData.append([dp, hr[0], hr[1]])
        dayparts_df = pd.DataFrame(daypartData,
                                columns=['daypart', 'start_hour', 'end_hour'])
        timeshift = config.get('timeshift')
        dayparts_df['start_hour'] = dayparts_df['start_hour'].map(lambda x: apply_timeshift(x, timeshift))
        dayparts_df['end_hour'] = dayparts_df['end_hour'].map(lambda x: apply_timeshift(x, timeshift))

        month_names = MONTH_NAMES
        days_per_month = DAYS_PER_MONTH

        seasons_df['month_name'] = seasons_df['month'].map(month_names)
        seasons_df['days'] = seasons_df['month_name'].map(days_per_month)
        seasons_df_grouped = seasons_df.groupby(['season'],
                                                as_index=False)['days'].sum()
        days_dict = dict(zip(list(seasons_df_grouped['season']),
                            list(seasons_df_grouped['days'])
                            )
                        )
        seasons_df['days'] = seasons_df['season'].map(days_dict)

        years = config.get_years()

        seasons_dict = dict(zip(list(seasons_df['month']),
                                list(seasons_df['season'])
                                )
                            )

        dayparts_dict = {i: [j, k]
                        for i, j, k
                        in zip(list(dayparts_df['daypart']),
                                list(dayparts_df['start_hour']),
                                list(dayparts_df['end_hour'])
                                )
                        }

        hours_dict = {i: abs(k-j)
                    for i, j, k
                    in zip(list(dayparts_df['daypart']),
                            list(dayparts_df['start_hour']),
                            list(dayparts_df['end_hour'])
                            )
                    }

        months = list(seasons_dict)
        hours = list(range(1, 25))

        # APPLY TRANSFORMATION

        df_ts_template = pd.DataFrame(list(itertools.product(interconnections,
                                                            months,
                                                            hours,
                                                            years)
                                        ),
                                    columns=['TECHNOLOGY',
                                            'MONTH',
                                            'HOUR',
                                            'YEAR']
                                    )

        df_ts_template = df_ts_template.sort_values(by=['TECHNOLOGY', 'YEAR'])
        df_ts_template['SEASON'] = df_ts_template['MONTH'].map(seasons_dict)
        df_ts_template['DAYS'] = df_ts_template['SEASON'].map(days_dict)
        df_ts_template['YEAR'] = df_ts_template['YEAR'].astype(int)

        for daypart in dayparts_dict:
            if dayparts_dict[daypart][0] > dayparts_dict[daypart][1]: # loops over 24hrs
                df_ts_template.loc[(df_ts_template['HOUR'] >= dayparts_dict[daypart][0]) |
                            (df_ts_template['HOUR'] < dayparts_dict[daypart][1]),
                            'DAYPART'] = daypart
            else:
                df_ts_template.loc[(df_ts_template['HOUR'] >= dayparts_dict[daypart][0]) &
                        (df_ts_template['HOUR'] < dayparts_dict[daypart][1]),
                        'DAYPART'] = daypart

        df_ts_template = df_ts_template.drop_duplicates()

        # Trade flows
        df = result_data["TotalAnnualTechnologyActivityByMode"]

        df['SEASON'] = df['TIMESLICE'].str[0:2]
        df['DAYPART'] = df['TIMESLICE'].str[2:]
        df['YEAR'] = df['YEAR'].astype(int)
        df.drop(['REGION', 'TIMESLICE'],
                axis=1,
                inplace=True)

        df = pd.merge(df,
                    df_ts_template,
                    how='left',
                    on=['TECHNOLOGY', 'SEASON', 'DAYPART', 'YEAR']).dropna()

        df['HOUR_COUNT'] = df['DAYPART'].map(hours_dict)
        df['VALUE'] = (df['VALUE'].mul(1e6))/(df['DAYS']*df['HOUR_COUNT'].mul(3600))

        df = df[['YEAR',
                'MONTH',
                'HOUR',
                'TECHNOLOGY',
                'MODE_OF_OPERATION',
                'VALUE']]
        df['MODE_OF_OPERATION'] = df['MODE_OF_OPERATION'].astype(int)
        df.loc[df['MODE_OF_OPERATION'] == 2, 'VALUE'] *= -1

        df['NODE_1'] = df.TECHNOLOGY.str[3:8]
        df['NODE_2'] = df.TECHNOLOGY.str[8:13]
        df.drop(columns=['TECHNOLOGY', 'MODE_OF_OPERATION'],
                axis=1,
                inplace=True)

        df['MONTH'] = pd.Categorical(df['MONTH'],
                                    categories=months,
                                    ordered=True)
        df = df.sort_values(by=['MONTH', 'HOUR'])
        df['VALUE'] = df['VALUE'].round(2)
        df = df[['YEAR',
                'MONTH',
                'HOUR',
                'NODE_1',
                'NODE_2',
                'VALUE']]
    else:
        df = pd.DataFrame(columns=['YEAR',
                                   'MONTH',
                                   'HOUR',
                                   'NODE_1',
                                   'NODE_2',
                                   'VALUE']
                         )
    return df.to_csv(os.path.join(save_dir,'TradeFlows.csv'),index=None)

def apply_timeshift(x, timeshift):
    '''Applies timeshift to organize dayparts.
    
    Args:
        x = Value between 0-24
        timeshift = value offset from UTC (-11 -> +12)'''

    x += timeshift
    if x > 23:
        return x - 24
    elif x < 0:
        return x + 24
    else:
        return x

def read_data(dirpath: str) -> Dict[str,pd.DataFrame]:
    """Reads in result CSVs
    
    Replace with ReadCSV in otoole v1.0
    """
    data = {}
    files = [Path(x) for x in Path(dirpath).iterdir()]
    for f in files:
        data[f.stem] = pd.read_csv(f)
    return data

if __name__ == '__main__':
    main()
