import json
import os
import sys

# Get the parent directory of the current script
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add the parent directory to sys.path
sys.path.append(root_path)

from scripts.postprocessing.posterior_predictive import posterior_predictive
# from scripts.inference.plot_inference_results import plot_inference_results

def task_posterior_predictive():
    postprocess_parameters_path = "input/settings/postprocess_parameters.json"
    with open(postprocess_parameters_path, 'r') as f:
        postprocess_parameters = json.load(f)
        # TODO: Add targets for the histogram plots

    return {'actions': [(posterior_predictive,[],{'parameters':postprocess_parameters["posterior_predictive"]})],
            'file_dep': [postprocess_parameters["model_path"],postprocess_parameters["inference_data_path"]],
            'targets': [postprocess_parameters["output_parameters"]["output_path"]+postprocess_parameters["output_parameters"]["output_format"]],
            'uptodate': [True]}

if __name__ == "__main__":

    postprocess_parameters_path = "input/settings/postprocess_parameters.json"
    with open(postprocess_parameters_path, 'r') as f:
        postprocess_parameters = json.load(f)
        
    posterior_predictive(postprocess_parameters["posterior_predictive"])