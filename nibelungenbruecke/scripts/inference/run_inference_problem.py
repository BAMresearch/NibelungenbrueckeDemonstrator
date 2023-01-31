# import os
# import sys
import matplotlib.pyplot as plt
import arviz as az
# # Get the parent directory of the current script
# root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # Add the parent directory to sys.path
# sys.path.append(root_path)

from nibelungenbruecke.scripts.utilities.checks import check_lists_same_length
from nibelungenbruecke.scripts.utilities.probeye_utilities import add_parameter_wrapper, add_experiment_wrapper
from nibelungenbruecke.scripts.inference.import_forward_model import import_forward_model
from nibelungenbruecke.scripts.inference.import_likelihood_model import import_likelihood_model
from nibelungenbruecke.scripts.inference.import_solver import import_solver

from probeye.definition.inverse_problem import InverseProblem

# local imports (inference data post-processing)
from probeye.postprocessing.sampling_plots import create_pair_plot
from probeye.postprocessing.sampling_plots import create_posterior_plot
from probeye.postprocessing.sampling_plots import create_trace_plot

def run_inference_problem(parameters:dict):
    "Generates synthetic data according to a process especified in the parameters"
    
    # Initialize defaults
    input_parameters = _get_default_parameters()
    for key, value in parameters.items():
        input_parameters[key] = value
    
    parameters = input_parameters

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

    # Save data
    if parameters["output_parameters"]["output_format"]==".nc":
        # TODO: Better error/error handling
        # FIXME: Fix probeye so that the solver includes the option of passing the tex variable or the name
        print("[Saving inference data] WARNING: Parameters with a tex field with math expressions give an error unless the solver saves them with the name field instead.")
        az.to_netcdf(inference_data, parameters["output_parameters"]["output_path"]+parameters["output_parameters"]["output_format"])
    else:
        raise Exception(f"[Run inference]: Output format {parameters['output_parameters']['output_format']} not implemented. Implemented formats are: .nc")
    
    # TODO: The plots should go in a different task
    true_values = parameters["postprocessing"]["true_values"]
    if parameters["postprocessing"]["pair_plot"]:
        pair_plot_array = create_pair_plot(
            inference_data,
            solver.problem,
            true_values=true_values,
            focus_on_posterior=True,
            show_legends=True,
            show = False,
            title="Sampling results from Solver (pair plot)",
        )
        fig = plt.gcf()
        fig.savefig(parameters["postprocessing"]["output_pair_plot"]+parameters["postprocessing"]["pair_plot_format"])

    if parameters["postprocessing"]["posterior_plot"]:
        post_plot_array = create_posterior_plot(
            inference_data,
            solver.problem,
            show = False,
            true_values=true_values,
            title="Sampling results from Solver (posterior plot)",
        )
        fig = plt.gcf()
        fig.savefig(parameters["postprocessing"]["output_posterior_plot"]+parameters["postprocessing"]["posterior_plot_format"])

    if parameters["postprocessing"]["trace_plot"]:
        trace_plot_array = create_trace_plot(
            inference_data,
            solver.problem, 
            show = False,
            title="Sampling results from Solver (trace plot)",
        )
        fig = plt.gcf()
        fig.savefig(parameters["postprocessing"]["output_trace_plot"]+parameters["postprocessing"]["trace_plot_format"])

def _get_default_parameters():

    default_parameters = {
        "model_path": "input/models/mesh.msh",
        "output_parameters":{
            "output_path": "./output//inference_results",
            "output_format": ".nc"
        },
        "print_info": True, 
        "inverse_problem_parameters":{
            "name": "Nibelungenbrücke displacements",
            "print_header": True
        },
        "forward_model_parameters": {
            "name": "Nibelungenbrücke displacements",
            "experiments": ["TestSeries_1"],
            "forward_model_path": "probeye_forward_model_bridge",
            "input_sensors_path": "input/sensors/sensors_displacements_probeye_input.json",
            "output_sensors_path": "input/sensors/sensors_displacements_probeye_output.json",
            "problem_parameters": ["rho", "mu", "lambda"], 
            "parameter_key_paths": [["material_parameters"],["material_parameters"],["material_parameters"]],
            "model_parameters": {
                "model_name": "displacements",
                "material_parameters":{
                    "rho": 10.0,
                    "g": 100,
                    "mu": 1,
                    "lambda": 1.25
                },
                "tension_z": 0.0,
                "boundary_conditions": {
                    "bc1":{
                    "model":"clamped_boundary",
                    "side_coord": 0.0,
                    "coord": 2
                },
                    "bc2":{
                    "model":"clamped_boundary",
                    "side_coord": 95.185,
                    "coord": 2
                }}
            }
        },
        "parameter_list_parameters":[
            {
                "name":"rho",
                "tex":"$\\rho$",
                "info":"Normalized mass",
                "prior":{
                    "name": "LogNormal",
                    "mean": 2,
                    "std": 0.5
                }
            },
            {
                "name":"mu",
                "tex":"$\\mu$",
                "info":"Lamé constant \\mu",
                "domain":"(0, 50)",
                "prior":{
                    "name": "LogNormal",
                    "mean": 0.0,
                    "std": 0.1
                }
            },
            {
                "name":"lambda",
                "tex":"$\\lambda$",
                "info":"Lamé constant \\lambda",
                "domain":"(0.0, 50)",
                "prior":{
                    "name": "LogNormal",
                    "mean": 0.0,
                    "std": 0.4
                }
            },
            {
                "name":"sigma",
                "domain": "(0, +oo)",
                "tex":"$\\sigma$",
                "info":"Standard deviation, of zero-mean Gaussian noise model",
                "prior":{
                    "name":"Uniform",
                    "low": 0.0,
                    "high": 0.8
                }
            }
        ],
        "experiment_list_parameters": [
            {
                "name": "TestSeries_1",
                "input_data_path": "input/data/displacements.h5",
                "data_format": ".h5",
                "sensor_names": ["DisplacementSensor0","DisplacementSensor1","DisplacementSensor2"],
                "data_values": ["Data","Data","Data"],
                "parameter_names": ["disp_pilot_1", "disp_span", "disp_pilot_2"]
            }
        ],
        "likelihood_model_parameters":{
            "name": "GaussianLikelihoodModel",
            "parameters":{
                "experiment_name":"TestSeries_1",
                "model_error": "additive"
            }
        },
        "solver_parameters":{
            "module": "emcee",
            "name": "EmceeSolver",
            "show_progress": True
        },
        "run_parameters":{
            "n_steps": 60,
            "n_initial_steps": 20,
            "n_walkers": 10
        },
        "postprocessing":{
            "pair_plot": True,
            "output_pair_plot": "output/figures/pair_plot",
            "pair_plot_format": ".pdf",
            "posterior_plot": True,
            "output_posterior_plot": "output/figures/posterior_plot",
            "posterior_plot_format": ".pdf",
            "trace_plot": True,
            "output_trace_plot": "output/figures/trace_plot",
            "trace_plot_format": ".pdf",
            "true_values":{
                "rho": 10,
                "mu": 1,
                "lambda": 1.25,
                "sigma": 0.5
            }    
        }
    }

    return default_parameters