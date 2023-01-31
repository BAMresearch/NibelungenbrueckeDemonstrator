import json
# import os
# import sys

# # Get the parent directory of the current script
# root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # Add the parent directory to sys.path
# sys.path.append(root_path)

from nibelungenbruecke.scripts.data_generation.generate_data import generate_data

def task_generate_synthetic_data():
    data_parameters_path = "input/settings/generate_data_parameters.json"
    with open(data_parameters_path, 'r') as f:
        data_parameters = json.load(f)

    return {'actions': [(generate_data,[],{'parameters':data_parameters})],
            'file_dep': [data_parameters["model_path"]],
            'targets': [data_parameters["output_parameters"]["output_path"]+data_parameters["output_parameters"]["output_format"]],
            'uptodate': [True]}

if __name__ == "__main__":

    data_parameters_path = "input/settings/generate_data_parameters.json"
    with open(data_parameters_path, 'r') as f:
        data_parameters = json.load(f)
        
    generate_data(data_parameters)