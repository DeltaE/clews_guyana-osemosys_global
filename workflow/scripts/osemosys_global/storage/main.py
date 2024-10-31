import pandas as pd
import os

#os.chdir(r'C:\Users\maart\Github\osemosys_global\workflow\scripts\osemosys_global\storage')

from read import(
    import_storage_build_rates,
    import_op_life,
    import_iar_base,
    import_oar_base,
    import_capact_base,
    import_fix_cost_base,
    import_var_cost_base,
    import_max_cap_invest_base,
    import_min_cap_invest_base,
  #  import_res_cap_base,
    import_set_base
)

#from constants import(

 #   )

#from data import(
 #   format_gtd_existing,
 #   format_gtd_planned,
 #   correct_gtd_data
 #   )

from activity import(
    activity_storage,
    create_storage_capacity_activity
    )

from costs import(
    set_storage_capex_costs,
    set_storage_operating_costs
    )
    
from operational_life import set_op_life_storage

from investment_constraints import cap_investment_constraints_sto

from user_defined_capacity import set_user_defined_capacity_sto

#from residual_capacity import res_capacity_transmission

from sets import(set_unique_storage_technologies, 
                 set_unique_storage_technologies_custom_nodes, 
                 set_unique_technologies)

from technology_to_from_storage import (set_technology_to_storage,
                                        set_technology_from_storage
                                        )

#os.chdir(r'C:\Users\maart\Github\osemosys_global')

def main(
    build_rates: pd.DataFrame,
    unique_sto_techs: list,
    default_op_life: dict[str, int],
    iar_base: pd.DataFrame,
    oar_base: pd.DataFrame,
    capact_base: pd.DataFrame,
    fix_cost_base: pd.DataFrame,
    var_cost_base: pd.DataFrame,    
    max_cap_invest_base: pd.DataFrame,
    min_cap_invest_base: pd.DataFrame,
 #   res_cap_base: pd.DataFrame,
    tech_set_base: pd.DataFrame,
    fuel_set_base: pd.DataFrame
):
    
    # CALL FUNCTIONS
    
    # Set storage set
    storage_set = set_unique_storage_technologies(fuel_set_base, unique_sto_techs)
    
    # Set storage sets in case custom nodes are defined
    if custom_nodes:
        storage_set_custom_nodes = set_unique_storage_technologies_custom_nodes(custom_nodes, 
                                                                                unique_sto_techs)
        storage_set = pd.concat([storage_set, storage_set_custom_nodes])
        
    # Create TechnologyToStorage and TechnologyFromStorage
    tech_to_storage = set_technology_to_storage(storage_set, region_name)
    tech_from_storage = set_technology_from_storage(storage_set, region_name)    

    
    # Set capital costs for storage.
    cap_cost_storage = set_storage_capex_costs(storage_set, 
                                               storage_parameters,
                                               start_year,
                                               end_year,
                                               region_name)
    
    # Set fixed and variable operating costs for storage.
    fix_cost_storage, var_cost_storage = set_storage_operating_costs(storage_set,
                                                                     storage_parameters,
                                                                     fix_cost_base,
                                                                     var_cost_base,
                                                                     start_year,
                                                                     end_year,
                                                                     region_name)
    
    # Set activity ratios for storage.
    iar_storage, oar_storage = activity_storage(storage_set, iar_base, oar_base, 
                                                storage_parameters, start_year, 
                                                end_year, region_name)
    
    # assign capacity to activity unit to storage.
    cap_activity_storage = create_storage_capacity_activity(storage_set, capact_base)
    
    # Set operational life for storage.
    op_life_storage = set_op_life_storage(storage_set, default_op_life, region_name)
    
    # Set annual capacity investment constraints.
    max_cap_invest_storage = cap_investment_constraints_sto(storage_set, 
                                                            max_cap_invest_base,
                                                            build_rates,
                                                            no_investment_techs, 
                                                            start_year, 
                                                            end_year, 
                                                            region_name)
    
    # Set residual capacity.
    #res_cap_trn = res_capacity_transmission(gtd_exist_corrected, gtd_planned_corrected, 
     #                                       res_cap_base, op_life_dict, 
      #                                      start_year, end_year, region_name,
       #                                     RETIREMENT_YEAR_TRANSMISSION, 
        #                                    PLANNED_BUILD_YEAR_TRANSMISSION)

    # Alter output csv's based on user defined capacities following user config.
    if tech_capacity_sto is not None:
        (max_cap_invest_storage, 
         min_cap_invest_storage, 
    #     res_cap_trn, 
     #    iar_trn,
          oar_storage,
     #    op_life_trn, 
          cap_cost_storage,
          fix_cost_storage, 
          var_cost_storage
         ) = set_user_defined_capacity_sto(
            tech_capacity_sto, 
     #       default_op_life, 
            min_cap_invest_base, 
            max_cap_invest_storage, 
     #       res_cap_trn,
     #       iar_trn,
            oar_storage,
      #      op_life_trn,
            cap_cost_storage,
            fix_cost_storage, 
            var_cost_storage,
            start_year,
            end_year,
            region_name
            )  

    # get new additions to technology sets
    new_techs = set_unique_technologies(storage_set)
    tech_set = pd.concat([tech_set_base, new_techs])
        
    # OUTPUT CSV's
    
    oar_storage.to_csv(os.path.join(output_data_dir, "OutputActivityRatio.csv"), index=None)
    
    iar_storage.to_csv(os.path.join(output_data_dir, "InputActivityRatio.csv"), index=None)
    
    cap_activity_storage.to_csv(os.path.join(output_data_dir, "CapacityToActivityUnit.csv"), index = None)
    
    cap_cost_storage.to_csv(os.path.join(output_data_dir, "CapitalCostStorage.csv"), index = None)
    
    fix_cost_storage.to_csv(os.path.join(output_data_dir, "FixedCost.csv"), index = None)
    var_cost_storage.to_csv(os.path.join(output_data_dir, "VariableCost.csv"), index = None)
    
    op_life_storage.to_csv(os.path.join(output_data_dir, "OperationalLifeStorage.csv"), index = None)
    
    max_cap_invest_storage.to_csv(os.path.join(output_data_dir, 
                                            'TotalAnnualMaxCapacityInvestment.csv'),
                                        index = None)

    tech_set.to_csv(os.path.join(output_data_dir, "TECHNOLOGY.csv"), index = None)
    storage_set.to_csv(os.path.join(output_data_dir, "STORAGE.csv"), index = None)
    
    tech_to_storage.to_csv(os.path.join(output_data_dir, "TechnologyToStorage.csv"), index=None)
    tech_from_storage.to_csv(os.path.join(output_data_dir, "TechnologyFromStorage.csv"), index=None)
        
   # res_cap_trn.to_csv(os.path.join(output_data_dir, 
  #                                          'ResidualCapacity.csv'),
   #                                     index = None)       
    
    if tech_capacity_sto is not None:
        min_cap_invest_storage.to_csv(os.path.join(output_data_dir, 
                                                'TotalAnnualMinCapacityInvestment.csv'),
                                            index = None)
        
    else:
        min_cap_invest_base.to_csv(os.path.join(output_data_dir, 
                                                'TotalAnnualMinCapacityInvestment.csv'),
                                            index = None)

if __name__ == "__main__":
    
    if "snakemake" in globals():
        file_storage_build_rates = snakemake.input.storage_build_rates 
        file_default_op_life = snakemake.input.default_op_life
        start_year = snakemake.params.start_year
        end_year = snakemake.params.end_year
        region_name = snakemake.params.region_name
        custom_nodes = snakemake.params.custom_nodes
        tech_capacity_sto = snakemake.params.user_defined_capacity_storage
        no_investment_techs = snakemake.params.no_investment_techs      
        storage_parameters = snakemake.params.storage_parameters           
        output_data_dir = snakemake.params.output_data_dir
        input_data_dir = snakemake.params.input_data_dir
        transmission_data_dir = snakemake.params.transmission_data_dir            
        file_iar_base = f'{transmission_data_dir}/InputActivityRatio.csv'
        file_oar_base = f'{transmission_data_dir}/OutputActivityRatio.csv'
        file_capact_base = f'{transmission_data_dir}/CapacityToActivityUnit.csv'  
        file_fix_cost_base = f'{transmission_data_dir}/FixedCost.csv'
        file_var_cost_base = f'{transmission_data_dir}/VariableCost.csv'        
        file_max_cap_invest_base = f'{transmission_data_dir}/TotalAnnualMaxCapacityInvestment.csv'
        file_min_cap_invest_base = f'{transmission_data_dir}/TotalAnnualMinCapacityInvestment.csv'
      #  file_res_cap_base = f'{transmission_data_dir}/ResidualCapacity.csv'
        file_tech_set = f'{transmission_data_dir}/TECHNOLOGY.csv'        
        file_fuel_set = f'{output_data_dir}/FUEL.csv'
        
    # The below else statement defines variables if the 'transmission/main' script is to be run locally
    # outside the snakemake workflow. This is relevant for testing purposes only! User inputs when running 
    # the full workflow need to be defined in the config file. 

    else:    
        file_storage_build_rates = 'resources/data/storage_build_rates.csv'
        file_default_op_life = 'resources/data/operational_life.csv'
        start_year = 2021
        end_year = 2050
        region_name = 'GLOBAL'
        custom_nodes = []
        tech_capacity_sto = {'sto1': ['PWRSDSINDEA01', 0, 2020, 2025, 3, 450, 40, 0, 87],
                             'sto2': ['PWRLDSINDNE01', 4, 1980, 2025, 2, 350, 19, 0.5, 82],
                             'sto3': ['PWRLDSINDNE01', 1, 2030, 2025, 2, 350, 19, 0.5, 82]}
        no_investment_techs = ["CSP", "WAV", "URN", "OTH", "WAS", 
                               "COG", "GEO", "BIO", "PET", "LDS"]
        storage_parameters = {'SDS': [484.5, 44.25, 0, 85],
                              'LDS': [379.4, 20.2, 0.58, 80]}

        output_data_dir = 'results/data'
        input_data_dir = 'resources/data'
        transmission_data_dir = 'results/data/transmission'        
        file_iar_base = f'{transmission_data_dir}/InputActivityRatio.csv'
        file_oar_base = f'{transmission_data_dir}/OutputActivityRatio.csv'
        file_capact_base = f'{transmission_data_dir}/CapacityToActivityUnit.csv'
        file_fix_cost_base = f'{transmission_data_dir}/FixedCost.csv'
        file_var_cost_base = f'{transmission_data_dir}/VariableCost.csv'
        file_max_cap_invest_base = f'{transmission_data_dir}/TotalAnnualMaxCapacityInvestment.csv'
        file_min_cap_invest_base = f'{transmission_data_dir}/TotalAnnualMinCapacityInvestment.csv'
     #   file_res_cap_base = f'{transmission_data_dir}/ResidualCapacity.csv'
        file_tech_set = f'{transmission_data_dir}/TECHNOLOGY.csv'
        file_fuel_set = f'{output_data_dir}/FUEL.csv'

    # SET INPUT DATA
    
    sto_techs = list(storage_parameters.keys())
    
    build_rates = import_storage_build_rates(file_storage_build_rates)
    
    op_life = import_op_life(file_default_op_life)
    op_life_dict = dict(zip(list(op_life['tech']),
                            list(op_life['years'])))

    iar_base = import_iar_base(file_iar_base)
    oar_base = import_oar_base(file_oar_base)
    capact_base = import_capact_base(file_capact_base)
    fix_cost_base = import_fix_cost_base(file_fix_cost_base)
    var_cost_base = import_var_cost_base(file_var_cost_base)    
    max_cap_invest_base = import_max_cap_invest_base(file_max_cap_invest_base)
    min_cap_invest_base = import_min_cap_invest_base(file_min_cap_invest_base)
#    res_cap_base = import_res_cap_base(file_res_cap_base)  
    tech_set_base = import_set_base(file_tech_set)  
    fuel_set_base = import_set_base(file_fuel_set)  
    
    input_data = {
        "unique_sto_techs" : sto_techs,
        "default_op_life": op_life_dict,
        "build_rates" : build_rates,
        "iar_base" : iar_base,
        "oar_base" : oar_base,
        "capact_base" : capact_base,
        "fix_cost_base" : fix_cost_base,
        "var_cost_base" : var_cost_base,
        "max_cap_invest_base" : max_cap_invest_base,
        "min_cap_invest_base" : min_cap_invest_base,
    #    "res_cap_base" : res_cap_base, 
        "tech_set_base" : tech_set_base,
        "fuel_set_base" : fuel_set_base,  
    }
    
    # CALL MAIN
    main(**input_data)