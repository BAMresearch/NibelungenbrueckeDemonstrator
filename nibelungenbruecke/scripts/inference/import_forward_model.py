# import os
# import sys

# # Get the parent directory of the current script
# root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # Add the parent directory to sys.path
# sys.path.append(root_path)

from nibelungenbruecke.scripts.utilities.checks import check_path_exists
from nibelungenbruecke.scripts.inference.forward_model_factory import forward_model_factory

def import_forward_model(model_path, parameters):
    "Imports forward model from a set of parameters"
    
    # Import parameters
    forward_model_parameters = _get_default_parameters()
    for key, value in parameters.items():
        forward_model_parameters[key] = value

    # Sanity checks
    check_path_exists(model_path)
    if forward_model_parameters["forward_model_path"] is None:
        raise Exception("[Import Forward Model] Error: Generation model not defined.")

    # Generate forward model
    forward_model = forward_model_factory(forward_model_parameters["forward_model_path"], forward_model_parameters, model_path)

    return forward_model

def _get_default_parameters():

    default_parameters = {
        "forward_model_path": "probeye_forward_model_bridge",
        "input_sensors_path": "input/sensors/sensors_displacements_probeye_input.json",
        "output_sensors_path": "input/sensors/sensors_displacements_probeye_output.json",
        "problem_parameters": ["rho", "mu", "lambda"], 
        "parameters_key_paths": [[],[],[]],
        "model_parameters": {}
    }

    return default_parameters