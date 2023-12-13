import json

from nibelungenbruecke.scripts.data_generation.generate_data import generate_data

def task_generate_synthetic_data():
    data_parameters_path = "./input/settings/new_generate_data_parameters.json"
    with open(data_parameters_path, 'r') as f:
        data_parameters = json.load(f)

    return {'actions': [(generate_data,[],{'parameters':data_parameters})],
            'file_dep': [data_parameters["model_path"], data_parameters_path],
            'targets': [data_parameters["output_parameters"]["output_path"]+data_parameters["output_parameters"]["output_format"]],
            'uptodate': [True]}

if __name__ == "__main__":

    data_parameters_path = "./input/settings/new_generate_data_parameters.json"
    with open(data_parameters_path, 'r') as f:
        data_parameters = json.load(f)
        
    generate_data(data_parameters)