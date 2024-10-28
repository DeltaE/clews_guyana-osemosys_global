"""Function to integrate user defined capacities for storage."""

import pandas as pd
import itertools

from data import get_years

def set_user_defined_capacity_sto(tech_capacity_sto,# op_life_dict, 
                                  #df_min_cap_invest, df_max_cap_invest, df_res_cap,
                                  df_oar_base, 
                                  #op_life_base,
                                  cap_cost_base, 
                                  #fix_cost_base, start_year, 
                                  #end_year, 
                                  region_name
                                  ):
    
    techCapacity_sto = []
    first_year_expansion_dict = {}
    build_rate_dict = {}
    capex_dict = {}
    build_year_dict = {}
    efficiency_dict = {}

    for idx, tech_params in tech_capacity_sto.items():
        techCapacity_sto.append([idx, tech_params[0], tech_params[1], tech_params[2]])
        build_year_dict[idx] = tech_params[2]
        first_year_expansion_dict[idx] = tech_params[3]
        build_rate_dict[idx] = tech_params[4]
        capex_dict[idx] = tech_params[5]
        efficiency_dict[idx] = tech_params[6]
                
    tech_capacity_sto_df = pd.DataFrame(techCapacity_sto,
                                    columns=['idx', 'TECHNOLOGY', 'VALUE', 'YEAR'])
    
    tech_capacity_sto_df['REGION'] = region_name
    
   # df_min_cap_inv = pd.concat([df_min_cap_invest, tech_capacity_sto_df])
  #  df_min_cap_inv.drop_duplicates(inplace=True)
    
  #  max_cap_techs_df = pd.DataFrame(list(itertools.product(list(tech_capacity_sto_df['idx']),
 #                                            get_years(start_year, end_year))
 #                          ),
 #                     columns = ['idx', 
 #                                'YEAR']
  #                    )
    
   # max_cap_techs_df['REGION'], max_cap_techs_df['VALUE'] = region_name, ''
    
  #  max_cap_techs_df = pd.merge(max_cap_techs_df, df_min_cap_inv[['TECHNOLOGY', 'idx']],
  #                how='left',
  #                on=['idx'])
    
  #  max_cap_techs_df = max_cap_techs_df[['idx', 'REGION', 'TECHNOLOGY', 'YEAR', 'VALUE']]

  #  for idx, tech_params in tech_capacity_sto.items():
  #      max_cap_techs_df.loc[max_cap_techs_df['idx'] == idx, 'BUILD_YEAR'] = build_year_dict.get(idx)
  #      max_cap_techs_df.loc[max_cap_techs_df['idx'] == idx, 'FIRST_YEAR'] = first_year_expansion_dict.get(idx)
  #      max_cap_techs_df.loc[max_cap_techs_df['idx'] == idx, 'MAX_BUILD'] = build_rate_dict.get(idx)
            
  #  max_cap_techs_df.loc[(max_cap_techs_df['YEAR']>=max_cap_techs_df['FIRST_YEAR']),
  #         'VALUE'] = max_cap_techs_df['MAX_BUILD']
        
 #   max_cap_techs_df.infer_objects().fillna(0,
  #            inplace=True)

  #  max_cap_techs_df = max_cap_techs_df[['REGION',
   #                                      'TECHNOLOGY',
   #                                      'YEAR',
   #                                      'VALUE']]
    
    # Append existing TotalAnnualMaxCapacityInvestment data with MAX_BUILD
  #  df_max_cap_inv = pd.concat([df_max_cap_invest, max_cap_techs_df]).drop_duplicates()

    # Print TotalAnnualMaxCapacityInvestment.csv with MAX_BUILD
  #  df_max_cap_inv.drop_duplicates(subset=['REGION', 
   #                                        'TECHNOLOGY',
   #                                        'YEAR'],
   #                                keep='last',
   #                                inplace=True)
        
    # For technologies with start year before model start year, add to ResidualCapacity
  #  df_res_cap_ud = df_min_cap_inv.copy().loc[df_min_cap_inv.copy()['YEAR'] < min(get_years(start_year, end_year))]
  #  df_res_cap_ud.rename(columns={'YEAR':'START_YEAR'},
  #                       inplace=True)
 #   df_res_cap_ud_final = pd.DataFrame(list(itertools.product(df_res_cap_ud['TECHNOLOGY'].unique(),
  #                                                            get_years(start_year, end_year))
   #                                         ),
  #                                     columns = ['TECHNOLOGY',
  #                                                'YEAR']
  #                                     )
   # df_res_cap_ud_final = pd.merge(df_res_cap_ud_final,
  #                                 df_res_cap_ud,
  #                                 how='left',
  #                                 on=['TECHNOLOGY'])
    
  #  df_res_cap_ud_final['TECH'] = df_res_cap_ud_final['TECHNOLOGY'].str[3:6]
  #  df_res_cap_ud_final.loc[df_res_cap_ud_final['TECHNOLOGY'].str.contains('TRN'),
 #                           'TECH'] = 'TRN'
  #  df_res_cap_ud_final['OP_LIFE'] = df_res_cap_ud_final['TECH'].map(op_life_dict)
  #  df_res_cap_ud_final['END_YEAR'] = (df_res_cap_ud_final['OP_LIFE'] 
  #                                     + df_res_cap_ud_final['START_YEAR'])
  #  df_res_cap_ud_final = df_res_cap_ud_final.loc[df_res_cap_ud_final['YEAR'] 
  #                                                >= df_res_cap_ud_final['START_YEAR']]
  #  df_res_cap_ud_final = df_res_cap_ud_final.loc[df_res_cap_ud_final['YEAR'] 
  #                                                <= df_res_cap_ud_final['END_YEAR']]
  #  df_res_cap_ud_final['REGION'] = region_name
  #  df_res_cap_ud_final = df_res_cap_ud_final[['REGION',
  #                                             'TECHNOLOGY',
  #                                             'YEAR',
  #                                             'VALUE']]

   # df_res_cap = pd.concat([df_res_cap, df_res_cap_ud_final 
  #                          if not df_res_cap_ud_final.empty else None])

    # Group residual capacities in case user defined technology entries already exist.
  #  df_res_cap = df_res_cap.groupby(['REGION', 'TECHNOLOGY', 'YEAR']
  #                                  , as_index = False).sum()

    # For technologies with start year at or after model start year, add to 
    # TotalAnnualMinCapacityInvestment      
 #   df_min_cap_inv = df_min_cap_inv[['REGION', 'TECHNOLOGY', 'YEAR', 'VALUE']].loc[
  #      df_min_cap_inv['YEAR'] >= min(get_years(start_year, end_year))]
    
  #  df_min_cap_inv.drop_duplicates(subset=['REGION', 
  #                                         'TECHNOLOGY',
  #                                         'YEAR'],
  #                                 keep='last',
  #                                 inplace=True)

    # Update CapitalCost with user-defined efficiencies by storage technology
    df_oar = df_oar_base.copy()

    for idx, tech_params in tech_capacity_sto.items():
        df_oar.loc[df_oar['TECHNOLOGY'] == tech_params[0],
                   'VALUE'] = round(1 / (efficiency_dict[idx] / 100), 3)
    
    # Update CapitalCost with user-defined capex costs by storage technology
    cap_cost_sto = cap_cost_base.copy()

    for idx, tech_params in tech_capacity_sto.items():
        print(tech_params[0])
        cap_cost_sto.loc[cap_cost_sto['STORAGE'] == 
                         tech_params[0].replace('PWR', ''),
                         'VALUE'] = capex_dict[idx]

    return(#df_max_cap_inv, 
           #df_min_cap_inv, 
          # df_res_cap, 
           df_oar, 
          # op_life, 
           cap_cost_sto
           )