import os
import sys

# Get the parent directory of the current script
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add the parent directory to sys.path
sys.path.append(root_path)

from utilities.checks import check_lists_same_length
from utilities.probeye_utilities import add_parameter_wrapper, add_experiment_wrapper
from inference.import_forward_model import import_forward_model
from inference.import_likelihood_model import import_likelihood_model
from inference.import_solver import import_solver

from probeye.definition.inverse_problem import InverseProblem


def run_inference_problem(parameters):
    "Generates synthetic data according to a process especified in the parameters"
    
    # Sanity checks
    check_lists_same_length(parameters["forward_model_parameters"]["experiments"],
                            parameters["experiment_list_parameters"],
                            "[Inverse problem definition] Experiments in list of experiments \
                            and in forward model do not coincide.")

    # Define problem
    inverse_problem = InverseProblem(**parameters["inverse_problem_parameters"])

    # Define forward model
    forward_model = import_forward_model(parameters["model_path"], parameters["forward_model_parameters"])

    # Add parameters to problem

    for parameter in parameters["parameter_list_parameters"]:
        add_parameter_wrapper(inverse_problem, parameter)

    # Add experiments to problem
    for experiment in parameters["experiment_list_parameters"]:
        add_experiment_wrapper(inverse_problem,experiment)

    # Add forward model
    inverse_problem.add_forward_model(forward_model, experiments = parameters["forward_model_parameters"]["experiments"])
    
        
    # Add likelihood model
    inverse_problem.add_likelihood_model(import_likelihood_model(parameters["likelihood_model_parameters"]))

    # Print info
    if parameters["print_info"]:
        inverse_problem.info(print_header = True)

    # Add solver
    solver = import_solver(inverse_problem, parameters["solver_parameters"])

    # Generate the Geometry and model of the forward model in the inverse problem
    for i_likelihood_model in solver.problem.likelihood_models.values():
        i_likelihood_model.forward_model.LoadGeometry(parameters["model_path"])
        i_likelihood_model.forward_model.GenerateModel()

    # Run solver
    inference_data = solver.run(**parameters["run_parameters"])


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