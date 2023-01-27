import json
import os
import sys

# Get the parent directory of the current script
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add the parent directory to sys.path
sys.path.append(root_path)

from scripts.inference.run_inference_problem import run_inference_problem
# from scripts.inference.plot_inference_results import plot_inference_results

def task_run_inference_problem():
    inference_parameters_path = "input/settings/inference_parameters.json"
    with open(inference_parameters_path, 'r') as f:
        inference_parameters = json.load(f)

    return {'actions': [(run_inference_problem,[],{'parameters':inference_parameters})],
            'file_dep': [inference_parameters["model_path"]],
            # 'targets': [inference_parameters["output_path"]+inference_parameters["output_format"]],
            'uptodate': [True]}

if __name__ == "__main__":

    inference_parameters_path = "input/settings/inference_parameters.json"
    with open(inference_parameters_path, 'r') as f:
        inference_parameters = json.load(f)
        
    run_inference_problem(inference_parameters)