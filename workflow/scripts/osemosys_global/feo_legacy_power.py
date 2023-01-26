import requests, json
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import os
import yaml
from OPG_configuration import ConfigFile, ConfigPaths
import logging 
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

def main():

    U = "abhishek0208@gmail.com"
    P = "uh&75gz6s@57p9G7"

    AUTH_URL = "https://auth.feo.transitionzero.org"
    URL = "https://power-legacy.feo.transitionzero.org"

    r = requests.post(AUTH_URL + '/auth/token',
                      data={'username':U,
                            'password':P})

    print(r.status_code)
    print(r.text)

    config_paths = ConfigPaths()
    config = ConfigFile('config')
    input_data_dir = config_paths.input_data_dir
    custom_nodes_dir = config_paths.custom_nodes_dir

    geographic_scope = config.get('geographic_scope')
    
    df_geo_scope = pd.read_csv(os.path.join(input_data_dir,
                                            "iso_codes.csv"))
    iso3_to_iso2 = dict(zip(list(df_geo_scope['alpha-3']),
                              list(df_geo_scope['alpha-2'])))
    iso2_to_iso3 = dict(zip(list(df_geo_scope['alpha-2']),
                              list(df_geo_scope['alpha-3'])))
        
    geographic_scope_iso2 = [iso3_to_iso2.get(c, c) 
                             for c in geographic_scope]

    if r.status_code==200:
        token = json.loads(r.text)['access_token']
        headers = {"Authorization": f"Bearer {token}"}

        df = pd.DataFrame()
        next_page = 0
        while next_page != None:
            params = {'admin_0':geographic_scope_iso2, # UPDATES THIS TO GENERALISED VARIABLE
                      'page':next_page,
                      'limit':100}

            r = requests.get(URL+'/units/',
                            params=params,
                            headers=headers)
            units = json.loads(r.text)['units']
            next_page = json.loads(r.text)['next_page']

            df_temp = pd.DataFrame(units)
            df = pd.concat([df, df_temp])
        
        # Keep only 'operating' plants
        df = df[df['operating_status'] == 'operating']

        # 
        df = df.dropna(subset=['admin_1'])
        
        # Set start_year for each power plant. If not available, set to '0'
        df['START_YEAR'] = df['operation_start'].str.split('-', 
                                                        expand=True)[0]
        df['START_YEAR'].fillna(0, inplace=True)
        
        # Re-order columns
        df = df[['admin_1',
                'primary_fuel',
                'START_YEAR',
                'capacity_mw']]

        # Replace Climate Trace technology codes (ISO2) with FEO tech codes (ISO3)
        df_tech_code = pd.read_csv(os.path.join(input_data_dir,
                                                "naming_convention_tech.csv"))
        tech_code_dict = dict(zip(list(df_tech_code['tech']),
                                list(df_tech_code['code'])))
        
        df['FUEL_TYPE'] = df['primary_fuel'].map(tech_code_dict)

        # Convert admin_1 (e.g. ID-SA) to CUSTOM_NODE format (e.g. IDNSA)
        df['iso2'] = df['admin_1'].str.split('-', 
                                             expand=True)[0]
        df['node'] = df['admin_1'].str.split('-', 
                                             expand=True)[1]
        
        df['CUSTOM_NODE'] = df['iso2'].map(iso2_to_iso3) + df['node']


        df_op_life = pd.read_csv(os.path.join(input_data_dir,
                                                "operational_life.csv"))
        op_life_dict = dict(zip(list(df_op_life['tech']),
                                list(df_op_life['years'])))
        df['op_life'] = df['FUEL_TYPE'].map(op_life_dict)
        df['END_YEAR'] = df['START_YEAR'].astype(int) + df['op_life'].astype(int)
        #df.loc[df['END_YEAR']]
        
        print(df,
              df['admin_1'].unique(), '\n',
              len(df['admin_1'].unique()), '\n',
              df['primary_fuel'].unique(), '\n',
              df['FUEL_TYPE'].unique(),)
        
        try:
            os.makedirs(custom_nodes_dir)
        except FileExistsError:
            pass
        
        df.rename(columns={'capacity_mw':'CAPACITY'},
                  inplace=True)
        df = df[['FUEL_TYPE',
                 'CUSTOM_NODE',
                 'START_YEAR',
                 'END_YEAR',
                 'CAPACITY']]
        df.to_csv(os.path.join(input_data_dir,
                               "custom_nodes",
                               "residual_capacity.csv"),
                  index=None)

if __name__ == "__main__":
    main()
    logging.info('Residual capacity data table for custom nodes created')