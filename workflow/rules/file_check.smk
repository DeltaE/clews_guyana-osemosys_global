import os
import shutil
import pandas as pd

'''
UPDATES TO BE DONE
------------------
There is an issue where snakemake won't update get the list of files to create
at an intermediate point in the workflow. After all the preprocessing scripts
are created, we want to generate the list of missing files to be fed into the 
rule as outputs. I can't get this to work though, it keeps grabbing all files. 
I also don't want to use wildcards in this case because there is nothing to 
identify what rules create what csv's (like a prefix) to remove ambiguity 
from the rules. Therfore, we have to add in a rule order, 

For the time being I have hardcoded in what files should be generated by the 
file_check rule, but this should be updated in the future. 
'''

# REQUIRED 

configfile: 'config/config.yaml'

# GET LIST OF MISSING FILES 

missing_files = os.listdir('resources/simplicity/data')

# This is not working... see note at top of  file
'''
for csv in os.listdir(Path(output_dir, 'data')):
    if csv == 'default_values.csv':
        continue
    missing_files.remove(csv)
'''

missing_files.remove('default_values.csv')
[missing_files.remove(csv) for csv in demand_files]
[missing_files.remove(csv) for csv in power_plant_files]
[missing_files.remove(csv) for csv in timeslice_files]
[missing_files.remove(csv) for csv in variable_cost_files]
[missing_files.remove(csv) for csv in emission_files]
[missing_files.remove(csv) for csv in max_capacity_files]

# RULE

rule file_check:
    message:
        'Generating missing files...'
    input:
        expand('workflow/rules/flags/{flag_file}.done', flag_file = flag_files),
        expand('resources/simplicity/data/{missing_file}', missing_file = missing_files),
        'resources/data/default_values.csv'
    output: 
        expand('results/data/{missing_file}', missing_file = missing_files),
        'results/data/default_values.csv'
    conda:
        '../envs/data_processing.yaml'
    log: 
        log = 'results/logs/file_check.log'
    shell:
        'python workflow/scripts/osemosys_global/OPG_file_check.py 2> {log}'

'''
def get_missing_files():
    missing = os.listdir(Path(input_dir, 'simplicity/data'))
    for csv in os.listdir(Path(output_dir, 'data')):
        missing.remove(csv)
    #csv_paths = []
    #for csv in missing: 
    #    csv_paths.append(Path(input_dir, 'simplicity/data', csv))
    return missing

rule FileCheck:
    input:
        expand('resources/simplicity/data/{missing_file}', missing_file = get_missing_files),
        #expand('workflow/rules/flags/{flag_file}.done', flag_file = flag_files),
        #expand(Path(input_dir, 'simplicity/data/{osemosys_file}'), osemosys_file = osemosys_files),
        #Path(input_dir, 'data/default_values.csv'),
    output: 
        expand('results/data/{missing_file}', missing_file = get_missing_files),
        #expand(Path(output_dir,'data/{osemosys_file}'), osemosys_file = osemosys_files),
        #expand('results/data/{missing_file}.csv', missing_file = get_missing_files),
        #Path(output_dir, 'data/default_values.csv')
    log: 
        'workflow/logs/fileCheck.log'
    run: 
        #for each_csv in os.listdir(Path(input_dir, 'simplicity/data')):
        for each_csv in os.listdir(Path(input_dir, 'simplicity/data')): 
            if each_csv == "default_values.csv":
                    shutil.copy(Path(input_dir, 'data', each_csv),
                                Path(output_dir, 'data', each_csv))
            if each_csv not in os.listdir(Path(output_dir, 'data')): 
                csv_df_in = pd.read_csv(Path(input_dir, 'simplicity/data', each_csv))
                csv_df_out = pd.DataFrame(columns = list(csv_df_in.columns))
                csv_df_out.to_csv(Path(output_dir,'data', each_csv), index = None)
'''