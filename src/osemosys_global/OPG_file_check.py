#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import os
import shutil
import yaml
import logging 
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

#Read in information from YAML file
yaml_file = open("config.yaml")
parsed_yaml_file = yaml.load(yaml_file, Loader=yaml.FullLoader)

input_dir = parsed_yaml_file.get('inputDir')
output_dir = parsed_yaml_file.get('outputDir') + 'data/'

def create_csv_files(path):
    csv_file_dict = {} 
    for each_csv in os.listdir(r'../../simplicity/data/'):  
        #copy default values csv with data
        if each_csv == "default_values.csv":
                shutil.copy(r'../../data/default_values.csv',path)
        if each_csv not in os.listdir(path):
            csv_df_in = pd.read_csv(os.path.join(r'../../simplicity/data/',
                                                  each_csv))
            csv_df_out = pd.DataFrame(columns = list(csv_df_in.columns))
            csv_df_out.to_csv(os.path.join(path, 
                                               each_csv),
                                 index = None)
            csv_file_dict[each_csv] = list(csv_df_in.columns)
    
    return csv_file_dict


# In[ ]:


create_csv_files(output_dir)
logging.info('File Check Completed')

# In[ ]:




