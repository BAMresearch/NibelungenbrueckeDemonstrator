import os
import sys

# Get the parent directory of the current script
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add the parent directory to sys.path
sys.path.append(root_path)

from utilities.checks import check_path_exists
from data_generation.generator_model_factory import generator_model_factory
def generate_data(parameters):
    "Generates synthetic data according to a process especified in the parameters"
    
    # Import parameters
    data_parameters = _get_default_parameters()
    for key, value in parameters.items():
        data_parameters[key] = value

    # Sanity checks
    check_path_exists(data_parameters["model_path"])
    if data_parameters["generation_models_list"][0] is None:
        raise Exception("[Synthetic_data] Error: Generation model not defined.")

    # Generate several sets of data iteratively
    for model_parameters in data_parameters["generation_models_list"]:
        generator_model = generator_model_factory(data_parameters["model_path"],
                                                  model_parameters["generator_path"], 
                                                  model_parameters["sensors_path"],
                                                  model_parameters["model_parameters"],
                                                  data_parameters["output_parameters"])
        generator_model.Generate()

def _get_default_parameters():

    default_parameters = {
        "model_path": "input/models/mesh.msh",
        "output_path": "data",
        "output_format": ".h5",
        "generation_models_list": [None],
    }

    return default_parameters
