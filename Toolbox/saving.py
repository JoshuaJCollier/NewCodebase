# Saving and loading data, generalised format
import os
import sys
import inspect
import pandas as pd
import numpy as np
import yaml
import glob
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

def generateMetadata(source, source_size, dist, baseline, pol = None, parts = [], params = {}):
    """_summary_

    Args:
        source (str): Source type, i.e. 'LED'
        source_size (str): Source size, i.e. '1000um'
        dist (str): Distance, i.e. '60mm'
        baseline (str): Baseline, i.e. '127um'
        pol (int, optional): Polarization. Defaults to None.
        parts (list, optional): List of parts in experiment, in order of source to collector. Defaults to [].
        parameters (dict, optional): Dictionary of experiment parameters. Defaults to {}.

    Returns:
        dict: Metadata to save in a yaml
    """
    # Establish metadata for a file
    metadata = {}
    metadata['caller'] = inspect.stack()[1].function # get caller function name
    metadata['datetime'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    metadata['parameters'] = params # {'snspd integration':'10ms', }
    metadata['source'] = source #'LED'
    metadata['source size (m)'] = source_size #'1000um'
    metadata['distance (m)'] = dist #'60mm'
    metadata['baseline (m)'] = baseline #'127um'
    metadata['polarization (deg)'] = pol #'0'
    metadata['parts'] = parts # parts = ['LED', 'Collimating lens', 'Polarizer', 'SM VGA', 'Pol controllers', 'optical delay lines', '50:50 BS', 'SNSPDs']
    return metadata

def save(campaign, data, metadata):
    """ This function will save data, including metadata

    Args:
        campaign (str): Name of campaign, will be used for name of saved file
        data (pandas dataframe): Dataframe of data
        metadata (dict): Dictionary of experimental info and context (todays data, etc)
    """
    
    path = 'C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\3. Data\\{}'.format(campaign.title())
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
        
    os.chdir('C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\3. Data\\{}'.format(campaign.title()))
    existing = []
    files_existing = []
    for file in glob.glob("*.parquet"):
        files_existing.append(file)
        existing.append(int(file.split('.')[0].split('_')[1])) #splitting on . gives you the name, splitting on _ gives you the number
        
    existing_max = 0
    if len(existing) > 0:
        existing_max = max(existing)

    filename = '{}_{:05d}'.format(campaign.lower(), existing_max+1)
    if filename in files_existing:
        filename = '{}_{:05d}_error_duplicated_name'.format(campaign.lower(), existing_max+1)
        
    table = pa.Table.from_pandas(data)
    pq.write_table(table, '{}.parquet'.format(filename))
        
    with open('{}.yaml'.format(filename), 'w') as file:
        yaml.dump(metadata, file)
        
    print('Saved {} parquet and yaml'.format(filename))
    return filename
    
def load(campaign, index):
    os.chdir('C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\3. Data\\{}'.format(campaign.title()))

    filename = '{}_{:05d}'.format(campaign.lower(), index)
    
    data = pd.read_parquet('{}.parquet'.format(filename), engine='pyarrow')
    metadata = ''
    with open('{}.yaml'.format(filename), 'r') as file:
        try:
            metadata = yaml.safe_load(file)
            print(metadata)
        except yaml.YAMLError as exc:
            print(exc)
    
    return data, metadata

#print(int('file_0001.parquet'.split('.')[0].split('_')[1]))