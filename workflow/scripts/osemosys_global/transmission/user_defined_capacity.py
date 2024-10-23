"""Function to integrate user defined capacities for transmission."""

import pandas as pd
import itertools

from data import get_years

def set_user_defined_capacity_trn(tech_capacity_trn, op_life_dict, 
                                  df_min_cap_invest, df_max_cap_invest, df_res_cap,
                                  df_iar_final, df_oar_final, op_life_base,
                                  cap_cost_base, fix_cost_base, start_year, 
                                  end_year, region_name):
    
    techCapacity_trn = []
    first_year_expansion_dict = {}
    build_rate_dict = {}
    capex_dict = {}
    fix_dict = {}
    build_year_dict = {}
    efficiency_dict = {}

    for idx, tech_params in tech_capacity_trn.items():
        techCapacity_trn.append([idx, tech_params[0], tech_params[1], tech_params[2]])
        build_year_dict[idx] = tech_params[2]
        first_year_expansion_dict[idx] = tech_params[3]
        build_rate_dict[idx] = tech_params[4]
        capex_dict[idx] = tech_params[5]
        fix_dict[idx] = tech_params[6]
        efficiency_dict[idx] = tech_params[7]
                
    tech_capacity_trn_df = pd.DataFrame(techCapacity_trn,
                                    columns=['idx', 'TECHNOLOGY', 'VALUE', 'YEAR'])
    
    tech_capacity_trn_df['REGION'] = region_name
    
    df_min_cap_inv = pd.concat([df_min_cap_invest, tech_capacity_trn_df])
    df_min_cap_inv.drop_duplicates(inplace=True)
    
    max_cap_techs_df = pd.DataFrame(list(itertools.product(list(tech_capacity_trn_df['idx']),
                                             get_years(start_year, end_year))
                           ),
                      columns = ['idx', 
                                 'YEAR']
                      )
    
    max_cap_techs_df['REGION'], max_cap_techs_df['VALUE'] = region_name, ''
    
    max_cap_techs_df = pd.merge(max_cap_techs_df, df_min_cap_inv[['TECHNOLOGY', 'idx']],
                  how='left',
                  on=['idx'])
    
    max_cap_techs_df = max_cap_techs_df[['idx', 'REGION', 'TECHNOLOGY', 'YEAR', 'VALUE']]

    for idx, tech_params in tech_capacity_trn.items():
        max_cap_techs_df.loc[max_cap_techs_df['idx'] == idx, 'BUILD_YEAR'] = build_year_dict.get(idx)
        max_cap_techs_df.loc[max_cap_techs_df['idx'] == idx, 'FIRST_YEAR'] = first_year_expansion_dict.get(idx)
        max_cap_techs_df.loc[max_cap_techs_df['idx'] == idx, 'MAX_BUILD'] = build_rate_dict.get(idx)
            
    max_cap_techs_df.loc[(max_cap_techs_df['YEAR']>=max_cap_techs_df['FIRST_YEAR']),
           'VALUE'] = max_cap_techs_df['MAX_BUILD']
        
    max_cap_techs_df.infer_objects().fillna(0,
              inplace=True)

    max_cap_techs_df = max_cap_techs_df[['REGION',
                                         'TECHNOLOGY',
                                         'YEAR',
                                         'VALUE']]
    
    # Append existing TotalAnnualMaxCapacityInvestment data with MAX_BUILD
    df_max_cap_inv = pd.concat([df_max_cap_invest, max_cap_techs_df]).drop_duplicates()

    # Print TotalAnnualMaxCapacityInvestment.csv with MAX_BUILD
    df_max_cap_inv.drop_duplicates(subset=['REGION', 
                                           'TECHNOLOGY',
                                           'YEAR'],
                                   keep='last',
                                   inplace=True)
        
    # For technologies with start year before model start year, add to ResidualCapacity
    df_res_cap_ud = df_min_cap_inv.copy().loc[df_min_cap_inv.copy()['YEAR'] < min(get_years(start_year, end_year))]
    df_res_cap_ud.rename(columns={'YEAR':'START_YEAR'},
                         inplace=True)
    df_res_cap_ud_final = pd.DataFrame(list(itertools.product(df_res_cap_ud['TECHNOLOGY'].unique(),
                                                              get_years(start_year, end_year))
                                            ),
                                       columns = ['TECHNOLOGY',
                                                  'YEAR']
                                       )
    df_res_cap_ud_final = pd.merge(df_res_cap_ud_final,
                                   df_res_cap_ud,
                                   how='left',
                                   on=['TECHNOLOGY'])
    
    df_res_cap_ud_final['TECH'] = df_res_cap_ud_final['TECHNOLOGY'].str[3:6]
    df_res_cap_ud_final.loc[df_res_cap_ud_final['TECHNOLOGY'].str.contains('TRN'),
                            'TECH'] = 'TRN'
    df_res_cap_ud_final['OP_LIFE'] = df_res_cap_ud_final['TECH'].map(op_life_dict)
    df_res_cap_ud_final['END_YEAR'] = (df_res_cap_ud_final['OP_LIFE'] 
                                       + df_res_cap_ud_final['START_YEAR'])
    df_res_cap_ud_final = df_res_cap_ud_final.loc[df_res_cap_ud_final['YEAR'] 
                                                  >= df_res_cap_ud_final['START_YEAR']]
    df_res_cap_ud_final = df_res_cap_ud_final.loc[df_res_cap_ud_final['YEAR'] 
                                                  <= df_res_cap_ud_final['END_YEAR']]
    df_res_cap_ud_final['REGION'] = region_name
    df_res_cap_ud_final = df_res_cap_ud_final[['REGION',
                                               'TECHNOLOGY',
                                               'YEAR',
                                               'VALUE']]

    df_res_cap = pd.concat([df_res_cap, df_res_cap_ud_final 
                            if not df_res_cap_ud_final.empty else None])

    # Group residual capacities in case user defined technology entries already exist.
    df_res_cap = df_res_cap.groupby(['REGION', 'TECHNOLOGY', 'YEAR']
                                    , as_index = False).sum()

    # For technologies with start year at or after model start year, add to 
    # TotalAnnualMinCapacityInvestment      
    df_min_cap_inv = df_min_cap_inv[['REGION', 'TECHNOLOGY', 'YEAR', 'VALUE']].loc[
        df_min_cap_inv['YEAR'] >= min(get_years(start_year, end_year))]
    
    df_min_cap_inv.drop_duplicates(subset=['REGION', 
                                           'TECHNOLOGY',
                                           'YEAR'],
                                   keep='last',
                                   inplace=True)

    # Add IAR and OAR for custom technologies
    tech_list = list(tech_capacity_trn_df['TECHNOLOGY'].unique())
    df_iar_custom = pd.DataFrame(list(itertools.product(tech_list,
                                                    [1, 2],
                                                    get_years(start_year, end_year))
                                  ),
                             columns = ['TECHNOLOGY',
                                        'MODE_OF_OPERATION',
                                        'YEAR']
                             )
    df_oar_custom = pd.DataFrame(list(itertools.product(tech_list,
                                                    [1, 2],
                                                    get_years(start_year, end_year))
                                  ),
                             columns = ['TECHNOLOGY',
                                        'MODE_OF_OPERATION',
                                        'YEAR']
                             )  
    # IAR in modes 1 and 2 are primary electricity commodity ('ELC*01') in 
    # node_from and node_to, respectively. 
    # OAR is the inverse of the above
    df_iar_custom.loc[df_iar_custom['MODE_OF_OPERATION']==1,
                                    'FUEL'] = ('ELC' + 
                                               df_iar_custom['TECHNOLOGY'].str[3:8] + 
                                               '02')
    df_iar_custom.loc[df_iar_custom['MODE_OF_OPERATION']==2,
                                    'FUEL'] = ('ELC' + 
                                               df_iar_custom['TECHNOLOGY'].str[8:13] + 
                                               '02')
    df_oar_custom.loc[df_iar_custom['MODE_OF_OPERATION']==1,
                                    'FUEL'] = ('ELC' + 
                                               df_oar_custom['TECHNOLOGY'].str[8:13] + 
                                               '01')
    df_oar_custom.loc[df_iar_custom['MODE_OF_OPERATION']==2,
                                    'FUEL'] = ('ELC' + 
                                               df_oar_custom['TECHNOLOGY'].str[3:8] + 
                                               '01')
    
    df_iar_custom['VALUE'] = 1
    
    
    for idx, tech_params in tech_capacity_trn.items():
        df_oar_custom.loc[df_oar_custom['TECHNOLOGY'] == tech_params[0],
                         'VALUE'] = efficiency_dict[idx] / 100

    df_iar_custom['REGION'] = region_name
    df_oar_custom['REGION'] = region_name

    df_iar_custom = df_iar_custom[['REGION', 
                                   'TECHNOLOGY',
                                   'FUEL', 
                                   'MODE_OF_OPERATION',
                                   'YEAR', 
                                   'VALUE',]]
    df_oar_custom = df_oar_custom[['REGION', 
                                   'TECHNOLOGY',
                                   'FUEL', 
                                   'MODE_OF_OPERATION',
                                   'YEAR', 
                                   'VALUE',]]
     
    df_iar = pd.concat([df_iar_final, df_iar_custom])
    df_oar = pd.concat([df_oar_final, df_oar_custom])
    
    df_iar.drop_duplicates(subset=['REGION', 
                                     'TECHNOLOGY',
                                     'FUEL',  
                                     'MODE_OF_OPERATION',
                                     'YEAR'],
                           keep='last',
                           inplace=True)

    df_oar.drop_duplicates(subset=['REGION', 
                                     'TECHNOLOGY',
                                     'FUEL',  
                                     'MODE_OF_OPERATION',
                                     'YEAR'],
                             keep='last',
                             inplace=True)     

    op_life_custom = pd.DataFrame({'TECHNOLOGY': tech_list})

    op_life_custom.loc[op_life_custom['TECHNOLOGY'].str.contains('TRN'),
                       'VALUE'] = op_life_dict.get('TRN')
    op_life_custom['REGION'] = region_name
    op_life_custom = op_life_custom[['REGION',
                                     'TECHNOLOGY',
                                     'VALUE']]

    op_life = pd.concat([op_life_base, op_life_custom])
    op_life.drop_duplicates(subset=['REGION', 
                                    'TECHNOLOGY'],
                            keep='last',
                            inplace=True)
    
    # Update CapitalCost with user-defined costs by transmission line
    cap_cost_trn = pd.DataFrame(list(itertools.product(tech_list,
                                                       get_years(start_year, end_year))),
                                columns = ['TECHNOLOGY',
                                           'YEAR'])
    
    
    for idx, tech_params in tech_capacity_trn.items():
        cap_cost_trn.loc[cap_cost_trn['TECHNOLOGY'] == tech_params[0],
                         'VALUE'] = capex_dict[idx]

    cap_cost_trn['REGION'] = region_name
    cap_cost_trn = cap_cost_trn[['REGION',
                                 'TECHNOLOGY',
                                 'YEAR',
                                 'VALUE']]
    
    fix_cost_trn = cap_cost_trn.copy()
    
    for idx, tech_params in tech_capacity_trn.items():
        fix_cost_trn.loc[fix_cost_trn['TECHNOLOGY'].str.startswith(tech_params[0]),
                         'VALUE'] = fix_dict[idx]

    cap_cost = pd.concat([cap_cost_base, cap_cost_trn])
    cap_cost.drop_duplicates(subset=['REGION', 'TECHNOLOGY', 'YEAR'],
                             keep="last",
                             inplace=True)
    
    fix_cost = pd.concat([fix_cost_base, fix_cost_trn])
    fix_cost.drop_duplicates(subset=['REGION', 'TECHNOLOGY', 'YEAR'],
                             keep="last",
                             inplace=True)
    
    return(df_max_cap_inv, df_min_cap_inv, df_res_cap, 
           df_iar, df_oar, op_life, cap_cost, fix_cost)