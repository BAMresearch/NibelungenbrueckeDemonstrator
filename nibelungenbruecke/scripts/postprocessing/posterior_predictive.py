import matplotlib.pyplot as plt
import arviz as az
import numpy as np

from nibelungenbruecke.scripts.inference.import_forward_model import import_forward_model
from nibelungenbruecke.scripts.utilities.offloaders import offload_posterior_predictive
from nibelungenbruecke.scripts.utilities.probeye_utilities import load_probeye_sensors

# local imports (inference data post-processing)

def posterior_predictive(parameters:dict):
    "Generates synthetic data according to a process especified in the parameters"
    
    # Initialize defaults
    input_parameters = _get_default_parameters()
    for key, value in parameters.items():
        input_parameters[key] = value
    
    parameters = input_parameters

    # Define forward model
    forward_model = import_forward_model(parameters["model_path"], parameters["forward_model_parameters"])

    # Generate the Geometry and model of the forward model 
    forward_model.LoadGeometry(parameters["model_path"])
    forward_model.GenerateModel()

    # Load inference data
    inference_data = az.from_netcdf(parameters["inference_data_path"])

    # Generate posterior-predictive samples of the posterior distributions
    ppc_samples = {}
    samples = az.extract(inference_data, num_samples=100)
    for parameter in parameters["forward_model_parameters"]["problem_parameters"]:
        ppc_samples[parameter] = samples[parameter].data
    
    # Evaluate the responses
    responses = []

    for i in range(parameters["number_of_data_samples"]):
        i_sample = {}
        for key, values in ppc_samples.items():
            i_sample[key]=values[i]
        responses.append(forward_model.response(i_sample))
    
    offload_posterior_predictive(responses, load_probeye_sensors(parameters["forward_model_parameters"]["output_sensors_path"]), 
                                output_path = parameters["output_parameters"]["output_path"], 
                                output_format = parameters["output_parameters"]["output_format"])

    # Plot histograms
    if parameters["plot_histogram"]:
        for parameter in responses[0].keys():
            grouped_data = np.array([data_i[parameter] for data_i in responses])
            fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(12, 4))
            for i in range(3):
                ax[i].hist(grouped_data[:, i], bins=20, alpha=0.5, color='blue', edgecolor='black')
                mean = grouped_data[:, i].mean()
                std = grouped_data[:, i].std()
                ax[i].axvline(mean, color='red', label='Mean')
                ax[i].axvline(mean + 3 * std, color='green', label=r'$+3\sigma$')
                ax[i].axvline(mean - 3 * std, color='green', label=r'$-3\sigma$')
                ax[i].legend()
            fig.suptitle(f'Histograms for {parameter}', fontsize=16)
            fig.savefig(parameters["output_histogram_path"]+parameter+parameters["output_histogram_format"])
    
    
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